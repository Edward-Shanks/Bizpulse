"""
Shopify data repository - Database operations for shopify_data collection
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ShopifyDataRepository:
    """Repository for shopify_data collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.shopify_data
    
    async def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query"""
        return await self.collection.count_documents(query or {})
    
    async def distinct(self, field: str, query: Dict[str, Any] = None) -> List[Any]:
        """Get distinct values for a field"""
        return await self.collection.distinct(field, query or {})
    
    async def aggregate(self, pipeline: List[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        cursor = self.collection.aggregate(pipeline)
        if limit:
            return await cursor.to_list(limit)
        return await cursor.to_list(10000)
    
    async def find_one(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find one document matching query"""
        return await self.collection.find_one(query or {}, projection or {})



