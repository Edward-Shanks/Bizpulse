"""
Query builder utilities for MongoDB
Handles filter parsing and query construction
"""
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.helpers import parse_list
import logging

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
            normalized_categories = [normalize_category_name(cat) for cat in category_list]
            # Use case-insensitive regex matching
            category_regex_list = []
            for cat in normalized_categories:
                category_regex_list.append({'$regex': f'^{cat}$', '$options': 'i'})
            query['Category'] = {'$in': category_regex_list}
    
    if customers:
        customer_list = parse_list(customers)
        if customer_list:
            query['Customer'] = {'$in': customer_list}
    
    if sub_categories:
        subcategory_list = parse_list(sub_categories)
        if subcategory_list:
            # Handle both Sub_Cat (normalized) and Sub_Category (legacy)
            query['$or'] = [
                {'Sub_Cat': {'$in': subcategory_list}},
                {'Sub_Category': {'$in': subcategory_list}},
            ]
    
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
    """
    import re
    query = {}
    message_lower = message.lower()
    
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
    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    found_months = []
    for i, month in enumerate(month_names):
        if month in message_lower:
            found_months.append(month_names[i].capitalize())
    for i, abbr in enumerate(month_abbr):
        if f' {abbr} ' in message_lower or message_lower.startswith(abbr) or message_lower.endswith(abbr):
            found_months.append(month_names[i].capitalize())
    if found_months:
        query['Month_Name'] = {'$in': found_months}
    
    # Extract quarters (Q1, Q2, Q3, Q4)
    quarter_pattern = r'\bq([1-4])\b'
    quarters = re.findall(quarter_pattern, message_lower)
    if quarters:
        quarter_months = {
            '1': ['January', 'February', 'March'],
            '2': ['April', 'May', 'June'],
            '3': ['July', 'August', 'September'],
            '4': ['October', 'November', 'December']
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
    
    # Extract business (e.g., "business food", "for business food", "business: food")
    business_patterns = [
        r'business\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category)',
        r'for\s+business\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category)',
        r'business:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|channel|customer|brand|category)',
        r'business\s+([a-zA-Z\s,&]+?)(?:\s+channel|\s+customer|\s+brand|\s+category|$)',
    ]
    for pattern in business_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        if matches:
            business_name = matches[0].strip()
            # Remove trailing words that might be part of next filter
            business_name = re.sub(r'\s+(channel|customer|brand|category).*$', '', business_name, flags=re.IGNORECASE).strip()
            # Try to match with database businesses
            matched = False
            for db_business in all_businesses:
                if db_business:
                    db_business_lower = str(db_business).lower()
                    business_name_lower = business_name.lower()
                    # Check if business name matches (exact or contains)
                    if business_name_lower == db_business_lower or business_name_lower in db_business_lower or db_business_lower in business_name_lower:
                        query = await apply_business_filter(query, str(db_business), db)
                        matched = True
                        logger.info(f"✅ Matched business: '{business_name}' -> '{db_business}'")
                        break
            if matched:
                break
    
    # Extract channel (e.g., "channel Convenience", "channel: Convenience")
    channel_patterns = [
        r'channel\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|customer|brand|category)',
        r'channel:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|customer|brand|category)',
    ]
    for pattern in channel_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        if matches:
            channel_name = matches[0].strip()
            # Remove trailing words that might be part of next filter
            channel_name = re.sub(r'\s+(customer|brand|category).*$', '', channel_name, flags=re.IGNORECASE).strip()
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
                        break
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
    
    # Extract brand (e.g., "brand bensons", "brand: bensons", "brands Bonne Maman")
    # CRITICAL FIX: Don't match "brands by Revenue" or "top brands" - these are asking FOR brands, not filtering BY brand
    brand_patterns = [
        r'brands?\s+(?:is|are|of|for|by|top|all|the)\s+',  # Skip patterns like "brands by Revenue", "top brands", etc.
        r'brands?\s+([a-zA-Z][^,\.\?]+?)(?:\s+(?:and|or|,)\s+[a-zA-Z]|\s*$|\s*[,\?\.]|\s+category|\s+customer|\s+channel)',  # Match actual brand names
        r'brands?:\s*([a-zA-Z][^,\.\?]+?)(?:\s+(?:and|or|,)\s+[a-zA-Z]|\s*$|\s*[,\?\.]|\s+category|\s+customer|\s+channel)',
    ]
    
    # Skip brand extraction if the message is asking FOR brands (not filtering BY brand)
    is_asking_for_brands = any(phrase in message_lower for phrase in [
        'top brands', 'top 15 brands', 'top 10 brands', 'top 5 brands',
        'brands by revenue', 'brands by profit', 'brands by', 'all brands',
        'list brands', 'show brands', 'which brands', 'what brands'
    ])
    
    if not is_asking_for_brands:
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
    return query

