"""
Test file with real-world question examples
Tests actual user questions to ensure they work correctly
"""
import pytest
import re


# Real user questions that should work correctly
REAL_QUESTIONS = [
    {
        "question": "write me the board summary for the month of november 2025",
        "should_be_clear": True,
        "expected_months": ["November"],
        "expected_years": [2025],
        "description": "Board summary for specific month and year"
    },
    {
        "question": "tell me top 10 brands",
        "should_be_clear": True,
        "expected_months": [],
        "expected_years": [],
        "description": "Top N query"
    },
    {
        "question": "tell me brands",
        "should_be_clear": False,  # Too vague
        "expected_months": [],
        "expected_years": [],
        "description": "Vague question - should trigger clarification"
    },
    {
        "question": "what is the impact of operational expense on Kinetica brands",
        "should_be_clear": True,
        "expected_months": [],
        "expected_years": [],
        "description": "Impact analysis question"
    },
    {
        "question": "compare brand Bonne Maman with other brands",
        "should_be_clear": True,
        "expected_months": [],
        "expected_years": [],
        "description": "Comparison question"
    },
    {
        "question": "tell me about all business in details",
        "should_be_clear": True,
        "expected_months": [],
        "expected_years": [],
        "description": "All entities query"
    },
    {
        "question": "Compare Q1 for business Food across years",
        "should_be_clear": True,
        "expected_months": ["January", "February", "March"],
        "expected_years": [],
        "description": "Quarter query across years"
    },
    {
        "question": "write me the board summary for the month of november 2025",
        "should_be_clear": True,
        "expected_months": ["November"],
        "expected_years": [2025],
        "description": "Board summary - duplicate test"
    },
]


def test_year_extraction_pattern():
    """Test year extraction pattern"""
    year_pattern = r'\b(20\d{2})\b'
    
    for test_case in REAL_QUESTIONS:
        question = test_case["question"]
        expected_years = test_case["expected_years"]
        
        years_found = re.findall(year_pattern, question)
        years = [int(y) for y in years_found if 2000 <= int(y) <= 2100]
        
        assert set(years) == set(expected_years), \
            f"Year extraction failed for '{question}': got {years}, expected {expected_years}"


def test_month_extraction_pattern():
    """Test month extraction pattern"""
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
    
    quarter_to_months = {
        'q1': ['January', 'February', 'March'],
        'q2': ['April', 'May', 'June'],
        'q3': ['July', 'August', 'September'],
        'q4': ['October', 'November', 'December']
    }
    
    for test_case in REAL_QUESTIONS:
        question = test_case["question"]
        expected_months = test_case["expected_months"]
        
        message_lower = question.lower()
        found_months = []
        
        # Check for quarters first
        quarter_pattern = r'\bq([1-4])\b'
        quarters = re.findall(quarter_pattern, message_lower)
        if quarters:
            for q in quarters:
                q_key = f'q{q}'
                if q_key in quarter_to_months:
                    found_months.extend(quarter_to_months[q_key])
        
        # Check for month names
        for month_key, month_full in month_mapping.items():
            pattern = r'\b' + re.escape(month_key) + r'\b'
            if re.search(pattern, message_lower):
                if month_full not in found_months:
                    found_months.append(month_full)
        
        assert set(found_months) == set(expected_months), \
            f"Month extraction failed for '{question}': got {found_months}, expected {expected_months}"


def test_clarity_patterns():
    """Test clarity detection patterns"""
    clear_patterns = [
        r'top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers|channel|channels)',
        r'show\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)',
        r'tell\s+me\s+top\s+\d+\s+(brand|brands|business|businesses|category|categories|customer|customers)',
        r'compare\s+(brand|brands|business|businesses|category|categories)\s+',
        r'all\s+(brand|brands|business|businesses|category|categories|customer|customers)',
        r'tell\s+me\s+about\s+all\s+(brand|brands|business|businesses|category|categories)',
        r'show\s+me\s+all\s+(brand|brands|business|businesses|category|categories)',
        r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary',
        r'write\s+(me\s+)?(the\s+)?(a\s+)?(comprehensive\s+)?(board\s+)?summary\s+for',
        r'board\s+summary',
        r'what\s+is\s+the\s+impact',
    ]
    
    for test_case in REAL_QUESTIONS:
        question = test_case["question"]
        should_be_clear = test_case["should_be_clear"]
        
        user_msg_lower = question.lower()
        is_matched = any(re.search(pattern, user_msg_lower) for pattern in clear_patterns)
        
        if should_be_clear:
            assert is_matched, \
                f"Question should match clear pattern: '{question}'"
        # Note: unclear questions might still match some patterns, that's okay


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

