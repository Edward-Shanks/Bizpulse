"""
Marketing Strategy API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
from app.core.dependencies import get_database, get_current_user
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

class MarketingStrategyConfig(BaseModel):
    strategy_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    ai_insights: Optional[str] = None
    version: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = "draft"  # draft, approved, archived

class MarketingStrategyListItem(BaseModel):
    id: str
    strategy_name: str
    module_id: int
    created_at: str
    updated_at: str
    has_ai_insights: bool

class GenerateAIInsightsRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)
    module_id: int
    module_title: str

class MarketingStrategyVersion(BaseModel):
    id: str
    name: str
    createdAt: str
    owner: str

class Comment(BaseModel):
    id: str
    text: str
    author: str
    createdAt: str

@router.get("/marketing-strategy/{module_id}/list")
async def list_marketing_strategies(
    module_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Get list of all strategies for a module"""
    try:
        strategies = await db.marketing_strategies.find(
            {"module_id": module_id, "user_email": email}
        ).sort("created_at", -1).to_list(100)
        
        strategy_list = []
        for strategy in strategies:
            created_at = strategy.get("created_at")
            updated_at = strategy.get("updated_at")
            
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            if isinstance(updated_at, datetime):
                updated_at = updated_at.isoformat()
            
            strategy_list.append({
                "id": str(strategy.get("_id", "")),
                "strategy_name": strategy.get("strategy_name", "Unnamed Strategy"),
                "module_id": strategy.get("module_id", module_id),
                "created_at": created_at or "",
                "updated_at": updated_at or "",
                "has_ai_insights": bool(strategy.get("ai_insights"))
            })
        
        return {"strategies": strategy_list}
    except Exception as e:
        logger.error(f"Error listing marketing strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving strategies: {str(e)}")

