"""
Query builder utilities for MongoDB
Handles filter parsing and query construction
"""
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.helpers import parse_list
import logging
import re

logger = logging.getLogger(__name__)

async def apply_business_filter(
    query: Dict[str, Any],
    businesses: str,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Apply business filter with smart matching
    Handles business names with commas and partial matching
    """
    if not businesses:
        return query
    
    # URL decode and parse business list
    import urllib.parse
    businesses_decoded = urllib.parse.unquote(businesses)
    
    # Smart parsing: Handle business names that contain commas (e.g., "Brillo, Goddards & KMPL")
    # Strategy: First try the full string as a single business, then try splitting if needed
    all_businesses = await db.business_data.distinct('Business')
    
    # First, try matching the entire decoded string as a single business name
    full_string_test = {'Business': businesses_decoded.strip()}
    full_string_count = await db.business_data.count_documents(full_string_test)
    
    if full_string_count > 0:
        # The full string is a valid business name (comma is part of the name)
        business_list = [businesses_decoded.strip()]
        logger.info(f"🔍 Business filter - Full string match: '{businesses_decoded}' is a single business")
    else:
        # Try splitting by comma - but validate each part
        potential_parts = [b.strip() for b in businesses_decoded.split(',') if b.strip()]
        business_list = []
        
        # Check if split parts are valid business names
        for part in potential_parts:
            part_test = {'Business': part}
            part_count = await db.business_data.count_documents(part_test)
            if part_count > 0:
                # This part is a valid business name
                business_list.append(part)
            else:
                # Part doesn't match - might be part of a business name with comma
                # Try combining with previous part if we have one
                if business_list:
                    combined = f"{business_list[-1]}, {part}"
                    combined_test = {'Business': combined}
                    combined_count = await db.business_data.count_documents(combined_test)
                    if combined_count > 0:
                        # Combined name is valid - replace last item
                        business_list[-1] = combined
                    else:
                        # Still not valid - add as-is (will be handled by matching logic)
                        business_list.append(part)
                else:
                    # First part doesn't match - might be part of comma-separated name
                    # Add it and let matching logic handle it
                    business_list.append(part)
    
    if not business_list:
        return query
    
    # Get all unique business names from database for matching
    all_businesses_lower = {b.lower(): b for b in all_businesses if b}
    
    # Try to match each business name
    matched_businesses = []
    
    for business_input in business_list:
        business_lower = business_input.lower().strip()
        
        # Strategy 1: Exact match (case-insensitive)
        if business_lower in all_businesses_lower:
            matched_businesses.append(all_businesses_lower[business_lower])
            continue
        
        # Strategy 2: Try the full string as-is (for names with commas)
        for db_business in all_businesses:
            if db_business and db_business.lower() == business_lower:
                matched_businesses.append(db_business)
                break
        else:
            # Strategy 3: Word-set matching (for partial matches)
            input_words = set(business_lower.split())
            best_match = None
            best_score = 0
            
            for db_business in all_businesses:
                if not db_business:
                    continue
                db_words = set(db_business.lower().split())
                
                # Calculate word overlap
                common_words = input_words & db_words
                if len(common_words) > 0:
                    # All input words must be in database business name
                    if input_words.issubset(db_words):
                        score = len(common_words) / len(input_words)
                        if score > best_score:
                            best_score = score
                            best_match = db_business
            
            if best_match:
                matched_businesses.append(best_match)
            else:
                logger.warning(f"Could not match business: {business_input}")
    
    if matched_businesses:
        query['Business'] = {'$in': matched_businesses}
    
    return query

def build_analytics_query(
    years: Optional[str] = None,
    months: Optional[str] = None,
    businesses: Optional[str] = None,
    channels: Optional[str] = None,
    brands: Optional[str] = None,
    categories: Optional[str] = None,
    customers: Optional[str] = None,
    sub_categories: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build MongoDB query from filter parameters
    Returns base query dict (business filter needs to be applied separately)
    """
    query: Dict[str, Any] = {}
    
    if years:
        year_list = parse_list(years, int)
        if year_list:
            query['Year'] = {'$in': year_list}
    
    if months:
        month_list = parse_list(months)
        if month_list:
            query['Month_Name'] = {'$in': month_list}
    
    if channels:
        channel_list = parse_list(channels)
        if channel_list:
            query['Channel'] = {'$in': channel_list}
    
    if brands:
        brand_list = parse_list(brands)
        if brand_list:
            query['Brand'] = {'$in': brand_list}
    
    if categories:
        category_list = parse_list(categories)
        if category_list:
            # Normalize categories for case-insensitive matching
            from app.utils.helpers import normalize_category_name
            import re
            normalized_categories = [normalize_category_name(cat) for cat in category_list]
            # Use $or with regex for case-insensitive matching (MongoDB doesn't support $in with regex)
            # Escape special regex characters
            if len(normalized_categories) == 1:
                # Single category - use regex directly with escaped special chars
                escaped_cat = re.escape(normalized_categories[0])
                query['Category'] = {'$regex': f'^{escaped_cat}$', '$options': 'i'}
            else:
                # Multiple categories - use $or with regex
                category_or_conditions = [
                    {'Category': {'$regex': f'^{re.escape(cat)}$', '$options': 'i'}} 
                    for cat in normalized_categories
                ]
                query['$or'] = category_or_conditions
    
    if customers:
        customer_list = parse_list(customers)
        if customer_list:
            query['Customer'] = {'$in': customer_list}
    
    if sub_categories:
        subcategory_list = parse_list(sub_categories)
        if subcategory_list:
            # Handle both Sub_Cat (normalized) and Sub_Category (legacy)
            # If $or already exists (from categories), combine with $and
            subcat_or = [
                {'Sub_Cat': {'$in': subcategory_list}},
                {'Sub_Category': {'$in': subcategory_list}},
            ]
            if '$or' in query:
                # Categories already created $or, combine with $and
                existing_or = query.pop('$or')
                query['$and'] = [
                    {'$or': existing_or},
                    {'$or': subcat_or}
                ]
            else:
                query['$or'] = subcat_or
    
    return query

async def build_mongodb_query_from_context(
    context: Dict[str, Any],
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """Build MongoDB query from frontend context filters"""
    query = {}
    
    # Years
    years = context.get('selectedYears') or context.get('year') or []
    if isinstance(years, str):
        years = parse_list(years, int)
    if years and len(years) > 0:
        query['Year'] = {'$in': [int(y) for y in years]}
    
    # Months
    months = context.get('selectedMonths') or context.get('month') or []
    if isinstance(months, str):
        months = parse_list(months)
    if months and len(months) > 0:
        query['Month_Name'] = {'$in': months}
    
    # Businesses - use smart matching
    businesses = context.get('selectedBusinesses') or context.get('business') or []
    if businesses:
        if isinstance(businesses, list):
            # If it's already a list, join it for the filter function
            businesses_str = ','.join([str(b) for b in businesses])
        else:
            businesses_str = str(businesses)
        # Apply smart business filter
        query = await apply_business_filter(query, businesses_str, db)
    
    # Brands
    brands = context.get('selectedBrands') or context.get('brand') or []
    if isinstance(brands, str):
        brands = parse_list(brands)
    if brands and len(brands) > 0:
        query['Brand'] = {'$in': brands}
    
    # Channels
    channels = context.get('selectedChannels') or context.get('channel') or []
    if isinstance(channels, str):
        channels = parse_list(channels)
    if channels and len(channels) > 0:
        query['Channel'] = {'$in': channels}
    
    # Customers
    customers = context.get('selectedCustomers') or context.get('customer') or []
    if isinstance(customers, str):
        customers = parse_list(customers)
    if customers and len(customers) > 0:
        query['Customer'] = {'$in': customers}
    
    # Categories
    categories = context.get('selectedCategories') or context.get('category') or []
    if isinstance(categories, str):
        categories = parse_list(categories)
    if categories and len(categories) > 0:
        query['Category'] = {'$in': categories}
    
    return query

async def parse_query_from_natural_language(
    message: str,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Parse natural language query to extract filters and build MongoDB query
    Handles: business, channel, customer, brand, category, year, month, quarter
    
    Returns:
        {
            "filters": {...},  # MongoDB match filters
            "intent": {
                "metric": "Gross_Sales" | "Revenue" | "Units" | etc.,
                "operation": "compare" | "sum" | "average" | etc.,
                "group_by": "Year" | "Month" | "Business" | etc.
            }
        }
    """
    import re
    query = {}
    message_lower = message.lower()
    
    # CRITICAL: Extract intent (metric, operation, group_by) - as per ChatGPT recommendation
    intent = {
        "metric": None,
        "operation": None,
        "group_by": None
    }
    
    # Extract metric intent (CRITICAL - as per ChatGPT recommendation)
    if any(k in message_lower for k in [
        'gross sales', 'gross sale', 'total sales', 'sales value', 'revenue', 'gross revenue'
    ]):
        intent["metric"] = "Gross_Sales"  # MongoDB field name
        logger.info("📊 INTENT: Detected metric: gross_sales/revenue")
    elif any(k in message_lower for k in [
        'net sales', 'net revenue'
    ]):
        intent["metric"] = "Net_Sales"
        logger.info("📊 INTENT: Detected metric: net_sales")
    elif any(k in message_lower for k in [
        'volume', 'units sold', 'quantity', 'units', 'cases'
    ]):
        intent["metric"] = "Units"
        logger.info("📊 INTENT: Detected metric: units/volume")
    elif any(k in message_lower for k in [
        'profit', 'gross profit', 'margin'
    ]):
        intent["metric"] = "Gross_Profit"
        logger.info("📊 INTENT: Detected metric: gross_profit")
    else:
        # DEFAULT: Assume gross sales if not specified (as per user requirement)
        intent["metric"] = "Gross_Sales"
        logger.info("📊 INTENT: No metric specified, defaulting to gross_sales")
    
    # Extract operation intent (compare, sum, average, etc.)
    if any(k in message_lower for k in [
        'compare', 'comparison', 'vs', 'versus', 'against', 'compared to', 'compared with'
    ]):
        intent["operation"] = "compare"
        logger.info("📊 INTENT: Detected operation: compare")
        
        # Determine group_by for comparison
        if any(k in message_lower for k in ['across years', 'year over year', 'yoy', 'by year']):
            intent["group_by"] = "Year"
            logger.info("📊 INTENT: Detected group_by: Year")
        elif any(k in message_lower for k in ['by month', 'monthly', 'across months']):
            intent["group_by"] = "Month_Name"
            logger.info("📊 INTENT: Detected group_by: Month_Name")
        elif any(k in message_lower for k in ['by business', 'across businesses', 'businesses']):
            intent["group_by"] = "Business"
            logger.info("📊 INTENT: Detected group_by: Business")
        elif any(k in message_lower for k in ['by brand', 'across brands', 'brands']):
            intent["group_by"] = "Brand"
            logger.info("📊 INTENT: Detected group_by: Brand")
        else:
            # Default group_by for comparisons: Year (most common)
            intent["group_by"] = "Year"
            logger.info("📊 INTENT: Default group_by for comparison: Year")
    elif any(k in message_lower for k in [
        'sum', 'total', 'aggregate', 'combined'
    ]):
        intent["operation"] = "sum"
        logger.info("📊 INTENT: Detected operation: sum")
    elif any(k in message_lower for k in [
        'average', 'avg', 'mean'
    ]):
        intent["operation"] = "average"
        logger.info("📊 INTENT: Detected operation: average")
    else:
        # Default operation: sum (for totals)
        intent["operation"] = "sum"
        logger.info("📊 INTENT: Default operation: sum")
    
    # Get all available values from database for matching
    all_businesses = await db.business_data.distinct('Business')
    all_channels = await db.business_data.distinct('Channel')
    all_customers = await db.business_data.distinct('Customer')
    all_brands = await db.business_data.distinct('Brand')
    all_categories = await db.business_data.distinct('Category')
    
    # Extract years (e.g., "2023", "2023 and 2024", "2023, 2024, 2025")
    year_pattern = r'\b(20\d{2})\b'
    years = re.findall(year_pattern, message)
    if years:
        query['Year'] = {'$in': [int(y) for y in years if 2000 <= int(y) <= 2100]}
    
    # Extract months (e.g., "January", "jan", "Q1", "quarter 1")
    # CRITICAL FIX: Database stores abbreviated months (Jan, Feb, Mar), so convert full names to abbreviated
    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    # Map full names to abbreviated format (database format)
    month_to_abbr = {
        'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
        'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
        'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec'
    }
    found_months = []
    for i, month in enumerate(month_names):
        # Use word boundary to match whole words only (e.g., "november" not "novemberly")
        pattern = r'\b' + re.escape(month) + r'\b'
        if re.search(pattern, message_lower):
            # Convert to abbreviated format (database format)
            month_abbreviated = month_to_abbr.get(month, month.capitalize())
            if month_abbreviated not in found_months:
                found_months.append(month_abbreviated)
    for i, abbr in enumerate(month_abbr):
        # Use word boundary for abbreviations too
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, message_lower):
            # Map abbreviation to abbreviated format (capitalize first letter)
            month_abbreviated = abbr.capitalize()
            if month_abbreviated not in found_months:
                found_months.append(month_abbreviated)
    if found_months:
        query['Month_Name'] = {'$in': found_months}
        logger.info(f"📅 Extracted months from query builder: {found_months} (converted to abbreviated format)")
    
    # Extract quarters (Q1, Q2, Q3, Q4)
    # CRITICAL FIX: Database stores abbreviated months (Jan, Feb, Mar), not full names (January, February, March)
    # Terminal logs confirm: dashboard uses 'Jan', 'Feb', 'Mar' and finds data, but 'January', 'February', 'March' finds 0 documents
    quarter_pattern = r'\bq([1-4])\b'
    quarters = re.findall(quarter_pattern, message_lower)
    if quarters:
        # CRITICAL: Use abbreviated format to match database (confirmed from terminal logs)
        quarter_months = {
            '1': ['Jan', 'Feb', 'Mar'],
            '2': ['Apr', 'May', 'Jun'],
            '3': ['Jul', 'Aug', 'Sep'],
            '4': ['Oct', 'Nov', 'Dec']
        }
        q_months = []
        for q in quarters:
            q_months.extend(quarter_months.get(q, []))
        if q_months:
            if 'Month_Name' in query:
                # Intersect with existing months
                existing_months = query['Month_Name'].get('$in', [])
                query['Month_Name'] = {'$in': [m for m in existing_months if m in q_months] or q_months}
            else:
                query['Month_Name'] = {'$in': q_months}
            logger.info(f"📅 Q{quarters[0]} mapped to months: {q_months} (abbreviated format to match database)")
    
    # Skip business extraction if comparing businesses or asking for all businesses
    # Also check for "with other business in the group" which is a common phrasing
    is_comparing_business = (
        any(phrase in message_lower for phrase in [
            'compare business', 'compare businesses', 'business vs', 'businesses vs', 'business versus', 'businesses versus',
            'compare x with', 'compare x to', 'compare x against', 'x compared to', 'x compared with',
            'x vs other', 'x versus other', 'x against other', 'x and other businesses', 'x with other businesses',
            'with other businesses', 'versus other businesses', 'against other businesses', 'to other businesses',
            'with other business', 'versus other business', 'against other business', 'to other business',
            'compared to other', 'compared with other', 'in the group', 'with other business in the group',
            'with other businesses in the group', 'relative to other businesses', 'among other businesses', 
            'alongside other businesses', 'other business in the group', 'other businesses in the group'
        ]) and ('business' in message_lower or 'businesses' in message_lower)
    ) or 'with other business' in message_lower or 'with other businesses' in message_lower
    
    # Detect "all business" or "top X business" queries - these should show all businesses
    is_asking_for_all_businesses = (
        any(phrase in message_lower for phrase in [
            'all business', 'all businesses', 'every business', 'every businesses',
            'show all business', 'show all businesses', 'list all business', 'list all businesses',
            'all business in', 'all businesses in', 'all business data', 'all businesses data',
            'top business', 'top businesses', 'top 10 business', 'top 10 businesses', 'top 15 business', 'top 15 businesses',
            'top 5 business', 'top 5 businesses', 'top 20 business', 'top 20 businesses',
            'best business', 'best businesses', 'leading business', 'leading businesses',
            'top business by', 'top businesses by', 'rank business', 'rank businesses',
            'business ranking', 'businesses ranking', 'top performing business', 'top performing businesses'
        ]) or 
        re.search(r'top\s+\d+\s+business', message_lower) or 
        re.search(r'top\s+\d+\s+businesses', message_lower)
    )
    
    # Extract business (e.g., "business food", "for business food", "business: food")
    # But skip if comparing businesses or asking for all businesses (we want all businesses)
    if not is_comparing_business and not is_asking_for_all_businesses:
        business_patterns = [
            r'business\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category|across)',
            r'for\s+business\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category|across)',
            r'business:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category|across)',
            r'business\s+([a-zA-Z\s,&]+?)(?:\s+channel|\s+customer|\s+brand|\s+category|\s+across|$)',
            # Pattern for "Compare Q1 for business Food" - extract "Food"
            r'(?:for|of|in)\s+business\s+([a-zA-Z\s,&]+?)(?:\s+across|\s+years|\s+year|$)',
        ]
        for pattern in business_patterns:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                business_name = matches[0].strip()
                # Remove trailing words that might be part of next filter
                business_name = re.sub(r'\s+(channel|customer|brand|category|across|years|year).*$', '', business_name, flags=re.IGNORECASE).strip()
                # Try to match with database businesses using fuzzy matching
                matched = False
                best_match = None
                best_score = 0
                
                # First try exact/contains matching (fast)
                for db_business in all_businesses:
                    if db_business:
                        db_business_lower = str(db_business).lower()
                        business_name_lower = business_name.lower()
                        # Check if business name matches (exact or contains)
                        if business_name_lower == db_business_lower or business_name_lower in db_business_lower or db_business_lower in business_name_lower:
                            query = await apply_business_filter(query, str(db_business), db)
                            matched = True
                            logger.info(f"✅ Exact/Contains match: '{business_name}' -> '{db_business}'")
                            break
                
                # If no exact match, try fuzzy matching
                if not matched:
                    try:
                        from difflib import SequenceMatcher
                        business_name_lower = business_name.lower()
                        for db_business in all_businesses:
                            if db_business:
                                db_business_lower = str(db_business).lower()
                                # Calculate similarity ratio
                                similarity = SequenceMatcher(None, business_name_lower, db_business_lower).ratio()
                                # Also check if one contains the other (partial match)
                                if business_name_lower in db_business_lower or db_business_lower in business_name_lower:
                                    similarity = max(similarity, 0.7)  # Boost partial matches
                                
                                if similarity > best_score:
                                    best_score = similarity
                                    best_match = db_business
                        
                        # Use fuzzy match if similarity is above threshold (60%)
                        if best_match and best_score >= 0.6:
                            query = await apply_business_filter(query, str(best_match), db)
                            matched = True
                            logger.info(f"✅ Fuzzy match: '{business_name}' -> '{best_match}' (similarity: {best_score:.2f})")
                    except ImportError:
                        logger.warning("⚠️ difflib not available, skipping fuzzy matching")
                
                if matched:
                    break
    else:
        logger.info("ℹ️ Skipping business extraction - user is comparing businesses, not filtering BY business")
    
    # Extract channel (e.g., "channel Convenience", "channel: Convenience", "Food and grocery channel", "Food and channel grocery")
    # CRITICAL: Support patterns like "and grocery channel" AND "and channel grocery" (similar to brand extraction)
    channel_patterns = [
        r'channel\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|customer|brand|category)',
        r'channel:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|customer|brand|category)',
        # CRITICAL: Match "and X channel" pattern (e.g., "Food and grocery channel")
        r'and\s+([a-z][a-zA-Z\s]+?)\s+channel(?:\s|$|,|\.|\?|in|for|across)',
        # CRITICAL: Match "and channel X" pattern (e.g., "Food and channel grocery")
        r'and\s+channel\s+([a-z][a-zA-Z\s]+?)(?:\s|$|,|\.|\?|in|for|across)',
        # Match "X channel" after business name (e.g., "business Food and grocery channel")
        r'(?:business|for|of)\s+[^,]+\s+and\s+([a-z][a-zA-Z\s]+?)\s+channel',
        # Match "channel X" after business name (e.g., "business Food and channel grocery")
        r'(?:business|for|of)\s+[^,]+\s+and\s+channel\s+([a-z][a-zA-Z\s]+?)(?:\s|$|,|\.|\?|in|for|across)',
    ]
    for pattern in channel_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        if matches:
            channel_name = matches[0].strip()
            # Remove trailing words that might be part of next filter
            channel_name = re.sub(r'\s+(customer|brand|category|in|for|across).*$', '', channel_name, flags=re.IGNORECASE).strip()
            # Skip if it's a common phrase
            if channel_name.lower() in ['and', 'or', 'the', 'a', 'an']:
                continue
            # Try exact/contains matching first
            matched = False
            for db_channel in all_channels:
                if db_channel:
                    db_channel_lower = str(db_channel).lower()
                    channel_name_lower = channel_name.lower()
                    if channel_name_lower == db_channel_lower or channel_name_lower in db_channel_lower or db_channel_lower in channel_name_lower:
                        if 'Channel' in query:
                            if isinstance(query['Channel'], dict) and '$in' in query['Channel']:
                                if str(db_channel) not in query['Channel']['$in']:
                                    query['Channel']['$in'].append(str(db_channel))
                            else:
                                query['Channel'] = {'$in': [str(db_channel)]}
                        else:
                            query['Channel'] = {'$in': [str(db_channel)]}
                        logger.info(f"✅ Matched channel: '{channel_name}' -> '{db_channel}'")
                        matched = True
                        break
            if matched:
                break
            # If no exact match, try fuzzy matching
            if not matched:
                try:
                    from difflib import SequenceMatcher
                    channel_name_lower = channel_name.lower()
                    best_match = None
                    best_score = 0
                    for db_channel in all_channels:
                        if db_channel:
                            db_channel_lower = str(db_channel).lower()
                            similarity = SequenceMatcher(None, channel_name_lower, db_channel_lower).ratio()
                            if channel_name_lower in db_channel_lower or db_channel_lower in channel_name_lower:
                                similarity = max(similarity, 0.7)  # Boost partial matches
                            if similarity > best_score:
                                best_score = similarity
                                best_match = db_channel
                    if best_match and best_score >= 0.6:
                        if 'Channel' in query:
                            if isinstance(query['Channel'], dict) and '$in' in query['Channel']:
                                if str(best_match) not in query['Channel']['$in']:
                                    query['Channel']['$in'].append(str(best_match))
                            else:
                                query['Channel'] = {'$in': [str(best_match)]}
                        else:
                            query['Channel'] = {'$in': [str(best_match)]}
                        logger.info(f"✅ Fuzzy matched channel: '{channel_name}' -> '{best_match}' (similarity: {best_score:.2f})")
                        matched = True
                except ImportError:
                    logger.warning("⚠️ difflib not available, skipping fuzzy matching for channels")
            if matched:
                break
    
    # Extract customer (e.g., "customer bwg", "customer: bwg")
    customer_patterns = [
        r'customer\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|brand|category)',
        r'customer:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|brand|category)',
    ]
    for pattern in customer_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        if matches:
            customer_name = matches[0].strip()
            # Remove trailing words that might be part of next filter
            customer_name = re.sub(r'\s+(brand|category).*$', '', customer_name, flags=re.IGNORECASE).strip()
            for db_customer in all_customers:
                if db_customer:
                    db_customer_lower = str(db_customer).lower()
                    customer_name_lower = customer_name.lower()
                    if customer_name_lower == db_customer_lower or customer_name_lower in db_customer_lower or db_customer_lower in customer_name_lower:
                        if 'Customer' in query:
                            if isinstance(query['Customer'], dict) and '$in' in query['Customer']:
                                if str(db_customer) not in query['Customer']['$in']:
                                    query['Customer']['$in'].append(str(db_customer))
                            else:
                                query['Customer'] = {'$in': [str(db_customer)]}
                        else:
                            query['Customer'] = {'$in': [str(db_customer)]}
                        logger.info(f"✅ Matched customer: '{customer_name}' -> '{db_customer}'")
                        break
            break
    
    # Extract brand (e.g., "brand bensons", "brand: bensons", "brands Bonne Maman", "Food and KOKA brand")
    # CRITICAL FIX: Don't match "brands by Revenue" or "top brands" - these are asking FOR brands, not filtering BY brand
    # BUT: Match patterns like "Food and KOKA brand" where user is filtering BY a specific brand
    brand_patterns = [
        r'brands?\s+(?:is|are|of|for|by|top|all|the)\s+',  # Skip patterns like "brands by Revenue", "top brands", etc.
        r'brands?\s+([a-zA-Z][^,\.\?]+?)(?:\s+(?:and|or|,)\s+[a-zA-Z]|\s*$|\s*[,\?\.]|\s+category|\s+customer|\s+channel)',  # Match actual brand names
        r'brands?:\s*([a-zA-Z][^,\.\?]+?)(?:\s+(?:and|or|,)\s+[a-zA-Z]|\s*$|\s*[,\?\.]|\s+category|\s+customer|\s+channel)',
        # CRITICAL: Match "and X brand" pattern (e.g., "Food and KOKA brand")
        r'and\s+([A-Z][a-zA-Z\s]+?)\s+brand(?:\s|$|,|\.|\?|in|for|across)',
        # Match "X brand" after business name (e.g., "business Food and KOKA brand")
        r'(?:business|for|of)\s+[^,]+\s+and\s+([A-Z][a-zA-Z\s]+?)\s+brand',
    ]
    
    # Skip brand extraction if the message is asking FOR brands (not filtering BY brand)
    # Also skip if comparing brands - we want to show all brands for comparison
    is_asking_for_brands = (
        any(phrase in message_lower for phrase in [
            'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands', 'top 20 brands',
            'brands by revenue', 'brands by profit', 'brands by', 'all brands',
            'list brands', 'show brands', 'which brands', 'what brands',
            'tell me about brands', 'tell me about brand', 'show me brands', 'show me brand',
            'show me the top', 'tell me about all brands', 'brand performance', 'brand rankings',
            'brand revenue', 'brand profit', 'compare brand', 'compare brands'
        ]) or 
        re.search(r'top\s+\d+\s+brand', message_lower) or
        re.search(r'show\s+me\s+(the\s+)?top\s+\d+\s+brand', message_lower) or
        re.search(r'tell\s+me\s+about\s+(all\s+)?brand', message_lower)
    )
    
    is_comparing_brand = any(phrase in message_lower for phrase in [
        'compare brand', 'compare brands', 'brand vs', 'brands vs', 'brand versus', 'brands versus',
        'compare x with', 'compare x to', 'compare x against', 'x compared to', 'x compared with',
        'x vs other', 'x versus other', 'x against other', 'x and other brands', 'x with other brands',
        'compared to other', 'compared with other', 'vs other brands', 'versus other brands',
        'with other brands', 'against other brands', 'to other brands', 'relative to other brands'
    ]) and ('brand' in message_lower or 'brands' in message_lower)
    
    if not is_asking_for_brands and not is_comparing_brand:
        for pattern in brand_patterns[1:]:  # Skip the first pattern (negative match)
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                brand_name = matches[0].strip()
                # Remove trailing words that might be part of next filter
                brand_name = re.sub(r'\s+(and|or|category|customer|channel).*$', '', brand_name, flags=re.IGNORECASE).strip()
                # Skip if it's a common phrase like "by revenue", "by profit", etc.
                if brand_name.lower() in ['by revenue', 'by profit', 'by', 'revenue', 'profit', 'top', 'all']:
                    continue
                for db_brand in all_brands:
                    if db_brand:
                        db_brand_lower = str(db_brand).lower()
                        brand_name_lower = brand_name.lower()
                        if brand_name_lower == db_brand_lower or brand_name_lower in db_brand_lower or db_brand_lower in brand_name_lower:
                            if 'Brand' in query:
                                if isinstance(query['Brand'], dict) and '$in' in query['Brand']:
                                    if str(db_brand) not in query['Brand']['$in']:
                                        query['Brand']['$in'].append(str(db_brand))
                                else:
                                    query['Brand'] = {'$in': [str(db_brand)]}
                            else:
                                query['Brand'] = {'$in': [str(db_brand)]}
                            logger.info(f"✅ Matched brand: '{brand_name}' -> '{db_brand}'")
                            break
                break
    else:
        logger.info("ℹ️ Skipping brand extraction - user is asking FOR brands, not filtering BY brand")
    
    # Extract category (e.g., "category curry", "category: curry")
    category_patterns = [
        r'category\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|and|on|for|basis)',
        r'category:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|and|on|for|basis)',
    ]
    for pattern in category_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        if matches:
            category_name = matches[0].strip()
            # Remove trailing words that might be part of next filter
            category_name = re.sub(r'\s+(and|on|for|basis).*$', '', category_name, flags=re.IGNORECASE).strip()
            for db_category in all_categories:
                if db_category:
                    db_category_lower = str(db_category).lower()
                    category_name_lower = category_name.lower()
                    if category_name_lower == db_category_lower or category_name_lower in db_category_lower or db_category_lower in category_name_lower:
                        if 'Category' in query:
                            if isinstance(query['Category'], dict) and '$in' in query['Category']:
                                if str(db_category) not in query['Category']['$in']:
                                    query['Category']['$in'].append(str(db_category))
                            else:
                                query['Category'] = {'$in': [str(db_category)]}
                        else:
                            query['Category'] = {'$in': [str(db_category)]}
                        logger.info(f"✅ Matched category: '{category_name}' -> '{db_category}'")
                        break
            break
    
    logger.info(f"🔍 Parsed query from natural language: {query}")
    logger.info(f"📊 Query intent: {intent}")
    
    # Return structured output with both filters and intent (as per ChatGPT recommendation)
    return {
        "filters": query,
        "intent": intent
    }

