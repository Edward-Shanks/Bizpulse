"""
Filter service - Handles dynamic filter options
Returns available filter values based on current filter selections
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
from app.repositories.business_data_repository import BusinessDataRepository
from app.utils.query_builder import build_analytics_query, apply_business_filter
from app.utils.helpers import normalize_category_name
import logging
import re

logger = logging.getLogger(__name__)

class FilterService:
    """Service for filter operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.business_data_repo = BusinessDataRepository(db)
        self.db = db
    
    async def get_filter_options(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None,
        categories: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """
        Get dynamic filter options based on current filter selections
        Returns available values for each filter field
        """
        logger.info("🔍 Getting dynamic filter options")
        
        # Build query from current filters (excluding the field we're getting options for)
        query = build_analytics_query(
            years=years, months=months, channels=channels,
            brands=brands, categories=None  # Exclude categories from query when getting category options
        )
        
        if businesses:
            query = await apply_business_filter(query, businesses, self.db)
        
        # Remove category from query if we're getting category options
        if categories:
            # When getting other options, we need to include category in the query
            # But when getting category options, we exclude it
            pass  # Categories are handled separately below
        
        logger.info(f"📊 Building dynamic filter options with query: {query}")
        
        # Get distinct values for each filter field, respecting current filter constraints
        
        # Years: Get all years that exist given current filters (excluding Year filter itself)
        years_query = {k: v for k, v in query.items() if k != 'Year'}
        years_match = {"$match": years_query} if years_query else {"$match": {}}
        years_pipeline = [years_match, {"$group": {"_id": "$Year"}}]
        years_results = await self.business_data_repo.aggregate(years_pipeline)
        years = sorted([int(item['_id']) for item in years_results if item.get('_id') is not None])
        
        # Months: Get all months that exist given current filters (excluding Month_Name filter itself)
        months_query = {k: v for k, v in query.items() if k != 'Month_Name'}
        months_match = {"$match": months_query} if months_query else {"$match": {}}
        months_pipeline = [months_match, {"$group": {"_id": "$Month_Name"}}]
        months_results = await self.business_data_repo.aggregate(months_pipeline)
        months = [item['_id'] for item in months_results if item.get('_id') is not None]
        
        # Businesses: Get all businesses that exist given current filters (excluding Business filter itself)
        businesses_query = {k: v for k, v in query.items() if k != 'Business'}
        if businesses_query:
            businesses_match = {"$match": businesses_query}
            businesses_pipeline = [businesses_match, {"$group": {"_id": "$Business"}}]
        else:
            businesses_pipeline = [{"$group": {"_id": "$Business"}}]
        businesses_results = await self.business_data_repo.aggregate(businesses_pipeline)
        businesses = [str(item['_id']) for item in businesses_results if item.get('_id') is not None]
        
        # Channels: Get all channels that exist given current filters (excluding Channel filter itself)
        channels_query = {k: v for k, v in query.items() if k != 'Channel'}
        channels_match = {"$match": channels_query} if channels_query else {"$match": {}}
        channels_pipeline = [channels_match, {"$group": {"_id": "$Channel"}}]
        channels_results = await self.business_data_repo.aggregate(channels_pipeline)
        channels = [item['_id'] for item in channels_results if item.get('_id') is not None]
        
        # Brands: Get all brands that exist given current filters (excluding Brand filter itself)
        brands_query = {k: v for k, v in query.items() if k != 'Brand'}
        brands_match = {"$match": brands_query} if brands_query else {"$match": {}}
        brands_pipeline = [brands_match, {"$group": {"_id": "$Brand"}}]
        brands_results = await self.business_data_repo.aggregate(brands_pipeline)
        brands = [item['_id'] for item in brands_results if item.get('_id') is not None]
        
        # Categories: Get all categories that exist given current filters (excluding Category filter itself)
        # Use normalized categories for case-insensitive matching
        categories_query = {k: v for k, v in query.items() if k != 'Category'}
        categories_match = {"$match": categories_query} if categories_query else {"$match": {}}
        categories_pipeline = [categories_match, {"$group": {"_id": "$Category"}}]
        categories_results = await self.business_data_repo.aggregate(categories_pipeline)
        
        # Normalize and deduplicate categories
        categories_dict = {}
        for item in categories_results:
            cat_name = item.get('_id')
            if cat_name and cat_name != "Unknown":
                normalized = normalize_category_name(cat_name)
                if normalized not in categories_dict:
                    categories_dict[normalized] = normalized
        
        categories = sorted(list(categories_dict.values()))
        
        logger.info(f"✅ Filter options: {len(years)} years, {len(months)} months, {len(businesses)} businesses, {len(channels)} channels, {len(brands)} brands, {len(categories)} categories")
        
        return {
            "years": years,
            "months": months,
            "businesses": businesses,
            "channels": channels,
            "brands": brands,
            "categories": categories
        }

# Factory function
def get_filter_service(db: AsyncIOMotorDatabase) -> FilterService:
    """Get filter service instance"""
    return FilterService(db)

