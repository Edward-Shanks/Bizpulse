"""
Business data repository - Database operations for business_data collection
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BusinessDataRepository:
    """Repository for business_data collection operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.business_data
    
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
    
    async def insert_many(self, documents: List[Dict[str, Any]]) -> None:
        """Insert multiple documents"""
        if documents:
            await self.collection.insert_many(documents)
    
    async def delete_many(self, query: Dict[str, Any] = None) -> int:
        """Delete documents matching query"""
        result = await self.collection.delete_many(query or {})
        return result.deleted_count
    
    async def find(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """Find documents matching query"""
        cursor = self.collection.find(query or {}, projection or {})
        return await cursor.to_list(limit)



