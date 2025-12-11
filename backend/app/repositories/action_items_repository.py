"""
Action Items Repository
Handles database operations for action items
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.action_items import ActionItem, ActionItemsResponse
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ActionItemsRepository:
    """Repository for action items operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.cockpit_action_items
    
    async def find_one(self) -> Optional[Dict[str, Any]]:
        """Find the action items document (there's only one)"""
        return await self.collection.find_one({})
    
    async def upsert(self, data: Dict[str, Any]) -> Any:
        """Insert or update action items document"""
        return await self.collection.update_one(
            {},
            {"$set": data},
            upsert=True
        )

