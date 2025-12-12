"""
Filter service - Handles dynamic filter options with cascading filters
Returns available filter values based on current filter selections
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
from app.repositories.business_data_repository import BusinessDataRepository
from app.utils.query_builder import build_analytics_query, apply_business_filter
from app.utils.helpers import normalize_category_name, parse_list
import logging
import re

logger = logging.getLogger(__name__)

class FilterService:
    """Service for filter operations with cascading/dynamic filtering"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.business_data_repo = BusinessDataRepository(db)
        self.db = db
    
    def _format_month_abbreviation(self, month_name: str) -> str:
        """Convert full month name to abbreviation (Jan, Feb, Mar, etc.)"""
        month_map = {
            'January': 'Jan', 'February': 'Feb', 'March': 'Mar',
            'April': 'Apr', 'May': 'May', 'June': 'Jun',
            'July': 'Jul', 'August': 'Aug', 'September': 'Sep',
            'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
        }
        return month_map.get(month_name, month_name[:3])
    
    def _sort_months(self, months: List[str]) -> List[str]:
        """Sort months in calendar order"""
        month_order = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        return sorted(months, key=lambda x: month_order.get(x, 999))
    
    async def _build_base_query(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None,
        categories: Optional[str] = None,
        customers: Optional[str] = None,
        sub_categories: Optional[str] = None,
        exclude_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build base query from filters, excluding the field we're getting options for
        This ensures cascading filters work correctly
        """
        # Build query with all filters
        query = build_analytics_query(
            years=years if exclude_field != 'Year' else None,
            months=months if exclude_field != 'Month_Name' else None,
            channels=channels if exclude_field != 'Channel' else None,
            brands=brands if exclude_field != 'Brand' else None,
            categories=categories if exclude_field != 'Category' else None,
            customers=customers if exclude_field != 'Customer' else None,
            sub_categories=sub_categories if exclude_field not in ['Sub_Cat', 'Sub_Category'] else None
        )
        
        # Apply business filter if needed
        if businesses and exclude_field != 'Business':
            query = await apply_business_filter(query, businesses, self.db)
        
        # Remove the excluded field from query
        if exclude_field in query:
            del query[exclude_field]
        
        # Also remove Customer if it's the excluded field
        if exclude_field == 'Customer' and 'Customer' in query:
            del query['Customer']
        
        # Handle sub_categories exclusion - remove $or conditions related to Sub_Cat/Sub_Category
        if exclude_field in ['Sub_Cat', 'Sub_Category']:
            if '$or' in query:
                # Filter out Sub_Cat and Sub_Category conditions from $or
                filtered_or = [
                    condition for condition in query['$or']
                    if 'Sub_Cat' not in condition and 'Sub_Category' not in condition
                ]
                if filtered_or:
                    query['$or'] = filtered_or
                else:
                    del query['$or']
            # Also check $and conditions
            if '$and' in query:
                filtered_and = []
                for condition in query['$and']:
                    if isinstance(condition, dict) and '$or' in condition:
                        filtered_or = [
                            c for c in condition['$or']
                            if 'Sub_Cat' not in c and 'Sub_Category' not in c
                        ]
                        if filtered_or:
                            filtered_and.append({'$or': filtered_or})
                    elif not any(key in condition for key in ['Sub_Cat', 'Sub_Category']):
                        filtered_and.append(condition)
                if filtered_and:
                    query['$and'] = filtered_and
                else:
                    del query['$and']
        
        # Handle $or conditions properly - if exclude_field is Category and we have $or, 
        # we need to keep other $or conditions (like sub_categories) but remove Category regex
        if exclude_field == 'Category' and '$or' in query:
            # Filter out Category conditions from $or
            filtered_or = [
                condition for condition in query['$or']
                if 'Category' not in condition
            ]
            if filtered_or:
                query['$or'] = filtered_or
            else:
                del query['$or']
        
        # Also handle $and conditions if they exist
        if exclude_field == 'Category' and '$and' in query:
            # Remove Category conditions from $and
            filtered_and = []
            for condition in query['$and']:
                if isinstance(condition, dict) and '$or' in condition:
                    # Check if this $or contains Category conditions
                    filtered_or = [
                        c for c in condition['$or']
                        if 'Category' not in c
                    ]
                    if filtered_or:
                        filtered_and.append({'$or': filtered_or})
                elif 'Category' not in condition:
                    filtered_and.append(condition)
            if filtered_and:
                query['$and'] = filtered_and
            else:
                del query['$and']
        
        return query
    
    async def get_filter_options(
        self,
        years: Optional[str] = None,
        months: Optional[str] = None,
        businesses: Optional[str] = None,
        channels: Optional[str] = None,
        brands: Optional[str] = None,
        categories: Optional[str] = None,
        customers: Optional[str] = None,
        sub_categories: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """
        Get dynamic filter options based on current filter selections
        Returns available values for each filter field, respecting current selections
        
        This implements cascading filters:
        - Selecting a category shows only years/months where that category exists
        - Selecting a year shows only months/brands/categories for that year
        - And so on...
        """
        logger.info(f"🔍 Getting dynamic filter options - Years: {years}, Months: {months}, Categories: {categories}, Customers: {customers}, SubCategories: {sub_categories}")
        
        # Years: Get all years that exist given current filters (excluding Year filter itself)
        years_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Year'
        )
        years_match = {"$match": years_query} if years_query else {"$match": {}}
        years_pipeline = [
            years_match,
            {"$match": {"Year": {"$ne": None, "$exists": True, "$type": "number"}}},
            {"$group": {"_id": "$Year"}},
            {"$sort": {"_id": 1}}
        ]
        years_results = await self.business_data_repo.aggregate(years_pipeline)
        years_list = sorted([int(item['_id']) for item in years_results if item.get('_id') is not None])
        
        # Months: Get all months that exist given current filters (excluding Month_Name filter itself)
        # Format as abbreviations (Jan, Feb, Mar, etc.)
        months_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Month_Name'
        )
        months_match = {"$match": months_query} if months_query else {"$match": {}}
        months_pipeline = [
            months_match,
            {"$match": {"Month_Name": {"$ne": None, "$exists": True, "$nin": ["", " ", None]}}},
            {"$group": {"_id": "$Month_Name"}},
            {"$sort": {"_id": 1}}
        ]
        months_results = await self.business_data_repo.aggregate(months_pipeline)
        months_full = [item['_id'] for item in months_results if item.get('_id') and str(item['_id']).strip()]
        months_sorted = self._sort_months(months_full)
        months_list = [self._format_month_abbreviation(m) for m in months_sorted]
        
        # Businesses: Get all businesses that exist given current filters (excluding Business filter itself)
        businesses_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Business'
        )
        businesses_match = {"$match": businesses_query} if businesses_query else {"$match": {}}
        businesses_pipeline = [
            businesses_match,
            {"$match": {"Business": {"$ne": None, "$exists": True, "$nin": ["", " ", None]}}},
            {"$group": {"_id": "$Business"}},
            {"$sort": {"_id": 1}}
        ]
        businesses_results = await self.business_data_repo.aggregate(businesses_pipeline)
        businesses_list = sorted([str(item['_id']) for item in businesses_results if item.get('_id') and str(item['_id']).strip()])
        
        # Channels: Get all channels that exist given current filters (excluding Channel filter itself)
        channels_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Channel'
        )
        channels_match = {"$match": channels_query} if channels_query else {"$match": {}}
        channels_pipeline = [
            channels_match,
            {"$match": {"Channel": {"$ne": None, "$exists": True, "$nin": ["", " ", None]}}},
            {"$group": {"_id": "$Channel"}},
            {"$sort": {"_id": 1}}
        ]
        channels_results = await self.business_data_repo.aggregate(channels_pipeline)
        channels_list = sorted([str(item['_id']) for item in channels_results if item.get('_id') and str(item['_id']).strip()])
        
        # Brands: Get all brands that exist given current filters (excluding Brand filter itself)
        brands_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Brand'
        )
        brands_match = {"$match": brands_query} if brands_query else {"$match": {}}
        brands_pipeline = [
            brands_match,
            {"$match": {"Brand": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None", None]}}},
            {"$group": {"_id": "$Brand"}},
            {"$sort": {"_id": 1}}
        ]
        brands_results = await self.business_data_repo.aggregate(brands_pipeline)
        brands_list = sorted([str(item['_id']) for item in brands_results if item.get('_id') and str(item['_id']).strip() and str(item['_id']).lower() not in ["unknown", "none", "null"]])
        
        # Categories: Get all categories that exist given current filters (excluding Category filter itself)
        # Use normalized categories for case-insensitive matching
        categories_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Category'
        )
        categories_match = {"$match": categories_query} if categories_query else {"$match": {}}
        categories_pipeline = [
            categories_match,
            {"$match": {"Category": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None", None]}}},
            {"$group": {"_id": "$Category"}},
            {"$sort": {"_id": 1}}
        ]
        categories_results = await self.business_data_repo.aggregate(categories_pipeline)
        
        # Normalize and deduplicate categories
        categories_dict = {}
        for item in categories_results:
            cat_name = item.get('_id')
            if cat_name and str(cat_name).strip() and str(cat_name).lower() not in ["unknown", "none", "null"]:
                normalized = normalize_category_name(str(cat_name))
                if normalized and normalized not in categories_dict:
                    categories_dict[normalized] = normalized
        
        categories_list = sorted(list(categories_dict.values()))
        
        # Customers: Get all customers that exist given current filters (excluding Customer filter itself)
        customers_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Customer'
        )
        customers_match = {"$match": customers_query} if customers_query else {"$match": {}}
        customers_pipeline = [
            customers_match,
            {"$match": {"Customer": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None", None]}}},
            {"$group": {"_id": "$Customer"}},
            {"$sort": {"_id": 1}}
        ]
        customers_results = await self.business_data_repo.aggregate(customers_pipeline)
        customers_list = sorted([str(item['_id']) for item in customers_results if item.get('_id') and str(item['_id']).strip() and str(item['_id']).lower() not in ["unknown", "none", "null"]])
        
        # Sub-Categories: Get all sub-categories that exist given current filters (excluding Sub_Cat/Sub_Category filter itself)
        # Handle both Sub_Cat (normalized) and Sub_Category (legacy) fields
        sub_categories_query = await self._build_base_query(
            years=years, months=months, businesses=businesses,
            channels=channels, brands=brands, categories=categories, customers=customers, sub_categories=sub_categories,
            exclude_field='Sub_Cat'
        )
        sub_categories_match = {"$match": sub_categories_query} if sub_categories_query else {"$match": {}}
        sub_categories_pipeline = [
            sub_categories_match,
            {
                "$match": {
                    "$or": [
                        {"Sub_Cat": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None", None]}},
                        {"Sub_Category": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None", None]}}
                    ]
                }
            },
            {
                "$project": {
                    "sub_cat": {"$ifNull": ["$Sub_Cat", "$Sub_Category"]}
                }
            },
            {"$group": {"_id": "$sub_cat"}},
            {"$sort": {"_id": 1}}
        ]
        sub_categories_results = await self.business_data_repo.aggregate(sub_categories_pipeline)
        sub_categories_list = sorted([
            str(item['_id']) for item in sub_categories_results 
            if item.get('_id') and str(item['_id']).strip() and str(item['_id']).lower() not in ["unknown", "none", "null"]
        ])
        
        logger.info(f"✅ Filter options: {len(years_list)} years, {len(months_list)} months, {len(businesses_list)} businesses, {len(channels_list)} channels, {len(brands_list)} brands, {len(categories_list)} categories, {len(customers_list)} customers, {len(sub_categories_list)} sub_categories")
        
        return {
            "years": years_list,
            "months": months_list,
            "businesses": businesses_list,
            "channels": channels_list,
            "brands": brands_list,
            "categories": categories_list,
            "customers": customers_list,
            "sub_categories": sub_categories_list
        }

# Factory function
def get_filter_service(db: AsyncIOMotorDatabase) -> FilterService:
    """Get filter service instance"""
    return FilterService(db)
