"""
MongoDB-based Customer Insights Implementation with Caching
This module provides MongoDB aggregation pipelines for customer insights data
"""
import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache for MongoDB query results
_mongodb_cache = {}

def get_cache_key(years: Optional[str] = None, months: Optional[str] = None) -> str:
    """Generate cache key from filter parameters"""
    key_parts = []
    if years:
        key_parts.append(f"year:{years}")
    if months:
        key_parts.append(f"month:{months}")
    return ":".join(key_parts) if key_parts else "all"

def get_month_numbers(months: str) -> List[int]:
    """Convert month names to month numbers"""
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12,
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
        'Oct': 10, 'Nov': 11, 'Dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
    }
    month_list = [m.strip() for m in months.split(',') if m.strip()]
    month_numbers = []
    for m in month_list:
        if m in month_map:
            month_numbers.append(month_map[m])
        else:
            m_lower = m.lower()
            for key, value in month_map.items():
                if key.lower() == m_lower:
                    month_numbers.append(value)
                    break
    return sorted(list(set(month_numbers)))

async def get_customer_insights_mongodb(
    db: AsyncIOMotorDatabase,
    years: Optional[str] = None,
    months: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Get customer insights data from MongoDB with caching.
    Returns the same structure as the CSV-based implementation.
    """
    cache_key = get_cache_key(years, months)
    
    # Check cache
    if use_cache and cache_key in _mongodb_cache:
        logger.info(f"📊 Using MongoDB cache (key: {cache_key})")
        return _mongodb_cache[cache_key]
    
    logger.info(f"📊 Querying MongoDB (key: {cache_key})")
    start_time = pd.Timestamp.now()
    
    # Build match query
    match_query = {}
    
    if years:
        year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
        if year_list:
            match_query['Year'] = {'$in': year_list}
    
    if months:
        month_numbers = get_month_numbers(months)
        if month_numbers:
            match_query['Month'] = {'$in': month_numbers}
    
    # Ensure Year and Month are valid numbers for all queries
    base_match = match_query.copy() if match_query else {}
    
    # 1. Summary aggregation
    summary_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': None,
            'totalCustomers': {'$addToSet': '$Customer email'},
            'totalOrders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'totalSales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'newCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'New']}, 1, 0]}},
            'returningCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'Returning']}, 1, 0]}}
        }},
        {'$project': {
            'totalCustomers': {'$size': '$totalCustomers'},
            'totalOrders': 1,
            'totalSales': 1,
            'newCustomers': 1,
            'returningCustomers': 1,
            'avgOrderValue': {'$cond': [
                {'$gt': ['$totalOrders', 0]},
                {'$divide': ['$totalSales', '$totalOrders']},
                0
            ]}
        }}
    ]
    
    summary_result = await db.shopify_data.aggregate(summary_pipeline).to_list(1)
    summary = summary_result[0] if summary_result else {
        'totalCustomers': 0,
        'totalOrders': 0,
        'totalSales': 0,
        'avgOrderValue': 0,
        'newCustomers': 0,
        'returningCustomers': 0
    }
    
    # 2. New vs Returning customers
    new_vs_returning_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$New or returning customer',
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'unique_customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'type': '$_id',
            'orders': 1,
            'sales': 1,
            'unique_customers': {'$size': '$unique_customers'}
        }}
    ]
    new_vs_returning = await db.shopify_data.aggregate(new_vs_returning_pipeline).to_list(10)
    
    # 3. Channel Performance (Order or return)
    channel_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Order or return',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'channel': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}}
    ]
    channel_perf = await db.shopify_data.aggregate(channel_pipeline).to_list(10)
    
    # 4. Region Performance
    region_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Shipping region',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'region': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}},
        {'$limit': 10}
    ]
    region_perf = await db.shopify_data.aggregate(region_pipeline).to_list(10)
    
    # 5. Traffic Source
    traffic_source_pipeline = [
        {'$match': {**base_match, 'Referring channel': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': '$Referring channel',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'source': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}},
        {'$limit': 10}
    ]
    traffic_source = await db.shopify_data.aggregate(traffic_source_pipeline).to_list(10)
    
    # 6. Customer Lifetime Value (by order buckets)
    # Use $facet to group by buckets
    clv_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Customer email',
            'customer_orders': {'$max': {'$toDouble': {'$ifNull': ['$Customer number of orders', 0]}}},
            'total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'total_orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
        }},
        {'$project': {
            'customer_orders': 1,
            'total_sales': 1,
            'total_orders': 1,
            'bucket': {
                '$switch': {
                    'branches': [
                        {'case': {'$lte': ['$customer_orders', 1]}, 'then': '1'},
                        {'case': {'$lte': ['$customer_orders', 3]}, 'then': '2-3'},
                        {'case': {'$lte': ['$customer_orders', 5]}, 'then': '4-5'},
                        {'case': {'$lte': ['$customer_orders', 10]}, 'then': '6-10'},
                        {'case': {'$lte': ['$customer_orders', 20]}, 'then': '11-20'},
                        {'case': True, 'then': '20+'}
                    ],
                    'default': '1'
                }
            }
        }},
        {'$group': {
            '_id': '$bucket',
            'total_sales': {'$sum': '$total_sales'},
            'unique_customers': {'$addToSet': '$_id'},
            'total_orders': {'$sum': '$total_orders'}
        }},
        {'$project': {
            'order_bucket': '$_id',
            'total_sales': 1,
            'unique_customers': {'$size': '$unique_customers'},
            'total_orders': 1,
            'avg_sales_per_customer': {
                '$cond': [
                    {'$gt': [{'$size': '$unique_customers'}, 0]},
                    {'$divide': ['$total_sales', {'$size': '$unique_customers'}]},
                    0
                ]
            }
        }}
    ]
    clv_analysis = await db.shopify_data.aggregate(clv_pipeline).to_list(10)
    
    # 7. Monthly Trend
    monthly_match = base_match.copy()
    monthly_match['Year'] = {'$ne': None, '$exists': True, '$type': 'number'}
    monthly_match['Month'] = {'$ne': None, '$exists': True, '$type': 'number'}
    
    monthly_pipeline = [
        {'$match': monthly_match},
        {'$group': {
            '_id': {'Year': '$Year', 'Month': '$Month'},
            'Total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'Orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'Customer_email': {'$addToSet': '$Customer email'},
            'Orders_first_time': {'$sum': {'$toDouble': {'$ifNull': ['$Orders (first-time)', 0]}}},
            'Orders_returning': {'$sum': {'$toDouble': {'$ifNull': ['$Orders (returning)', 0]}}}
        }},
        {'$project': {
            'Year': '$_id.Year',
            'Month': '$_id.Month',
            'Total_sales': 1,
            'Orders': 1,
            'Customer_email': {'$size': '$Customer_email'},
            'Orders_first_time': 1,
            'Orders_returning': 1
        }},
        {'$sort': {'Year': 1, 'Month': 1}}
    ]
    monthly_results = await db.shopify_data.aggregate(monthly_pipeline).to_list(1000)
    
    # Format monthly trend with month names
    monthly_trend = []
    for item in monthly_results:
        year = int(item.get('Year', 0))
        month = int(item.get('Month', 0))
        if year and month:
            try:
                month_name = pd.to_datetime(f"{year}-{month}-01").strftime('%B')
                monthly_trend.append({
                    'Year': year,
                    'Month': month,
                    'MonthName': month_name,
                    'month_label': f"{month_name} {year}",
                    'Total_sales': float(item.get('Total_sales', 0)),
                    'Orders': float(item.get('Orders', 0)),
                    'Customer_email': int(item.get('Customer_email', 0)),
                    'Orders_first_time': float(item.get('Orders_first_time', 0)),
                    'Orders_returning': float(item.get('Orders_returning', 0))
                })
            except Exception as e:
                logger.warning(f"Error formatting monthly trend item: {str(e)}")
    
    # 8. Subscription Status
    subscription_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Customer email subscription status',
            'unique_customers': {'$addToSet': '$Customer email'},
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
        }},
        {'$project': {
            'status': '$_id',
            'unique_customers': {'$size': '$unique_customers'},
            'sales': 1,
            'orders': 1
        }}
    ]
    subscription_status = await db.shopify_data.aggregate(subscription_pipeline).to_list(10)
    
    # 9. Top Customers
    top_customers_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': {'email': '$Customer email', 'name': '$Customer name'},
            'total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'total_orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'lifetime_orders': {'$max': {'$toDouble': {'$ifNull': ['$Customer number of orders', 0]}}}
        }},
        {'$project': {
            'email': '$_id.email',
            'name': '$_id.name',
            'total_sales': 1,
            'total_orders': 1,
            'lifetime_orders': 1
        }},
        {'$sort': {'total_sales': -1}},
        {'$limit': 20}
    ]
    top_customers = await db.shopify_data.aggregate(top_customers_pipeline).to_list(20)
    
    # 10. Platform Analysis
    platform_pipeline = [
        {'$match': {**base_match, 'Referring platform': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': '$Referring platform',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'platform': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}},
        {'$limit': 10}
    ]
    platform_analysis = await db.shopify_data.aggregate(platform_pipeline).to_list(10)
    
    # 11. Traffic Type (normalize case to prevent duplicates like "Unknown" vs "unknown")
    # First, get all traffic types and normalize them
    traffic_type_pipeline = [
        {'$match': {**base_match, 'Traffic type': {'$ne': None, '$exists': True}}},
        {'$addFields': {
            'traffic_type_lower': {'$toLower': {'$ifNull': ['$Traffic type', '']}},
            'traffic_type_original': {'$ifNull': ['$Traffic type', '']}
        }},
        {'$addFields': {
            'normalized_traffic_type': {
                '$cond': {
                    'if': {
                        '$or': [
                            {'$eq': ['$traffic_type_lower', 'unknown']},
                            {'$eq': ['$traffic_type_original', '']},
                            {'$eq': ['$traffic_type_original', None]}
                        ]
                    },
                    'then': 'Unknown',  # Standardize to "Unknown" with capital U
                    'else': {
                        '$concat': [
                            {'$toUpper': {'$substr': ['$traffic_type_original', 0, 1]}},  # First letter uppercase
                            {'$toLower': {'$substr': ['$traffic_type_original', 1, {'$strLenCP': '$traffic_type_original'}]}}  # Rest lowercase
                        ]
                    }
                }
            }
        }},
        {'$group': {
            '_id': '$normalized_traffic_type',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'type': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}}
    ]
    traffic_type = await db.shopify_data.aggregate(traffic_type_pipeline).to_list(100)
    
    # 12. Hourly Patterns
    hourly_pipeline = [
        {'$match': {**base_match, 'Hour of day': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': {'$toInt': {'$ifNull': ['$Hour of day', 0]}},
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'hour': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'hour': 1}}
    ]
    hourly_patterns = await db.shopify_data.aggregate(hourly_pipeline).to_list(24)
    
    # 13. Country Distribution
    country_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Shipping country',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'country': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}}
    ]
    country_dist = await db.shopify_data.aggregate(country_pipeline).to_list(100)
    
    # 14. SMS Subscription
    sms_pipeline = [
        {'$match': {**base_match, 'Customer SMS subscription status': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': '$Customer SMS subscription status',
            'unique_customers': {'$addToSet': '$Customer email'},
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
        }},
        {'$project': {
            'status': '$_id',
            'unique_customers': {'$size': '$unique_customers'},
            'sales': 1,
            'orders': 1
        }}
    ]
    sms_subscription = await db.shopify_data.aggregate(sms_pipeline).to_list(10)
    
    # 15. Order Return Analysis
    order_return_pipeline = [
        {'$match': base_match},
        {'$group': {
            '_id': '$Order or return',
            'total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'net_returns': {'$sum': {'$toDouble': {'$ifNull': ['$Net returns', 0]}}},
            'total_returns': {'$sum': {'$toDouble': {'$ifNull': ['$Total returns', 0]}}}
        }},
        {'$project': {
            'type': '$_id',
            'total_sales': 1,
            'orders': 1,
            'net_returns': 1,
            'total_returns': 1
        }}
    ]
    order_return_analysis = await db.shopify_data.aggregate(order_return_pipeline).to_list(10)
    
    # 16. Medium Analysis
    medium_pipeline = [
        {'$match': {**base_match, 'Referring medium': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': '$Referring medium',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'medium': '$_id',
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'sales': -1}}
    ]
    medium_analysis = await db.shopify_data.aggregate(medium_pipeline).to_list(100)
    
    # 17. Top Products
    top_products_pipeline = [
        {'$match': {**base_match, 'Product variant SKU': {'$ne': None, '$exists': True}}},
        {'$group': {
            '_id': '$Product variant SKU',
            'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
            'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
            'quantity': {'$sum': {'$toDouble': {'$ifNull': ['$Quantity ordered', 0]}}}
        }},
        {'$project': {
            'sku': '$_id',
            'sales': 1,
            'orders': 1,
            'quantity': 1
        }},
        {'$sort': {'sales': -1}},
        {'$limit': 15}
    ]
    top_products = await db.shopify_data.aggregate(top_products_pipeline).to_list(15)
    
    # 18. Day of Week Analysis (handles both date and string date fields)
    day_of_week_pipeline = [
        {'$match': {**base_match, 'Day': {'$ne': None, '$exists': True}}},
        {'$project': {
            # Convert Day to date if it's a string, otherwise use as-is
            'dayDate': {
                '$cond': {
                    'if': {'$eq': [{'$type': '$Day'}, 'string']},
                    'then': {'$dateFromString': {'dateString': '$Day', 'onError': None}},
                    'else': '$Day'
                }
            },
            'Total sales': {'$toDouble': {'$ifNull': ['$Total sales', 0]}},
            'Orders': {'$toDouble': {'$ifNull': ['$Orders', 0]}},
            'Customer email': 1
        }},
        {'$match': {'dayDate': {'$ne': None, '$type': 'date'}}},
        {'$project': {
            'dayOfWeek': {'$dayOfWeek': '$dayDate'},
            'Total sales': 1,
            'Orders': 1,
            'Customer email': 1
        }},
        {'$group': {
            '_id': '$dayOfWeek',
            'sales': {'$sum': '$Total sales'},
            'orders': {'$sum': '$Orders'},
            'customers': {'$addToSet': '$Customer email'}
        }},
        {'$project': {
            'dayOfWeek': '$_id',
            'day': {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$_id', 1]}, 'then': 'Sunday'},
                        {'case': {'$eq': ['$_id', 2]}, 'then': 'Monday'},
                        {'case': {'$eq': ['$_id', 3]}, 'then': 'Tuesday'},
                        {'case': {'$eq': ['$_id', 4]}, 'then': 'Wednesday'},
                        {'case': {'$eq': ['$_id', 5]}, 'then': 'Thursday'},
                        {'case': {'$eq': ['$_id', 6]}, 'then': 'Friday'},
                        {'case': {'$eq': ['$_id', 7]}, 'then': 'Saturday'}
                    ],
                    'default': 'Unknown'
                }
            },
            'day_order': {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$_id', 2]}, 'then': 1},  # Monday
                        {'case': {'$eq': ['$_id', 3]}, 'then': 2},  # Tuesday
                        {'case': {'$eq': ['$_id', 4]}, 'then': 3},  # Wednesday
                        {'case': {'$eq': ['$_id', 5]}, 'then': 4},  # Thursday
                        {'case': {'$eq': ['$_id', 6]}, 'then': 5},  # Friday
                        {'case': {'$eq': ['$_id', 7]}, 'then': 6},  # Saturday
                        {'case': {'$eq': ['$_id', 1]}, 'then': 7}   # Sunday
                    ],
                    'default': 8
                }
            },
            'sales': 1,
            'orders': 1,
            'customers': {'$size': '$customers'}
        }},
        {'$sort': {'day_order': 1}},
        {'$project': {
            'day': 1,
            'sales': 1,
            'orders': 1,
            'customers': 1
        }}
    ]
    day_of_week = await db.shopify_data.aggregate(day_of_week_pipeline).to_list(7)
    
    # 19. Return Trend (monthly)
    return_trend_match = {**monthly_match, 'Order or return': 'return'}
    return_trend_pipeline = [
        {'$match': return_trend_match},
        {'$group': {
            '_id': {'Year': '$Year', 'Month': '$Month'},
            'Total returns': {'$sum': {'$abs': {'$toDouble': {'$ifNull': ['$Total returns', 0]}}}},
            'Orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
        }},
        {'$project': {
            'Year': '$_id.Year',
            'Month': '$_id.Month',
            'Total returns': 1,
            'Orders': 1
        }},
        {'$sort': {'Year': 1, 'Month': 1}}
    ]
    return_trend_results = await db.shopify_data.aggregate(return_trend_pipeline).to_list(100)
    
    # Get monthly sales for return rate calculation
    monthly_sales_pipeline = [
        {'$match': monthly_match},
        {'$group': {
            '_id': {'Year': '$Year', 'Month': '$Month'},
            'Total sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}}
        }},
        {'$project': {
            'Year': '$_id.Year',
            'Month': '$_id.Month',
            'Total sales': 1
        }}
    ]
    monthly_sales_results = await db.shopify_data.aggregate(monthly_sales_pipeline).to_list(100)
    monthly_sales_dict = {(r['Year'], r['Month']): r['Total sales'] for r in monthly_sales_results}
    
    # Format return trend
    return_trend = []
    for item in return_trend_results:
        year = int(item.get('Year', 0))
        month = int(item.get('Month', 0))
        if year and month:
            try:
                month_name = pd.to_datetime(f"{year}-{month}-01").strftime('%B')
                total_sales = monthly_sales_dict.get((year, month), 0)
                total_returns = abs(float(item.get('Total returns', 0)))
                return_rate = (total_returns / total_sales * 100) if total_sales > 0 else 0
                return_trend.append({
                    'Year': year,
                    'Month': month,
                    'MonthName': month_name,
                    'month_label': f"{month_name} {year}",
                    'Total returns': total_returns,
                    'Orders': float(item.get('Orders', 0)),
                    'return_rate': return_rate
                })
            except Exception as e:
                logger.warning(f"Error formatting return trend item: {str(e)}")
    
    # Build response
    response = {
        "newVsReturning": [dict(item) for item in new_vs_returning],
        "channelPerformance": [dict(item) for item in channel_perf],
        "regionPerformance": [dict(item) for item in region_perf],
        "trafficSource": [dict(item) for item in traffic_source],
        "customerLifetimeValue": [dict(item) for item in clv_analysis],
        "monthlyTrend": monthly_trend,
        "subscriptionStatus": [dict(item) for item in subscription_status],
        "topCustomers": [dict(item) for item in top_customers],
        "platformAnalysis": [dict(item) for item in platform_analysis],
        "trafficType": [dict(item) for item in traffic_type],
        "hourlyPatterns": [dict(item) for item in hourly_patterns],
        "countryDistribution": [dict(item) for item in country_dist],
        "smsSubscription": [dict(item) for item in sms_subscription],
        "orderReturnAnalysis": [dict(item) for item in order_return_analysis],
        "mediumAnalysis": [dict(item) for item in medium_analysis],
        "topProducts": [dict(item) for item in top_products],
        "dayOfWeekAnalysis": [dict(item) for item in day_of_week],
        "returnTrend": return_trend,
        "summary": {
            "totalCustomers": int(summary.get('totalCustomers', 0)),
            "totalOrders": int(summary.get('totalOrders', 0)),
            "totalSales": float(summary.get('totalSales', 0)),
            "avgOrderValue": float(summary.get('avgOrderValue', 0)),
            "newCustomers": int(summary.get('newCustomers', 0)),
            "returningCustomers": int(summary.get('returningCustomers', 0))
        }
    }
    
    # Cache the result
    if use_cache:
        _mongodb_cache[cache_key] = response
        logger.info(f"📊 MongoDB query completed in {(pd.Timestamp.now() - start_time).total_seconds():.3f}s, cached (key: {cache_key})")
    else:
        logger.info(f"📊 MongoDB query completed in {(pd.Timestamp.now() - start_time).total_seconds():.3f}s")
    
    return response

