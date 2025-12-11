"""
Action Items Service
Business logic for action items
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.action_items_repository import ActionItemsRepository
from app.models.action_items import ActionItem, ActionItemsResponse
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default action items data
DEFAULT_ACTION_ITEMS = {
    "critical": [
        {
            "id": 1,
            "title": "Reverse 45% YoY Revenue Decline: Emergency Recovery Plan",
            "dueDate": "2025-12-15",
            "priority": "high",
            "impact": "high",
            "category": "critical",
            "description": "Urgent action required to address significant year-over-year revenue decline"
        },
        {
            "id": 2,
            "title": "Reduce Grocery Channel Concentration from 73.4%",
            "dueDate": "2025-01-20",
            "priority": "high",
            "impact": "high",
            "category": "critical",
            "description": "Diversify channel mix to reduce dependency on grocery channel"
        },
        {
            "id": 3,
            "title": "Stabilize Top 5 Customer Relationships",
            "dueDate": "2025-01-15",
            "priority": "medium",
            "impact": "high",
            "category": "critical",
            "description": "Focus on maintaining and strengthening relationships with top customers"
        },
        {
            "id": 4,
            "title": "Audit Food Business Unit Margin Compression",
            "dueDate": "2025-02-01",
            "priority": "medium",
            "impact": "medium",
            "category": "critical",
            "description": "Investigate and address margin compression in food business unit"
        },
        {
            "id": 5,
            "title": "Launch Online Channel Growth Initiative",
            "dueDate": "2025-02-28",
            "priority": "low",
            "impact": "medium",
            "category": "critical",
            "description": "Develop and execute strategy to grow online channel presence"
        }
    ],
    "impact": [
        {
            "id": 6,
            "title": "Scale Food Business to €22M+ via Category Expansion",
            "dueDate": "2025-03-15",
            "priority": "high",
            "impact": "high",
            "category": "impact",
            "description": "Expand food business categories to achieve revenue target of €22M+"
        },
        {
            "id": 7,
            "title": "Develop Wholesale Channel Acceleration Program",
            "dueDate": "2025-02-28",
            "priority": "high",
            "impact": "high",
            "category": "impact",
            "description": "Create program to accelerate growth in wholesale channel"
        },
        {
            "id": 8,
            "title": "Optimize Household & Beauty Segment Efficiency",
            "dueDate": "2025-03-20",
            "priority": "medium",
            "impact": "medium",
            "category": "impact",
            "description": "Improve operational efficiency in household and beauty segments"
        },
        {
            "id": 9,
            "title": "Build International Channel to 5% of Revenue Mix",
            "dueDate": "2025-03-31",
            "priority": "low",
            "impact": "medium",
            "category": "impact",
            "description": "Develop international channel to reach 5% of total revenue"
        }
    ]
}

class ActionItemsService:
    """Service for action items business logic"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repo = ActionItemsRepository(db)
    
    async def get_action_items(self) -> ActionItemsResponse:
        """Get action items from MongoDB, auto-seed if empty"""
        logger.info("🔍 Fetching action items from MongoDB")
        
        cached_doc = await self.repo.find_one()
        
        if cached_doc:
            logger.info("✅ Found action items document in MongoDB")
            logger.info(f"   Document keys: {list(cached_doc.keys())}")
            logger.info(f"   Critical items count: {len(cached_doc.get('critical', []))}")
            logger.info(f"   Impact items count: {len(cached_doc.get('impact', []))}")
            
            critical_items = []
            impact_items = []
            
            # Parse critical items with error handling
            for idx, item in enumerate(cached_doc.get('critical', [])):
                try:
                    if idx == 0:
                        logger.info(f"   Sample critical item keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    critical_items.append(ActionItem(**item))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping invalid critical item {idx}: {e}")
                    logger.warning(f"   Item data: {item}")
                    continue
            
            # Parse impact items with error handling
            for idx, item in enumerate(cached_doc.get('impact', [])):
                try:
                    if idx == 0:
                        logger.info(f"   Sample impact item keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    impact_items.append(ActionItem(**item))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping invalid impact item {idx}: {e}")
                    logger.warning(f"   Item data: {item}")
                    continue
            
            logger.info(f"✅ Successfully loaded {len(critical_items)} critical and {len(impact_items)} impact items")
            
            # If we have valid items, return them
            if critical_items or impact_items:
                return ActionItemsResponse(
                    critical=critical_items,
                    impact=impact_items
                )
            else:
                # Document exists but has no valid items - need to re-seed
                logger.warning("⚠️ Document exists but has no valid items, re-seeding...")
                cached_doc = None  # Force re-seeding
        
        # Auto-seed action items if collection is empty or has no valid items
        if not cached_doc:
            logger.warning("⚠️ No action items document found in MongoDB or document has no valid items")
            logger.info("ℹ️ Auto-seeding action items...")
            
            action_items_data = {
                **DEFAULT_ACTION_ITEMS,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # Save to MongoDB with upsert
            try:
                result = await self.repo.upsert(action_items_data)
                logger.info(f"✅ MongoDB update result: matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save action items to MongoDB: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            logger.info(f"✅ Auto-seeded {len(action_items_data['critical'])} critical and {len(action_items_data['impact'])} impact items")
            
            # Parse and return the seeded items
            try:
                critical_items = [ActionItem(**item) for item in action_items_data['critical']]
                impact_items = [ActionItem(**item) for item in action_items_data['impact']]
                
                return ActionItemsResponse(
                    critical=critical_items,
                    impact=impact_items
                )
            except Exception as e:
                logger.error(f"❌ Failed to parse seeded action items: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                # Return empty arrays as fallback
                return ActionItemsResponse(
                    critical=[],
                    impact=[]
                )
    
    async def seed_action_items(self) -> Dict[str, Any]:
        """Seed action items in MongoDB if collection is empty"""
        # Check if data already exists
        existing = await self.repo.find_one()
        if existing and (existing.get('critical') or existing.get('impact')):
            critical_count = len(existing.get('critical', []))
            impact_count = len(existing.get('impact', []))
            logger.info(f"Action items already exist: {critical_count} critical, {impact_count} impact")
            return {
                "message": "Action items already exist",
                "critical_count": critical_count,
                "impact_count": impact_count
            }
        
        # Action items data
        action_items_data = {
            **DEFAULT_ACTION_ITEMS,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into MongoDB
        result = await self.repo.upsert(action_items_data)
        
        logger.info(f"✅ Seeded action items: {len(action_items_data['critical'])} critical, {len(action_items_data['impact'])} impact")
        
        return {
            "message": "Action items seeded successfully",
            "critical_count": len(action_items_data['critical']),
            "impact_count": len(action_items_data['impact'])
        }

