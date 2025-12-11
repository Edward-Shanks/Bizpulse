"""
Kanban Repository
Handles database operations for kanban (campaigns and goals)
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class KanbanRepository:
    """Repository for kanban operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.kanban_collection = db.kanban
        self.goals_collection = db.goals  # Note: original code uses 'goals' collection
    
    # Kanban (campaigns) operations
    async def find_kanban(self) -> Optional[Dict[str, Any]]:
        """Find the kanban document (there's only one)"""
        return await self.kanban_collection.find_one({})
    
    async def insert_kanban(self, document: Dict[str, Any]) -> Any:
        """Insert a new kanban document"""
        return await self.kanban_collection.insert_one(document)
    
    async def update_kanban(self, update: Dict[str, Any]) -> Any:
        """Update the kanban document"""
        return await self.kanban_collection.update_one(
            {},
            {"$set": update}
        )
    
    # Goals operations
    async def find_goals_by_campaign(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Find goals for a specific campaign"""
        cursor = self.goals_collection.find({"campaignId": campaign_id})
        return await cursor.to_list(1000)
    
    async def find_goal_by_id(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Find a goal by ID"""
        return await self.goals_collection.find_one({"id": goal_id})
    
    async def insert_goal(self, goal: Dict[str, Any]) -> Any:
        """Insert a new goal"""
        return await self.goals_collection.insert_one(goal)
    
    async def update_goal(self, goal_id: str, update: Dict[str, Any]) -> Any:
        """Update a goal"""
        return await self.goals_collection.update_one(
            {"id": goal_id},
            {"$set": update}
        )
    
    async def delete_goal(self, goal_id: str) -> Any:
        """Delete a goal"""
        return await self.goals_collection.delete_one({"id": goal_id})

