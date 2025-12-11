"""
Root Cause Analysis Repository
Handles database operations for root cause analysis
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RootCauseRepository:
    """Repository for root cause analysis operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.root_cause_analysis
    
    async def find_one(self) -> Optional[Dict[str, Any]]:
        """Find the root cause analysis document (there's only one)"""
        return await self.collection.find_one({})
    
    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a new root cause analysis document"""
        return await self.collection.insert_one(document)
    
    async def update_one(self, update: Dict[str, Any]) -> Any:
        """Update the root cause analysis document"""
        return await self.collection.update_one(
            {},
            {"$set": update}
        )

