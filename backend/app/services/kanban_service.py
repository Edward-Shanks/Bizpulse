"""
Kanban Service
Business logic for kanban (campaigns and goals)
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.kanban_repository import KanbanRepository
from app.repositories.business_data_repository import BusinessDataRepository
from app.models.kanban import (
    StrategicRecommendation, StrategicRecommendationsResponse,
    GoalRequest, GoalResponse, GenerateGoalsRequest, UpdateGoalRequest,
    AcceptCampaignRequest
)
from app.utils.ai_service import query_perplexity
from datetime import datetime, timezone
import pandas as pd
import json
import uuid
import logging
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class KanbanService:
    """Service for kanban business logic"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = KanbanRepository(db)
        self.business_data_repo = BusinessDataRepository(db)
        self.db = db  # Keep for user queries
    
    async def move_expired_campaigns(self):
        """Move campaigns from live to past if their endDate has passed"""
        try:
            kanban_doc = await self.repo.find_kanban()
            if not kanban_doc:
                return
            
            live_campaigns = kanban_doc.get('live', [])
            past_campaigns = kanban_doc.get('past', [])
            
            current_date = datetime.now(timezone.utc).date()
            expired_campaigns = []
            remaining_live = []
            
            for campaign in live_campaigns:
                if campaign.get('endDate'):
                    try:
                        end_date = datetime.fromisoformat(campaign['endDate'].replace('Z', '+00:00')).date()
                        if end_date < current_date:
                            campaign['status'] = 'past'
                            campaign['expiredAt'] = datetime.now(timezone.utc).isoformat()
                            expired_campaigns.append(campaign)
                        else:
                            remaining_live.append(campaign)
                    except Exception as e:
                        logger.warning(f"Error parsing endDate for campaign {campaign.get('title')}: {e}")
                        remaining_live.append(campaign)
                else:
                    remaining_live.append(campaign)
            
            if expired_campaigns:
                past_campaigns.extend(expired_campaigns)
                await self.repo.update_kanban({
                    "live": remaining_live,
                    "past": past_campaigns,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                })
                logger.info(f"Moved {len(expired_campaigns)} expired campaigns to past")
        except Exception as e:
            logger.error(f"Error moving expired campaigns: {str(e)}")
    
    async def get_annual_goal(self) -> Dict[str, Any]:
        """Get real annual goal metrics based on customer activation data"""
        try:
            data = await self.business_data_repo.find(query={}, limit=10000)
            if not data:
                return {
                    "current": 0,
                    "target": 100,
                    "metric": "% Activated Customers",
                    "progress": 0
                }
            
            df = pd.DataFrame(data)
            if df.empty:
                return {
                    "current": 0,
                    "target": 100,
                    "metric": "% Activated Customers",
                    "progress": 0
                }
            
            unique_customers = df['Customer'].nunique() if 'Customer' in df.columns else 0
            current_year = datetime.now(timezone.utc).year
            current_year_data = df[df['Year'] == current_year] if 'Year' in df.columns else df
            active_customers = current_year_data['Customer'].nunique() if not current_year_data.empty and 'Customer' in current_year_data.columns else 0
            
            if unique_customers > 0:
                activation_percentage = (active_customers / unique_customers) * 100
            else:
                activation_percentage = 0
            
            historical_years = df['Year'].unique() if 'Year' in df.columns else []
            if len(historical_years) > 1:
                yearly_activation = []
                for year in historical_years:
                    year_data = df[df['Year'] == year]
                    year_customers = year_data['Customer'].nunique() if 'Customer' in year_data.columns else 0
                    if unique_customers > 0:
                        yearly_activation.append((year_customers / unique_customers) * 100)
                
                if yearly_activation:
                    avg_activation = sum(yearly_activation) / len(yearly_activation)
                    target = min(100, max(activation_percentage + 5, avg_activation + 10))
                else:
                    target = min(100, activation_percentage + 10)
            else:
                target = min(100, activation_percentage + 10)
            
            return {
                "current": round(activation_percentage, 1),
                "target": round(target, 1),
                "metric": "% Activated Customers",
                "progress": round((activation_percentage / target * 100) if target > 0 else 0, 1),
                "active_customers": active_customers,
                "total_customers": unique_customers
            }
        except Exception as e:
            logger.error(f"Error calculating annual goal: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "current": 0,
                "target": 100,
                "metric": "% Activated Customers",
                "progress": 0
            }
    
    async def get_recommendations(self) -> StrategicRecommendationsResponse:
        """Load kanban recommendations from MongoDB (does not generate new ones)"""
        try:
            await self.move_expired_campaigns()
            
            kanban_doc = await self.repo.find_kanban()
            if not kanban_doc:
                initial_doc = {
                    "recommended": [],
                    "live": [],
                    "past": [],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await self.repo.insert_kanban(initial_doc)
                return StrategicRecommendationsResponse(
                    recommended=[],
                    live=[],
                    past=[]
                )
            
            recommended = [StrategicRecommendation(**rec) for rec in kanban_doc.get('recommended', [])]
            live = [StrategicRecommendation(**camp) for camp in kanban_doc.get('live', [])]
            past = [StrategicRecommendation(**camp) for camp in kanban_doc.get('past', [])]
            
            return StrategicRecommendationsResponse(
                recommended=recommended,
                live=live,
                past=past
            )
        except Exception as e:
            logger.error(f"Error loading kanban recommendations: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error loading recommendations: {str(e)}")
    
    async def generate_strategic_recommendations(self) -> StrategicRecommendationsResponse:
        """Generate NEW AI-powered strategic recommendations based on real business data"""
        logger.info("🚀 STARTING strategic recommendations generation")
        try:
            data = await self.business_data_repo.find(query={}, limit=10000)
            if not data:
                raise HTTPException(status_code=404, detail="No data available")
            
            df = pd.DataFrame(data)
            if df.empty:
                raise HTTPException(status_code=404, detail="No data available in database")
            
            required_columns = ['Revenue', 'Gross_Profit', 'Units', 'Year', 'Business', 'Channel', 'Customer', 'Brand']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise HTTPException(status_code=500, detail=f"Missing required columns: {missing_columns}")
            
            total_revenue = float(df['Revenue'].sum()) if not df.empty else 0
            total_profit = float(df['Gross_Profit'].sum()) if not df.empty else 0
            total_units = float(df['Units'].sum()) if not df.empty else 0
            
            yearly_data = df.groupby('Year').agg({
                'Revenue': 'sum',
                'Gross_Profit': 'sum',
                'Units': 'sum'
            }).reset_index()
            
            business_perf = df.groupby('Business').agg({
                'Revenue': 'sum',
                'Gross_Profit': 'sum'
            }).reset_index().sort_values('Revenue', ascending=False).head(5)
            
            channel_perf = df.groupby('Channel').agg({
                'Revenue': 'sum',
                'Gross_Profit': 'sum'
            }).reset_index().sort_values('Revenue', ascending=False).head(5)
            
            customer_perf = df.groupby('Customer').agg({
                'Revenue': 'sum',
                'Gross_Profit': 'sum'
            }).reset_index().sort_values('Revenue', ascending=False).head(5)
            
            kanban_doc = await self.repo.find_kanban()
            past_campaigns = kanban_doc.get('past', []) if kanban_doc else []
            
            past_context = ""
            if past_campaigns:
                past_context = "\n\nPAST CAMPAIGNS PERFORMANCE (for learning):\n"
                for idx, past_camp in enumerate(past_campaigns[:10], 1):
                    past_context += f"{idx}. {past_camp.get('title', 'Unknown')}\n"
                    past_context += f"   Category: {past_camp.get('category', 'N/A')}\n"
                    past_context += f"   Budget: €{past_camp.get('budget', 0):,.2f}\n"
                    impact = past_camp.get('impact', {})
                    past_context += f"   Expected Impact: €{impact.get('value', 0):,.2f} ({impact.get('percentage', 0)}% uplift)\n"
                    past_context += f"   Period: {past_camp.get('startDate', 'N/A')} to {past_camp.get('endDate', 'N/A')}\n"
                    past_context += f"   Channels: {', '.join(past_camp.get('channels', []))}\n\n"
            
            data_context = f"""
Business Performance Data Analysis:

OVERALL METRICS:
- Total Revenue: €{total_revenue:,.2f}
- Total Gross Profit: €{total_profit:,.2f}
- Total Cases Sold: {total_units:,.0f}
- Profit Margin: {(total_profit/total_revenue*100) if total_revenue > 0 else 0:.2f}%

YEAR-OVER-YEAR PERFORMANCE:
{yearly_data.to_string(index=False) if not yearly_data.empty else 'No yearly data'}

TOP 5 BUSINESSES BY REVENUE:
{business_perf.to_string(index=False) if not business_perf.empty else 'No business data'}

TOP 5 CHANNELS BY REVENUE:
{channel_perf.to_string(index=False) if not channel_perf.empty else 'No channel data'}

TOP 5 CUSTOMERS BY REVENUE:
{customer_perf.to_string(index=False) if not customer_perf.empty else 'No customer data'}

AVAILABLE DATA PERIODS:
- Years: {sorted(df['Year'].unique().tolist()) if not df.empty else []}
- Total Records: {len(df)}
- Unique Businesses: {df['Business'].nunique() if not df.empty else 0}
- Unique Channels: {df['Channel'].nunique() if not df.empty else 0}
- Unique Brands: {df['Brand'].nunique() if not df.empty else 0}
- Unique Customers: {df['Customer'].nunique() if not df.empty else 0}
{past_context}
"""
            
            ai_prompt = f"""
Based on the following business data, generate 4-6 strategic marketing and business recommendations.

DATA CONTEXT:
{data_context}

REQUIREMENTS:
1. Each recommendation must be specific, actionable, and data-driven
2. Include realistic budget estimates (in Euros) based on the revenue scale
3. Calculate expected impact (revenue increase in Euros and percentage uplift)
4. Provide detailed reasoning based on the actual data patterns AND past campaign performance (if available)
5. Suggest appropriate marketing channels (e.g., Meta Ads, Google Ads, Email, Social Media, etc.)
6. Assign an AI confidence score (0-100) based on data strength
7. Categorize as 'acquisition', 'retention', or 'engagement'
8. Include realistic start and end dates (3-6 month campaigns)
9. If past campaigns are provided, learn from them - avoid repeating unsuccessful strategies and build on what worked

OUTPUT FORMAT (JSON array):
[
  {{
    "title": "Specific recommendation title",
    "description": "Detailed description of the recommendation",
    "category": "acquisition|retention|engagement",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD",
    "budget": 50000,
    "impact": {{"value": 250000, "percentage": 15.5}},
    "reasoning": "Detailed reasoning based on data patterns, specific numbers, and why this will work",
    "channels": ["Channel1", "Channel2"],
    "aiScore": 85
  }}
]

Return ONLY valid JSON array, no additional text.
"""
            
            try:
                logger.info("🤖 Calling Perplexity AI to generate recommendations...")
                ai_response = await query_perplexity(ai_prompt)
                
                if not ai_response or len(ai_response.strip()) < 10:
                    logger.error("❌ AI service returned empty or invalid response")
                    raise HTTPException(status_code=500, detail="AI service returned invalid response")
                
                logger.info(f"🤖 AI Response received (length: {len(ai_response)})")
                logger.info(f"🤖 AI Response preview (first 500 chars): {ai_response[:500]}")
                logger.info(f"🤖 AI Response (last 500 chars): {ai_response[-500:]}")
                # Log full response to file for debugging
                try:
                    with open('ai_response_debug.json', 'w', encoding='utf-8') as f:
                        f.write(ai_response)
                    logger.info("🤖 Full AI response saved to ai_response_debug.json")
                except Exception as log_error:
                    logger.warning(f"⚠️ Could not save AI response to file: {str(log_error)}")
                
                ai_response_clean = ai_response.strip()
                if ai_response_clean.startswith('```json'):
                    ai_response_clean = ai_response_clean[7:]
                if ai_response_clean.startswith('```'):
                    ai_response_clean = ai_response_clean[3:]
                if ai_response_clean.endswith('```'):
                    ai_response_clean = ai_response_clean[:-3]
                ai_response_clean = ai_response_clean.strip()
                
                logger.info(f"🤖 Cleaned response (first 500 chars): {ai_response_clean[:500]}")
                
                # Try to extract JSON array if it's embedded in text
                json_match = re.search(r'\[.*\]', ai_response_clean, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"🤖 Extracted JSON array (length: {len(json_str)})")
                else:
                    # Try to find array boundaries
                    start_idx = ai_response_clean.find('[')
                    end_idx = ai_response_clean.rfind(']')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_str = ai_response_clean[start_idx:end_idx + 1]
                        logger.info(f"🤖 Extracted JSON array from positions {start_idx} to {end_idx}")
                    else:
                        json_str = ai_response_clean
                        logger.warning("⚠️ Could not find JSON array boundaries, using full response")
                
                # Try to fix common JSON issues
                try:
                    recommendations_data = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    logger.error(f"❌ JSON parse error: {str(json_error)}")
                    error_pos = json_error.pos if hasattr(json_error, 'pos') else 0
                    logger.error(f"❌ Error at position: {error_pos}")
                    if error_pos > 0:
                        start_pos = max(0, error_pos - 200)
                        end_pos = min(len(json_str), error_pos + 200)
                        logger.error(f"❌ JSON around error (chars {start_pos} to {end_pos}):")
                        logger.error(f"❌ ...{json_str[start_pos:end_pos]}...")
                    
                    # Try to fix common issues
                    fixed_json = json_str
                    
                    # Fix unquoted property names (more aggressive)
                    fixed_json = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json, flags=re.MULTILINE)
                    
                    # Fix single quotes in keys and values
                    fixed_json = re.sub(r"'([^']*)':", r'"\1":', fixed_json)
                    fixed_json = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_json)
                    
                    # Remove trailing commas before closing braces/brackets
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                    
                    # Fix missing commas between objects in array
                    fixed_json = re.sub(r'}\s*{', r'},{', fixed_json)
                    
                    # Fix missing commas between array elements
                    fixed_json = re.sub(r']\s*\[', r'],[', fixed_json)
                    
                    # Try to fix common delimiter issues
                    # Sometimes AI returns "key: value" instead of "key": "value"
                    fixed_json = re.sub(r'(["\w]+)\s*:\s*([^,}\]]+)(?=\s*[,}\]])', r'\1: "\2"', fixed_json)
                    
                    try:
                        recommendations_data = json.loads(fixed_json)
                        logger.info("✅ Successfully parsed JSON after fixing common issues")
                    except json.JSONDecodeError as e2:
                        logger.error(f"❌ JSON parse still failed after fixes: {str(e2)}")
                        error_pos2 = e2.pos if hasattr(e2, 'pos') else 0
                        if error_pos2 > 0:
                            start_pos2 = max(0, error_pos2 - 200)
                            end_pos2 = min(len(fixed_json), error_pos2 + 200)
                            logger.error(f"❌ Fixed JSON around error (chars {start_pos2} to {end_pos2}):")
                            logger.error(f"❌ ...{fixed_json[start_pos2:end_pos2]}...")
                        
                        # Last resort: try to extract just the array content and rebuild
                        try:
                            # Find all objects in the array
                            objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', fixed_json)
                            if objects:
                                logger.info(f"⚠️ Attempting to extract {len(objects)} objects from malformed JSON")
                                # Try to parse each object individually
                                parsed_objects = []
                                for obj_str in objects:
                                    try:
                                        # Clean up the object string
                                        obj_clean = obj_str.strip()
                                        # Fix common issues in individual objects
                                        obj_clean = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', obj_clean, flags=re.MULTILINE)
                                        obj_clean = re.sub(r"'([^']*)':", r'"\1":', obj_clean)
                                        obj_clean = re.sub(r":\s*'([^']*)'", r': "\1"', obj_clean)
                                        obj_clean = re.sub(r',(\s*[}])', r'\1', obj_clean)
                                        
                                        parsed_obj = json.loads(obj_clean)
                                        parsed_objects.append(parsed_obj)
                                    except Exception:
                                        continue  # Skip invalid objects
                                
                                if parsed_objects:
                                    recommendations_data = parsed_objects
                                    logger.info(f"✅ Successfully extracted {len(parsed_objects)} valid objects from malformed JSON")
                                else:
                                    raise HTTPException(status_code=500, detail=f"Failed to parse AI response: Could not extract valid JSON objects. AI may have returned invalid JSON format.")
                            else:
                                raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e2)}. AI may have returned invalid JSON format.")
                        except HTTPException:
                            raise
                        except Exception as e3:
                            logger.error(f"❌ Object extraction also failed: {str(e3)}")
                            raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e2)}. AI may have returned invalid JSON format.")
                
                logger.info(f"✅ Successfully parsed {len(recommendations_data)} recommendations from AI")
                
                if not recommendations_data or len(recommendations_data) == 0:
                    raise HTTPException(status_code=500, detail="AI service returned empty recommendations")
                
                recommendations = []
                for idx, rec in enumerate(recommendations_data[:6], 1):
                    recommendations.append(StrategicRecommendation(
                        id=idx,
                        title=rec.get('title', f'Recommendation {idx}'),
                        description=rec.get('description', ''),
                        type='system',
                        category=rec.get('category', 'acquisition'),
                        startDate=rec.get('startDate', '2025-01-20'),
                        endDate=rec.get('endDate'),
                        budget=float(rec.get('budget', 50000)),
                        impact=rec.get('impact', {'value': 100000, 'percentage': 10}),
                        reasoning=rec.get('reasoning', ''),
                        channels=rec.get('channels', ['Email']),
                        aiScore=int(rec.get('aiScore', 75)),
                        status='recommended'
                    ))
                
                kanban_doc = await self.repo.find_kanban()
                if not kanban_doc:
                    kanban_doc = {
                        "recommended": [rec.model_dump() for rec in recommendations],
                        "live": [],
                        "past": [],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                    await self.repo.insert_kanban(kanban_doc)
                else:
                    await self.repo.update_kanban({
                        "recommended": [rec.model_dump() for rec in recommendations],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    })
                
                return StrategicRecommendationsResponse(
                    recommended=recommendations,
                    live=[StrategicRecommendation(**camp) for camp in kanban_doc.get('live', [])],
                    past=[StrategicRecommendation(**camp) for camp in kanban_doc.get('past', [])]
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise HTTPException(status_code=500, detail="Failed to parse AI response")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error generating recommendations: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Strategic recommendations error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Strategic recommendations error: {str(e)}")
    
    async def generate_goals(self, request: GenerateGoalsRequest) -> List[GoalResponse]:
        """Generate AI-powered goals from a campaign"""
        logger.info(f"Generating goals for campaign ID: {request.campaignId}")
        
        kanban_doc = await self.repo.find_kanban()
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        campaign = None
        for camp in kanban_doc.get('live', []) + kanban_doc.get('recommended', []):
            if camp.get('id') == request.campaignId or str(camp.get('id')) == str(request.campaignId):
                campaign = camp
                break
        
        if not campaign:
            raise HTTPException(status_code=404, detail=f"Campaign not found: {request.campaignId}")
        
        # Get users for department assignment
        try:
            all_users = await self.db.users.find({"status": "active"}, {"_id": 0, "password_hash": 0}).to_list(1000)
        except Exception:
            all_users = []
        
        users_by_dept = {}
        for user in all_users:
            dept = user.get('department')
            if dept:
                if dept not in users_by_dept:
                    users_by_dept[dept] = []
                users_by_dept[dept].append(user)
        
        budget = campaign.get('budget', 0)
        if isinstance(budget, dict):
            budget = budget.get('value', 0) if isinstance(budget.get('value'), (int, float)) else 0
        elif not isinstance(budget, (int, float)):
            budget = 0
        
        impact = campaign.get('impact', {})
        impact_value = impact.get('value', 0) if isinstance(impact, dict) else 0
        impact_percentage = impact.get('percentage', 0) if isinstance(impact, dict) else 0
        channels = campaign.get('channels', []) if isinstance(campaign.get('channels'), list) else []
        
        campaign_context = f"""
Campaign Title: {campaign.get('title', 'Unknown')}
Campaign Description: {campaign.get('description', 'No description')}
Category: {campaign.get('category', 'N/A')}
Budget: €{budget:,.2f}
Expected Impact: €{impact_value:,.2f} ({impact_percentage}% uplift)
Channels: {', '.join(str(c) for c in channels)}
Start Date: {campaign.get('startDate', 'N/A')}
End Date: {campaign.get('endDate', 'N/A')}
"""
        
        ai_prompt = f"""
Based on the following campaign, generate 3-6 strategic goals that will help achieve this campaign's objectives.
Each goal should be:
1. Specific and actionable
2. Assigned to appropriate departments (sales, operations, finance, hr, marketing, technology)
3. Have clear owners (can be multiple)
4. Include dependencies
5. Have measurable metrics
6. Include 2-3 key results with current/target values

CAMPAIGN DETAILS:
{campaign_context}

AVAILABLE DEPARTMENTS AND TEAM MEMBERS:
{json.dumps({dept: [{'name': u.get('name'), 'email': u.get('email'), 'role': u.get('role')} for u in users] for dept, users in users_by_dept.items()}, indent=2)}

OUTPUT FORMAT (JSON array ONLY - no markdown, no code blocks, no explanations):
[
  {{
    "title": "Goal title",
    "description": "Detailed goal description",
    "department": "sales",
    "owners": ["user@example.com"],
    "teamMembers": ["member@example.com"],
    "dependencies": ["Dependency 1"],
    "metrics": ["Metric 1"],
    "keyResults": [
      {{"description": "KR 1", "current": 0, "target": 100}}
    ],
    "status": "on-track",
    "progress": 0
  }}
]

Return ONLY the JSON array. No markdown, no code blocks, no explanations.
"""
        
        try:
            ai_response = await query_perplexity(ai_prompt)
            if not ai_response:
                raise HTTPException(status_code=500, detail="AI service returned empty response")
            
            # Clean and parse JSON
            ai_response_clean = ai_response.strip()
            if ai_response_clean.startswith('```json'):
                ai_response_clean = ai_response_clean[7:]
            if ai_response_clean.startswith('```'):
                ai_response_clean = ai_response_clean[3:]
            if ai_response_clean.endswith('```'):
                ai_response_clean = ai_response_clean[:-3]
            ai_response_clean = ai_response_clean.strip()
            
            # Try to extract JSON array
            json_match = re.search(r'\[.*\]', ai_response_clean, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                start_idx = ai_response_clean.find('[')
                end_idx = ai_response_clean.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response_clean[start_idx:end_idx + 1]
                else:
                    raise HTTPException(status_code=500, detail="AI response does not contain valid JSON array")
            
            # Fix common JSON issues
            json_str = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str, flags=re.MULTILINE)
            json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
            json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            ai_goals = json.loads(json_str)
            
            if not isinstance(ai_goals, list) or len(ai_goals) == 0:
                raise HTTPException(status_code=500, detail="AI generated no valid goals")
            
            # Convert to GoalResponse format
            generated_goals = []
            for idx, ai_goal in enumerate(ai_goals[:6]):
                if not isinstance(ai_goal, dict):
                    continue
                
                # Map owner emails to user IDs
                owner_ids = []
                for owner_email in ai_goal.get('owners', []):
                    if isinstance(owner_email, str):
                        user = next((u for u in all_users if u.get('email') == owner_email), None)
                        if user and user.get('id'):
                            owner_ids.append(user.get('id'))
                
                team_member_ids = []
                for member_email in ai_goal.get('teamMembers', []):
                    if isinstance(member_email, str):
                        user = next((u for u in all_users if u.get('email') == member_email), None)
                        if user and user.get('id'):
                            team_member_ids.append(user.get('id'))
                
                department = ai_goal.get('department', 'sales')
                valid_departments = ['sales', 'operations', 'finance', 'hr', 'marketing', 'technology']
                if department not in valid_departments:
                    department = 'sales'
                
                key_results = []
                for kr in ai_goal.get('keyResults', []):
                    if isinstance(kr, dict):
                        key_results.append({
                            "description": str(kr.get('description', '')),
                            "current": int(kr.get('current', 0)) if isinstance(kr.get('current'), (int, float)) else 0,
                            "target": int(kr.get('target', 0)) if isinstance(kr.get('target'), (int, float)) else 0
                        })
                
                goal = {
                    "id": str(uuid.uuid4()),
                    "campaignId": str(request.campaignId),
                    "title": str(ai_goal.get('title', f'Untitled Goal {idx + 1}')),
                    "description": str(ai_goal.get('description', '')),
                    "department": department,
                    "owners": owner_ids,
                    "teamMembers": team_member_ids,
                    "dependencies": ai_goal.get('dependencies', []) if isinstance(ai_goal.get('dependencies'), list) else [],
                    "metrics": ai_goal.get('metrics', []) if isinstance(ai_goal.get('metrics'), list) else [],
                    "keyResults": key_results,
                    "status": ai_goal.get('status', 'on-track'),
                    "progress": max(0, min(100, int(ai_goal.get('progress', 0)))),
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "tasks": []
                }
                
                # Save to database
                await self.repo.insert_goal(goal)
                generated_goals.append(GoalResponse(**goal))
            
            if len(generated_goals) == 0:
                raise HTTPException(status_code=500, detail="No valid goals could be generated")
            
            return generated_goals
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating goals: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error generating goals: {str(e)}")
    
    async def create_goal(self, request: GoalRequest) -> GoalResponse:
        """Create a new goal linked to a campaign"""
        goal = {
            "id": str(uuid.uuid4()),
            "campaignId": request.campaignId,
            "title": request.title,
            "description": request.description,
            "department": request.department,
            "owners": request.owners,
            "teamMembers": request.teamMembers or [],
            "dependencies": request.dependencies or [],
            "metrics": request.metrics or [],
            "keyResults": request.keyResults or [],
            "status": request.status,
            "progress": request.progress,
            "tasks": [],
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        await self.repo.insert_goal(goal)
        
        # Update campaign to include goal ID
        kanban_doc = await self.repo.find_kanban()
        if kanban_doc:
            for camp in kanban_doc.get('live', []):
                if str(camp.get('id')) == str(request.campaignId):
                    if 'goals' not in camp:
                        camp['goals'] = []
                    camp['goals'].append(goal['id'])
                    await self.repo.update_kanban({
                        "live": kanban_doc.get('live', []),
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    })
                    break
        
        return GoalResponse(**goal)
    
    async def get_campaign_goals(self, campaign_id: str) -> List[GoalResponse]:
        """Get all goals for a specific campaign"""
        goals = await self.repo.find_goals_by_campaign(campaign_id)
        return [GoalResponse(**goal) for goal in goals]
    
    async def accept_campaign(self, request: AcceptCampaignRequest) -> Dict[str, Any]:
        """Move a campaign from recommended to live"""
        kanban_doc = await self.repo.find_kanban()
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        recommended = kanban_doc.get('recommended', [])
        live = kanban_doc.get('live', [])
        
        campaign_to_move = None
        updated_recommended = []
        for campaign in recommended:
            if campaign.get('id') == request.campaignId:
                campaign_to_move = campaign
            else:
                updated_recommended.append(campaign)
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail="Campaign not found in recommended")
        
        campaign_to_move['status'] = 'live'
        campaign_to_move['acceptedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('startDate'):
            campaign_to_move['startDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        live.append(campaign_to_move)
        
        await self.repo.update_kanban({
            "recommended": updated_recommended,
            "live": live,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved to live")
        return {"success": True, "message": "Campaign moved to live"}
    
    async def archive_campaign(self, request: AcceptCampaignRequest) -> Dict[str, Any]:
        """Move a campaign from recommended or live to past (archived)"""
        kanban_doc = await self.repo.find_kanban()
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        recommended = kanban_doc.get('recommended', [])
        live = kanban_doc.get('live', [])
        past = kanban_doc.get('past', [])
        
        campaign_to_move = None
        source_collection = request.fromCollection
        
        if source_collection == 'recommended':
            updated_source = []
            for campaign in recommended:
                if campaign.get('id') == request.campaignId:
                    campaign_to_move = campaign
                else:
                    updated_source.append(campaign)
            if campaign_to_move:
                recommended = updated_source
        elif source_collection == 'live':
            updated_source = []
            for campaign in live:
                if campaign.get('id') == request.campaignId:
                    campaign_to_move = campaign
                else:
                    updated_source.append(campaign)
            if campaign_to_move:
                live = updated_source
        else:
            raise HTTPException(status_code=400, detail=f"Invalid fromCollection: {source_collection}")
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail=f"Campaign not found in {source_collection}")
        
        campaign_to_move['status'] = 'past'
        campaign_to_move['archivedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('endDate'):
            campaign_to_move['endDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        past.append(campaign_to_move)
        
        await self.repo.update_kanban({
            "recommended": recommended,
            "live": live,
            "past": past,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved to past")
        return {"success": True, "message": "Campaign archived successfully"}
    
    async def move_to_live(self, request: AcceptCampaignRequest) -> Dict[str, Any]:
        """Move a campaign from past (archived) to live (active)"""
        kanban_doc = await self.repo.find_kanban()
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        past = kanban_doc.get('past', [])
        live = kanban_doc.get('live', [])
        
        campaign_to_move = None
        updated_past = []
        for campaign in past:
            if campaign.get('id') == request.campaignId:
                campaign_to_move = campaign
            else:
                updated_past.append(campaign)
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail="Campaign not found in archived")
        
        campaign_to_move['status'] = 'live'
        campaign_to_move['reactivatedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('startDate'):
            campaign_to_move['startDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        live.append(campaign_to_move)
        
        await self.repo.update_kanban({
            "past": updated_past,
            "live": live,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved to live")
        return {"success": True, "message": "Campaign moved to live"}