@router.get("/marketing-strategy/{module_id}/comments")
async def get_comments(
    module_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Get comments for a marketing strategy module"""
    try:
        # Use the marketing_strategies collection with a comments subdocument, or create a separate collection
        # For now, return empty list if collection doesn't exist
        try:
            comments = await db.marketing_strategy_comments.find(
                {"module_id": module_id, "user_email": email}
            ).sort("created_at", -1).to_list(50)
        except Exception as collection_error:
            # Collection might not exist yet, return empty list
            logger.warning(f"Comments collection not found or error accessing it: {str(collection_error)}")
            return {"comments": []}
        
        comment_list = []
        for c in comments:
            try:
                created_at = c.get("created_at")
                if created_at and isinstance(created_at, datetime):
                    created_at = created_at.isoformat()
                elif created_at:
                    created_at = str(created_at)
                else:
                    created_at = ""
                
                comment_list.append({
                    "id": str(c.get("_id", "")),
                    "text": c.get("text", ""),
                    "author": c.get("author", email),
                    "createdAt": created_at
                })
            except Exception as item_error:
                logger.warning(f"Error processing comment item: {str(item_error)}")
                continue
        
        return {"comments": comment_list}
    except Exception as e:
        logger.error(f"Error getting comments: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty list instead of error to prevent UI issues
        return {"comments": []}

@router.post("/marketing-strategy/{module_id}/comments")
async def add_comment(
    module_id: int,
    request: Dict[str, str],
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Add a comment to a marketing strategy module"""
    try:
        comment_doc = {
            "module_id": module_id,
            "user_email": email,
            "text": request.get("text", ""),
            "author": email,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.marketing_strategy_comments.insert_one(comment_doc)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Comment added successfully"
        }
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@router.get("/marketing-strategy/{module_id}/{strategy_id}")
async def get_marketing_strategy(
    module_id: int,
    strategy_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Get a specific marketing strategy by ID"""
    try:
        from bson import ObjectId
        strategy_doc = await db.marketing_strategies.find_one(
            {"_id": ObjectId(strategy_id), "module_id": module_id, "user_email": email}
        )
        
        if not strategy_doc:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        created_at = strategy_doc.get("created_at")
        updated_at = strategy_doc.get("updated_at")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()
        
        return {
            "id": str(strategy_doc.get("_id", "")),
            "strategy_name": strategy_doc.get("strategy_name", "Unnamed Strategy"),
            "module_id": strategy_doc.get("module_id", module_id),
            "config": strategy_doc.get("config", {}),
            "ai_insights": strategy_doc.get("ai_insights", ""),
            "created_at": created_at or "",
            "updated_at": updated_at or ""
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting marketing strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving strategy: {str(e)}")

@router.post("/marketing-strategy/{module_id}")
async def save_marketing_strategy(
    module_id: int,
    request: MarketingStrategyConfig,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Save marketing strategy configuration for a module"""
    try:
        strategy_name = request.strategy_name or f"Strategy {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        
        config_doc = {
            "module_id": module_id,
            "user_email": email,
            "strategy_name": strategy_name,
            "config": request.config,
            "ai_insights": request.ai_insights or "",
            "version": request.version or f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "owner": request.owner or email,
            "status": request.status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = await db.marketing_strategies.insert_one(config_doc)
        
        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Strategy saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving marketing strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving strategy: {str(e)}")

@router.put("/marketing-strategy/{module_id}/{strategy_id}")
async def update_marketing_strategy(
    module_id: int,
    strategy_id: str,
    request: MarketingStrategyConfig,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Update an existing marketing strategy"""
    try:
        from bson import ObjectId
        
        update_doc = {
            "updated_at": datetime.now(timezone.utc)
        }
        
        if request.strategy_name:
            update_doc["strategy_name"] = request.strategy_name
        if request.config:
            update_doc["config"] = request.config
        if request.ai_insights is not None:
            update_doc["ai_insights"] = request.ai_insights
        if request.status:
            update_doc["status"] = request.status
        
        result = await db.marketing_strategies.update_one(
            {"_id": ObjectId(strategy_id), "module_id": module_id, "user_email": email},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "id": strategy_id,
            "message": "Strategy updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating marketing strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating strategy: {str(e)}")

@router.delete("/marketing-strategy/{module_id}/{strategy_id}")
async def delete_marketing_strategy(
    module_id: int,
    strategy_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Delete a marketing strategy"""
    try:
        from bson import ObjectId
        
        result = await db.marketing_strategies.delete_one(
            {"_id": ObjectId(strategy_id), "module_id": module_id, "user_email": email}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "message": "Strategy deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting marketing strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting strategy: {str(e)}")

@router.get("/marketing-strategy/{module_id}/versions")
async def get_marketing_strategy_versions(
    module_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Get version history for a marketing strategy module"""
    try:
        versions = await db.marketing_strategies.find(
            {"module_id": module_id, "user_email": email},
            {"config": 0}  # Exclude config to reduce payload
        ).sort("created_at", -1).to_list(20)
        
        version_list = []
        for v in versions:
            version_list.append({
                "id": str(v.get("_id", "")),
                "name": v.get("version", "Unknown"),
                "createdAt": v.get("created_at", datetime.now(timezone.utc)).isoformat() if isinstance(v.get("created_at"), datetime) else v.get("created_at", ""),
                "owner": v.get("owner", email)
            })
        
        return {"versions": version_list}
    except Exception as e:
        logger.error(f"Error getting versions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving versions: {str(e)}")

@router.post("/marketing-strategy/{module_id}/generate-ai-insights")
async def generate_ai_insights(
    module_id: int,
    request: GenerateAIInsightsRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """Generate AI insights for a marketing strategy configuration"""
    try:
        from app.utils.llm_providers.factory import LLMProviderFactory
        
        # Get LLM provider
        llm_provider = LLMProviderFactory.get_provider()
        
        # Build prompt based on module type and configuration
        module_titles = {
            1: "Strategic Framework",
            2: "Channel Strategy",
            3: "Budget Allocation",
            4: "Market Segmentation",
            5: "Brand Positioning",
            6: "Competitive Strategy"
        }
        
        module_title = module_titles.get(module_id, "Marketing Strategy")
        config = request.config or {}
        
        # Create a comprehensive prompt
        # Build a more detailed, context-aware prompt
        config_summary = _format_config_for_prompt(config)
        
        prompt = f"""You are Vector AI, an expert strategic business intelligence analyst for ThriveBrands. Analyze the following {module_title} configuration and provide strategic, data-driven insights.

CONFIGURATION DATA:
{config_summary}

ANALYSIS REQUIREMENTS:
1. **Key Strategic Insights** (3-4 points):
   - Identify critical observations about the configuration
   - Highlight any gaps, misalignments, or opportunities
   - Point out what's working well and what needs attention
   - Be specific and reference actual values/choices from the configuration

2. **Strategic Strengths** (2-3 points):
   - Identify well-defined elements that create competitive advantage
   - Highlight strong strategic choices and their potential impact
   - Reference specific configuration elements that demonstrate strategic thinking

3. **Critical Opportunities** (3-4 points):
   - Identify specific areas for improvement with actionable recommendations
   - Suggest enhancements that align with the stated objectives
   - Provide concrete, implementable suggestions based on the configuration

4. **Actionable Recommendations** (4-5 specific actions):
   - Provide numbered, specific recommendations
   - Each recommendation should be actionable and tied to configuration elements
   - Include expected impact or rationale for each recommendation
   - Prioritize recommendations by strategic importance

5. **Risk Assessment** (2-3 key risks):
   - Identify potential risks or challenges based on the configuration
   - Assess feasibility of targets/goals given the current setup
   - Highlight any resource or strategic gaps

6. **Immediate Next Steps** (3-4 prioritized actions):
   - Provide a clear, prioritized action plan
   - Focus on what should be done first to move forward
   - Include timeline or priority indicators where relevant

IMPORTANT GUIDELINES:
- Reference specific values, targets, and choices from the configuration
- Be data-driven and specific, not generic
- Provide actionable insights that can be immediately implemented
- If configuration is incomplete, clearly identify what's missing and why it matters
- Connect recommendations to the stated objectives and targets
- Use business terminology appropriate for strategic planning
- Format with **bold** headings, numbered lists, and bullet points
- Keep total response between 600-800 words for comprehensive yet concise analysis

Generate a strategic analysis that a C-level executive would find valuable and actionable."""

        system_message = (
            "You are Vector AI, an elite strategic business intelligence analyst with 15+ years of experience "
            "in marketing strategy, business planning, and revenue optimization. You specialize in analyzing "
            "marketing strategy configurations and providing actionable, data-driven insights that drive business growth. "
            "Your analysis is always specific, actionable, and tied to actual configuration data. "
            "You think like a strategic consultant, identifying opportunities, risks, and providing clear recommendations."
        )
        
        # Generate AI insights with optimized balance between quality and speed
        ai_insights = await llm_provider.generate(
            prompt=prompt,
            custom_system_message=system_message,
            temperature=0.4,  # Slightly higher for more creative but still focused insights
            max_tokens=1200  # Increased for more comprehensive analysis while maintaining reasonable speed
        )
        
        return {
            "success": True,
            "ai_insights": ai_insights
        }
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating AI insights: {str(e)}")

def _format_config_for_prompt(config: Dict[str, Any]) -> str:
    """Format configuration data into a readable, structured string for the LLM prompt"""
    import json
    try:
        # Remove empty values and format nicely
        cleaned_config = {}
        for key, value in config.items():
            if value and value != [] and value != {}:
                cleaned_config[key] = value
        
        if not cleaned_config:
            return "⚠️ No configuration data provided. Please complete all sections (A, B, C, D) before generating insights."
        
        # Create a more readable, structured format
        formatted_parts = []
        
        # Strategic Framework specific formatting
        if 'strategicFramework' in cleaned_config:
            sf = cleaned_config['strategicFramework']
            formatted_parts.append("=== STRATEGIC FRAMEWORK ===")
            if sf.get('businessObjectives'):
                bo = sf['businessObjectives']
                formatted_parts.append(f"Primary Goal: {bo.get('primaryGoal', 'NOT SET')}")
                formatted_parts.append(f"Revenue Target: €{bo.get('revenueTarget', 'NOT SET')}")
                formatted_parts.append(f"Growth Target: {bo.get('growthTarget', 'NOT SET')}%")
                formatted_parts.append(f"Time Horizon: {bo.get('timeHorizon', 'NOT SET')}")
            if sf.get('strategicFocus'):
                sf_focus = sf['strategicFocus']
                formatted_parts.append(f"Market Focus: {', '.join(sf_focus.get('marketFocus', [])) or 'NOT SET'}")
                formatted_parts.append(f"Geography: {', '.join(sf_focus.get('geography', [])) or 'NOT SET'}")
                formatted_parts.append(f"Product Focus: {', '.join(sf_focus.get('productFocus', [])) or 'NOT SET'}")
            if sf.get('valueProposition'):
                vp = sf['valueProposition']
                formatted_parts.append(f"Core Value Message: {vp.get('coreMessage', 'NOT SET')}")
                formatted_parts.append(f"Differentiators: {', '.join(vp.get('differentiators', [])) or 'NONE'}")
                formatted_parts.append(f"Pricing Strategy: {vp.get('pricingStrategy', 'NOT SET')}")
            if sf.get('kpis'):
                kpis = sf['kpis']
                formatted_parts.append(f"North Star Metric: {kpis.get('northStarMetric', 'NOT SET')}")
                formatted_parts.append(f"Supporting KPIs: {', '.join(kpis.get('supportingKPIs', [])) or 'NONE'}")
        
        # Channel Strategy specific formatting
        elif 'channelStrategy' in cleaned_config:
            cs = cleaned_config['channelStrategy']
            formatted_parts.append("=== CHANNEL STRATEGY ===")
            formatted_parts.append(f"Selected Channels: {', '.join(cs.get('channels', [])) or 'NONE'}")
            if cs.get('channelRoles'):
                formatted_parts.append("Channel Roles:")
                for channel, role in cs['channelRoles'].items():
                    formatted_parts.append(f"  - {channel}: {role.get('objective', 'N/A')} ({role.get('funnelStage', 'N/A')})")
        
        # Budget Allocation specific formatting
        elif 'budgetAllocation' in cleaned_config:
            ba = cleaned_config['budgetAllocation']
            formatted_parts.append("=== BUDGET ALLOCATION ===")
            formatted_parts.append(f"Total Budget: {ba.get('currency', '€')}{ba.get('totalBudget', 'NOT SET')}")
            formatted_parts.append(f"Time Period: {ba.get('timePeriod', 'NOT SET')}")
        
        # Market Segmentation specific formatting
        elif 'marketSegmentation' in cleaned_config:
            ms = cleaned_config['marketSegmentation']
            formatted_parts.append("=== MARKET SEGMENTATION ===")
            formatted_parts.append(f"Segmentation Types: {', '.join(ms.get('segmentationType', [])) or 'NONE'}")
            if ms.get('segments'):
                formatted_parts.append(f"Number of Segments: {len(ms['segments'])}")
        
        # Brand Positioning specific formatting
        elif 'brandPositioning' in cleaned_config:
            bp = cleaned_config['brandPositioning']
            formatted_parts.append("=== BRAND POSITIONING ===")
            if bp.get('brandIdentity'):
                formatted_parts.append(f"Brand Personality: {', '.join(bp['brandIdentity'].get('personality', [])) or 'NONE'}")
                formatted_parts.append(f"Brand Tone: {bp['brandIdentity'].get('tone', 'NOT SET')}")
        
        # Competitive Strategy specific formatting
        elif 'competitiveStrategy' in cleaned_config:
            comp = cleaned_config['competitiveStrategy']
            if comp.get('competitors'):
                formatted_parts.append("=== COMPETITIVE STRATEGY ===")
                formatted_parts.append(f"Tracked Competitors: {len(comp['competitors'])}")
        
        # If no specific formatting, use JSON as fallback
        if not formatted_parts:
            formatted_parts.append("Configuration Details:")
            formatted_parts.append(json.dumps(cleaned_config, indent=2, default=str))
        
        return "\n".join(formatted_parts)
    except Exception as e:
        logger.error(f"Error formatting config: {str(e)}")
        return json.dumps(config, indent=2, default=str) if config else "No configuration data provided."

