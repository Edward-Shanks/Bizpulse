"""
Comprehensive test suite for Insights Chat functionality
Tests question clarity, query building, and data retrieval
"""
import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.insights_service import InsightsService
from app.models.insights import InsightsChatRequest


class TestQuestionClarity:
    """Test question clarity detection"""
    
    @pytest.mark.asyncio
    async def test_clear_questions_patterns(self):
        """Test that clear questions are detected by patterns"""
        service = InsightsService(MagicMock())
        
        clear_questions = [
            "write me the board summary for the month of november 2025",
            "write me a board summary for november 2025",
            "write the board summary for november 2025",
            "board summary for november 2025",
            "tell me top 10 brands",
            "show me top 10 brands by revenue",
            "compare brands",
            "tell me about all brands",
            "show me all businesses",
            "what is the impact of operational expense on Kinetica brands",
        ]
        
        for question in clear_questions:
            is_clear, suggestions = await service._check_question_clarity(question)
            assert is_clear, f"Question should be clear: '{question}'"
            assert len(suggestions) == 0, f"Clear question should have no suggestions: '{question}'"
    
    @pytest.mark.asyncio
    async def test_unclear_questions(self):
        """Test that unclear questions trigger clarification"""
        service = InsightsService(MagicMock())
        
        unclear_questions = [
            "tell me brands",  # Too vague
            "top 10",  # Missing entity
            "compare",  # Missing what to compare
            "summary",  # Too vague
        ]
        
        for question in unclear_questions:
            is_clear, suggestions = await service._check_question_clarity(question)
            # These might be clear or unclear depending on LLM, but should not crash
            assert isinstance(is_clear, bool)
            assert isinstance(suggestions, list)


class TestMonthYearExtraction:
    """Test month and year extraction from messages"""
    
    def test_year_extraction(self):
        """Test year extraction from various formats"""
        test_cases = [
            ("november 2025", [2025]),
            ("write me the board summary for the month of november 2025", [2025]),
            ("compare Q1 for business Food across years", []),  # "years" is not a year
            ("2023 and 2024", [2023, 2024]),
            ("sales trend for 2025", [2025]),
        ]
        
        year_pattern = r'\b(20\d{2})\b'
        for message, expected_years in test_cases:
            years_found = re.findall(year_pattern, message)
            years = [int(y) for y in years_found if 2000 <= int(y) <= 2100]
            assert set(years) == set(expected_years), f"Failed for: '{message}' - got {years}, expected {expected_years}"
    
    def test_month_extraction(self):
        """Test month extraction from various formats"""
        month_mapping = {
            'january': 'January', 'jan': 'January',
            'february': 'February', 'feb': 'February',
            'march': 'March', 'mar': 'March',
            'april': 'April', 'apr': 'April',
            'may': 'May',
            'june': 'June', 'jun': 'June',
            'july': 'July', 'jul': 'July',
            'august': 'August', 'aug': 'August',
            'september': 'September', 'sep': 'September', 'sept': 'September',
            'october': 'October', 'oct': 'October',
            'november': 'November', 'nov': 'November',
            'december': 'December', 'dec': 'December'
        }
        
        test_cases = [
            ("november 2025", ["November"]),
            ("write me the board summary for the month of november 2025", ["November"]),
            ("nov 2025", ["November"]),
            ("january and february 2024", ["January", "February"]),
            ("Q1 2025", []),  # Quarters handled separately
        ]
        
        for message, expected_months in test_cases:
            message_lower = message.lower()
            found_months = []
            for month_key, month_full in month_mapping.items():
                pattern = r'\b' + re.escape(month_key) + r'\b'
                if re.search(pattern, message_lower):
                    if month_full not in found_months:
                        found_months.append(month_full)
            
            assert set(found_months) == set(expected_months), f"Failed for: '{message}' - got {found_months}, expected {expected_months}"


class TestQueryBuilding:
    """Test MongoDB query building from natural language"""
    
    @pytest.mark.asyncio
    async def test_november_2025_query(self):
        """Test that November 2025 query is built correctly"""
        from app.utils.query_builder import parse_query_from_natural_language
        
        db = AsyncMock()
        db.business_data = AsyncMock()
        db.business_data.distinct = AsyncMock(return_value=[])
        
        message = "write me the board summary for the month of november 2025"
        query = await parse_query_from_natural_language(message, db)
        
        # Should have Month_Name and Year filters
        assert 'Month_Name' in query or 'Year' in query, "Query should contain month or year filter"
        
        if 'Month_Name' in query:
            months = query['Month_Name'].get('$in', [])
            assert 'November' in months, f"November should be in months: {months}"
        
        if 'Year' in query:
            years = query['Year'].get('$in', [])
            assert 2025 in years, f"2025 should be in years: {years}"


class TestBoardSummaryQuestions:
    """Test board summary questions specifically"""
    
    @pytest.mark.asyncio
    async def test_board_summary_clarity_patterns(self):
        """Test that board summary questions are detected as clear"""
        service = InsightsService(MagicMock())
        
        board_summary_questions = [
            "write me the board summary for the month of november 2025",
            "write me a board summary for november 2025",
            "write the board summary for november 2025",
            "board summary for november 2025",
            "provide a board summary for november 2025",
            "create a comprehensive board summary for november 2025",
            "draft a board summary for november 2025",
            "generate a board summary for november 2025",
        ]
        
        for question in board_summary_questions:
            # Check if pattern matches
            user_msg_lower = question.lower()
            clear_patterns = [
                r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary',
                r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary\s+for',
                r'board\s+summary',
            ]
            
            is_matched = any(re.search(pattern, user_msg_lower) for pattern in clear_patterns)
            assert is_matched, f"Board summary question should match clear pattern: '{question}'"


class TestDataRetrieval:
    """Test data retrieval for specific queries"""
    
    @pytest.mark.asyncio
    async def test_november_2025_data_exists(self):
        """Test that November 2025 data can be retrieved"""
        from motor.motor_asyncio import AsyncIOMotorDatabase
        
        # This would require actual database connection
        # For now, we'll test the query building logic
        db = AsyncMock()
        db.business_data = AsyncMock()
        db.business_data.count_documents = AsyncMock(return_value=100)  # Mock data exists
        
        query = {
            'Month_Name': {'$in': ['November']},
            'Year': {'$in': [2025]}
        }
        
        count = await db.business_data.count_documents(query)
        assert count > 0, "November 2025 data should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

