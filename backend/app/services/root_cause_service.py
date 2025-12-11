"""
Root Cause Analysis Service
Business logic for root cause analysis
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.root_cause_repository import RootCauseRepository
from app.repositories.business_data_repository import BusinessDataRepository
from app.models.root_cause import RootCauseIssue, RootCauseAnalysisResponse
from app.utils.ai_service import query_perplexity
from datetime import datetime, timezone
import pandas as pd
import json
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class RootCauseService:
    """Service for root cause analysis business logic"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = RootCauseRepository(db)
        self.business_data_repo = BusinessDataRepository(db)
    
    async def get_issues(self) -> RootCauseAnalysisResponse:
        """Get root cause analysis issues from MongoDB"""
        logger.info("🔍 Fetching root cause analysis issues from MongoDB")
        
        rca_doc = await self.repo.find_one()
        
        if not rca_doc:
            # Initialize empty document
            initial_doc = {
                "issues": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await self.repo.insert_one(initial_doc)
            return RootCauseAnalysisResponse(
                issues=[],
                summary={"critical": 0, "investigating": 0, "resolved": 0}
            )
        
        # Convert MongoDB issues to RootCauseIssue objects
        issues = []
        for issue_data in rca_doc.get('issues', []):
            try:
                # Ensure id is an int
                if 'id' not in issue_data or not isinstance(issue_data.get('id'), int):
                    issue_data['id'] = len(issues) + 1
                issues.append(RootCauseIssue(**issue_data))
            except Exception as e:
                logger.warning(f"Error parsing issue: {e}, skipping issue: {issue_data}")
                continue
        
        # Calculate summary
        critical_count = len([i for i in issues if i.severity == 'high'])
        investigating_count = len([i for i in issues if i.status == 'investigating'])
        resolved_count = len([i for i in issues if i.status == 'resolved'])
        
        return RootCauseAnalysisResponse(
            issues=issues,
            summary={
                "critical": critical_count,
                "investigating": investigating_count,
                "resolved": resolved_count
            }
        )
    
    async def generate_issues(self) -> RootCauseAnalysisResponse:
        """Generate NEW AI-powered root cause analysis issues based on real business data"""
        logger.info("🔍 Generating NEW root cause analysis issues from business data")
        
        # Get comprehensive business data
        data = await self.business_data_repo.find(query={}, limit=10000)
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        df = pd.DataFrame(data)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available in database")
        
        required_columns = ['Revenue', 'Gross_Profit', 'Units', 'Year', 'Business', 'Channel', 'Customer', 'Brand']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise HTTPException(status_code=500, detail=f"Missing required columns: {missing_columns}")
        
        # Calculate key metrics for context
        total_revenue = float(df['Revenue'].sum()) if not df.empty else 0
        total_profit = float(df['Gross_Profit'].sum()) if not df.empty else 0
        total_units = float(df['Units'].sum()) if not df.empty else 0
        profit_margin = (total_profit/total_revenue*100) if total_revenue > 0 else 0
        
        # Year-over-year analysis
        yearly_data = df.groupby('Year').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum',
            'Units': 'sum'
        }).reset_index().sort_values('Year')
        
        # Identify declining trends
        if len(yearly_data) > 1:
            latest_year = yearly_data.iloc[-1]
            previous_year = yearly_data.iloc[-2] if len(yearly_data) > 1 else None
            # Convert to float to avoid pandas Series comparison issues
            revenue_decline = previous_year is not None and float(latest_year['Revenue']) < float(previous_year['Revenue'])
            profit_decline = previous_year is not None and float(latest_year['Gross_Profit']) < float(previous_year['Gross_Profit'])
        else:
            revenue_decline = False
            profit_decline = False
        
        # Business performance by segment
        business_perf = df.groupby('Business').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Channel performance
        channel_perf = df.groupby('Channel').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Customer performance
        customer_perf = df.groupby('Customer').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Build data context for AI
        data_context = f"""
Business Performance Data Analysis for Root Cause Analysis:

OVERALL METRICS:
- Total Revenue: €{total_revenue:,.2f}
- Total Gross Profit: €{total_profit:,.2f}
- Total Cases Sold: {total_units:,.0f}
- Profit Margin: {profit_margin:.2f}%

YEAR-OVER-YEAR PERFORMANCE:
{yearly_data.to_string(index=False) if not yearly_data.empty else 'No yearly data'}

TREND ANALYSIS:
- Revenue Trend: {'Declining' if revenue_decline else 'Stable/Increasing'}
- Profit Trend: {'Declining' if profit_decline else 'Stable/Increasing'}

TOP 5 BUSINESSES BY REVENUE:
{business_perf.head(5).to_string(index=False) if not business_perf.empty else 'No business data'}

TOP 5 CHANNELS BY REVENUE:
{channel_perf.head(5).to_string(index=False) if not channel_perf.empty else 'No channel data'}

TOP 5 CUSTOMERS BY REVENUE:
{customer_perf.head(5).to_string(index=False) if not customer_perf.empty else 'No customer data'}

AVAILABLE DATA PERIODS:
- Years: {sorted(df['Year'].unique().tolist()) if not df.empty else []}
- Total Records: {len(df)}
- Unique Businesses: {df['Business'].nunique() if not df.empty else 0}
- Unique Channels: {df['Channel'].nunique() if not df.empty else 0}
- Unique Brands: {df['Brand'].nunique() if not df.empty else 0}
- Unique Customers: {df['Customer'].nunique() if not df.empty else 0}
"""
        
        # Generate AI root cause analysis issues
        ai_prompt = f"""
Based on the following business performance data, identify 3-5 critical business issues that need root cause analysis.

DATA CONTEXT:
{data_context}

REQUIREMENTS:
1. Identify real issues based on data patterns (declining revenue, profit margins, customer churn, etc.)
2. For each issue, provide:
   - A clear, specific title (e.g., "Sales Decline in Q4", "Customer Churn Rate Increase")
   - Severity level: "high", "medium", or "low" based on impact
   - Root cause: A specific, data-driven explanation of why this issue is occurring
   - Impact: Quantified impact (e.g., "€250K revenue loss", "15% increase in churn")
   - AI Recommendation: Specific, actionable recommendation to address the root cause
   - Status: "investigating", "resolved", or "monitoring"
3. Base recommendations on actual data patterns and trends
4. Prioritize issues with highest business impact
5. Provide realistic impact estimates based on the data scale

OUTPUT FORMAT (JSON array):
[
  {{
    "title": "Specific issue title",
    "severity": "high|medium|low",
    "rootCause": "Detailed explanation of the root cause based on data",
    "impact": "Quantified impact description (e.g., €250K revenue loss)",
    "recommendation": "Specific, actionable AI recommendation",
    "status": "investigating|resolved|monitoring"
  }}
]

Return ONLY valid JSON array, no additional text.
"""
        
        try:
            ai_response = await query_perplexity(ai_prompt)
            
            # Parse JSON from AI response
            ai_response_clean = ai_response.strip()
            if ai_response_clean.startswith('```json'):
                ai_response_clean = ai_response_clean[7:]
            if ai_response_clean.startswith('```'):
                ai_response_clean = ai_response_clean[3:]
            if ai_response_clean.endswith('```'):
                ai_response_clean = ai_response_clean[:-3]
            ai_response_clean = ai_response_clean.strip()
            
            issues_data = json.loads(ai_response_clean)
            
            # Format issues
            issues = []
            for idx, issue_data in enumerate(issues_data[:5], 1):  # Limit to 5
                issues.append(RootCauseIssue(
                    id=idx,
                    title=issue_data.get('title', f'Issue {idx}'),
                    severity=issue_data.get('severity', 'medium'),
                    rootCause=issue_data.get('rootCause', ''),
                    impact=issue_data.get('impact', ''),
                    recommendation=issue_data.get('recommendation', ''),
                    status=issue_data.get('status', 'investigating'),
                    createdAt=datetime.now(timezone.utc).isoformat(),
                    updatedAt=datetime.now(timezone.utc).isoformat()
                ))
            
            # Save to MongoDB
            rca_doc = await self.repo.find_one()
            if not rca_doc:
                rca_doc = {
                    "issues": [issue.model_dump() for issue in issues],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await self.repo.insert_one(rca_doc)
            else:
                await self.repo.update_one({
                    "issues": [issue.model_dump() for issue in issues],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                })
            
            # Calculate summary
            critical_count = len([i for i in issues if i.severity == 'high'])
            investigating_count = len([i for i in issues if i.status == 'investigating'])
            resolved_count = len([i for i in issues if i.status == 'resolved'])
            
            logger.info(f"Generated {len(issues)} new root cause issues and saved to MongoDB")
            
            return RootCauseAnalysisResponse(
                issues=issues,
                summary={
                    "critical": critical_count,
                    "investigating": investigating_count,
                    "resolved": resolved_count
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response (first 500 chars): {ai_response[:500] if 'ai_response' in locals() else 'No response'}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating root cause issues: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error generating root cause issues: {str(e)}")

