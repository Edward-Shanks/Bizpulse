# Customer Deep Intelligence - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Customer Deep Intelligence screen. Use this document to verify values against the CSV/Shopify data file.

---

## Data Source
**Collection**: `shopify_data` (MongoDB)  
**CSV File**: Shopify customer data export

---

## Filtering
All calculations respect the following filters:
- **Year Filter**: Filters by `Year` column (numeric)
- **Month Filter**: Filters by `Month` column (numeric: 1-12)

**Filter Application**: All aggregations use `base_match` which includes these filters.

---

## 1. Key Performance Indicators (KPIs) - Top Row

### 1.1 Total Customers
**Display**: Large number card (e.g., "5.6k")

**Formula**:
```
Total Customers = COUNT(DISTINCT Customer email)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'totalCustomers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'totalCustomers': {'$size': '$totalCustomers'}
  }
}
```

**CSV Verification**:
- Column: `Customer email`
- Action: Count unique email addresses
- Filter: Apply Year/Month filters if selected

**Notes**:
- Uses `$addToSet` to get unique customers
- `$size` counts the unique set

---

### 1.2 Total Orders
**Display**: Large number card (e.g., "16.9k")

**Formula**:
```
Total Orders = SUM(Orders)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'totalOrders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
  }
}
```

**CSV Verification**:
- Column: `Orders`
- Action: Sum all values in the Orders column
- Filter: Apply Year/Month filters if selected
- Null Handling: Treat null/empty as 0

**Notes**:
- Sums the `Orders` column (not unique orders)
- Each row may represent multiple orders

---

### 1.3 Total Sales
**Display**: Large number card (e.g., "€592,600")

**Formula**:
```
Total Sales = SUM(Total sales)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'totalSales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}}
  }
}
```

**CSV Verification**:
- Column: `Total sales`
- Action: Sum all values in the Total sales column
- Filter: Apply Year/Month filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

**Notes**:
- Sums all sales amounts
- Currency format: € (Euros)

---

### 1.4 Avg Order Value
**Display**: Large number card (e.g., "€35")

**Formula**:
```
Avg Order Value = Total Sales / Total Orders
```

**MongoDB Aggregation**:
```javascript
{
  '$project': {
    'avgOrderValue': {
      '$cond': [
        {'$gt': ['$totalOrders', 0]},
        {'$divide': ['$totalSales', '$totalOrders']},
        0
      ]
    }
  }
}
```

**CSV Verification**:
- Step 1: Calculate Total Sales (see 1.3)
- Step 2: Calculate Total Orders (see 1.2)
- Step 3: Divide Total Sales by Total Orders
- If Total Orders = 0, then Avg Order Value = 0
- Currency: Euros (€)

**Notes**:
- Division by zero protection: Returns 0 if no orders

---

## 2. Charts and Visualizations

### 2.1 New vs Returning Customers (Donut Chart)

**Chart Type**: Donut Chart  
**Data Source**: `newVsReturning`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$New or returning customer',
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'unique_customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'type': '$_id',
    'orders': 1,
    'sales': 1,
    'unique_customers': {'$size': '$unique_customers'}
  }
}
```

**CSV Columns Used**:
- `New or returning customer` - Groups by this field (values: "New", "Returning")
- `Orders` - Sum for each group
- `Total sales` - Sum for each group
- `Customer email` - Count unique customers per group

**Chart Display**:
- **Labels**: `type` field (New, Returning)
- **Values**: `sales` (Total sales per type)
- **Tooltip**: Shows `sales` with percentage of total

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `New or returning customer`
3. For each group:
   - Sum `Orders` column
   - Sum `Total sales` column
   - Count unique `Customer email` values
4. Calculate percentage: `(group_sales / total_sales) * 100`

---

### 2.2 Sales Channel Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `channelPerformance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Order or return',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'channel': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1}
}
```

**CSV Columns Used**:
- `Order or return` - Groups by this field (values: "order", "return", etc.)
- `Total sales` - Sum for each channel
- `Orders` - Sum for each channel
- `Customer email` - Count unique customers per channel

**Chart Display**:
- **X-Axis**: `channel` (Order or return values)
- **Y-Axis**: `sales` (Total sales)
- **Bars**: Height represents sales amount

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Order or return`
3. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
4. Sort by sales descending

---

### 2.3 Top Regions by Sales (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `regionPerformance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Shipping region',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'region': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1},
  '$limit': 10
}
```

**CSV Columns Used**:
- `Shipping region` - Groups by this field
- `Total sales` - Sum for each region
- `Orders` - Sum for each region
- `Customer email` - Count unique customers per region

**Chart Display**:
- **X-Axis**: `region` (Shipping region names)
- **Y-Axis**: `sales` (Total sales)
- **Limit**: Top 10 regions by sales

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Shipping region`
3. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
4. Sort by sales descending
5. Take top 10

---

### 2.4 Traffic Source Analysis (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `trafficSource`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Referring channel': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': '$Referring channel',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'source': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1},
  '$limit': 10
}
```

**CSV Columns Used**:
- `Referring channel` - Groups by this field (must not be null)
- `Total sales` - Sum for each source
- `Orders` - Sum for each source
- `Customer email` - Count unique customers per source

**Chart Display**:
- **X-Axis**: `source` (Referring channel names)
- **Y-Axis**: `sales` (Total sales)
- **Limit**: Top 10 sources by sales

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Referring channel` is null/empty
3. Group by `Referring channel`
4. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
5. Sort by sales descending
6. Take top 10

---

### 2.5 Customer Lifetime Value (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `customerLifetimeValue`

**MongoDB Aggregation**:
```javascript
// Step 1: Group by customer to get their order count
{
  '$group': {
    '_id': '$Customer email',
    'customer_orders': {'$max': {'$toDouble': {'$ifNull': ['$Customer number of orders', 0]}}},
    'total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'total_orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
  }
}

// Step 2: Bucket customers by order count
{
  '$project': {
    'bucket': {
      '$switch': {
        'branches': [
          {'case': {'$lte': ['$customer_orders', 1]}, 'then': '1'},
          {'case': {'$lte': ['$customer_orders', 3]}, 'then': '2-3'},
          {'case': {'$lte': ['$customer_orders', 5]}, 'then': '4-5'},
          {'case': {'$lte': ['$customer_orders', 10]}, 'then': '6-10'},
          {'case': {'$lte': ['$customer_orders', 20]}, 'then': '11-20'},
          {'case': True, 'then': '20+'}
        ]
      }
    }
  }
}

// Step 3: Group by bucket and aggregate
{
  '$group': {
    '_id': '$bucket',
    'total_sales': {'$sum': '$total_sales'},
    'unique_customers': {'$addToSet': '$_id'},
    'total_orders': {'$sum': '$total_orders'}
  },
  '$project': {
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
  }
}
```

**CSV Columns Used**:
- `Customer email` - Groups by customer
- `Customer number of orders` - Gets max value per customer (lifetime orders)
- `Total sales` - Sum per customer
- `Orders` - Sum per customer

**Bucket Logic**:
- **1**: `Customer number of orders <= 1`
- **2-3**: `Customer number of orders <= 3` (and > 1)
- **4-5**: `Customer number of orders <= 5` (and > 3)
- **6-10**: `Customer number of orders <= 10` (and > 5)
- **11-20**: `Customer number of orders <= 20` (and > 10)
- **20+**: `Customer number of orders > 20`

**Chart Display**:
- **X-Axis**: `order_bucket` (1, 2-3, 4-5, 6-10, 11-20, 20+)
- **Y-Axis**: `total_sales` or `avg_sales_per_customer` (depending on chart config)

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Customer email`
3. For each customer:
   - Get MAX(`Customer number of orders`) - this is their lifetime order count
   - Sum `Total sales` for that customer
   - Sum `Orders` for that customer
4. Assign each customer to a bucket based on their lifetime order count
5. Group by bucket
6. For each bucket:
   - Sum `total_sales` from all customers in bucket
   - Count unique customers in bucket
   - Calculate `avg_sales_per_customer = total_sales / unique_customers`

---

### 2.6 Email Subscription Status (Donut Chart)

**Chart Type**: Donut Chart  
**Data Source**: `subscriptionStatus`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Customer email subscription status',
    'unique_customers': {'$addToSet': '$Customer email'},
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
  },
  '$project': {
    'status': '$_id',
    'unique_customers': {'$size': '$unique_customers'},
    'sales': 1,
    'orders': 1
  }
}
```

**CSV Columns Used**:
- `Customer email subscription status` - Groups by this field (values: "SUBSCRIBED", "UNSUBSCRIBED", "PENDING", "UNKNOWN", etc.)
- `Customer email` - Count unique customers per status
- `Total sales` - Sum for each status
- `Orders` - Sum for each status

**Chart Display**:
- **Labels**: `status` (Subscription status values)
- **Values**: `unique_customers` (Number of unique customers per status)
- **Tooltip**: Shows `unique_customers` with percentage

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Customer email subscription status`
3. For each group:
   - Count unique `Customer email` values
   - Sum `Total sales`
   - Sum `Orders`
4. Calculate percentage: `(group_customers / total_customers) * 100`

---

### 2.7 Top 15 Products by Sales (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `topProducts`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Product variant SKU': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': '$Product variant SKU',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'quantity': {'$sum': {'$toDouble': {'$ifNull': ['$Quantity ordered', 0]}}}
  },
  '$project': {
    'sku': '$_id',
    'sales': 1,
    'orders': 1,
    'quantity': 1
  },
  '$sort': {'sales': -1},
  '$limit': 15
}
```

**CSV Columns Used**:
- `Product variant SKU` - Groups by this field (must not be null)
- `Total sales` - Sum for each SKU
- `Orders` - Sum for each SKU
- `Quantity ordered` - Sum for each SKU

**Chart Display**:
- **X-Axis**: `sku` (Product variant SKU)
- **Y-Axis**: `sales` (Total sales)
- **Limit**: Top 15 products by sales

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Product variant SKU` is null/empty
3. Group by `Product variant SKU`
4. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Sum `Quantity ordered`
5. Sort by sales descending
6. Take top 15

---

### 2.8 Day of Week Sales Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `dayOfWeekAnalysis`

**MongoDB Aggregation**:
```javascript
// Step 1: Convert Day field to date if it's a string
{
  '$project': {
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
  }
}

// Step 2: Extract day of week (1=Sunday, 2=Monday, ..., 7=Saturday)
{
  '$project': {
    'dayOfWeek': {'$dayOfWeek': '$dayDate'},
    'Total sales': 1,
    'Orders': 1,
    'Customer email': 1
  }
}

// Step 3: Group by day of week
{
  '$group': {
    '_id': '$dayOfWeek',
    'sales': {'$sum': '$Total sales'},
    'orders': {'$sum': '$Orders'},
    'customers': {'$addToSet': '$Customer email'}
  }
}

// Step 4: Convert day number to day name and sort (Monday=1, Tuesday=2, ..., Sunday=7)
{
  '$project': {
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
        ]
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
        ]
      }
    },
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  }
},
{'$sort': {'day_order': 1}}
```

**CSV Columns Used**:
- `Day` - Date field (may be string or date object)
- `Total sales` - Sum for each day of week
- `Orders` - Sum for each day of week
- `Customer email` - Count unique customers per day of week

**Day of Week Mapping**:
- MongoDB `$dayOfWeek`: 1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday
- Display Order: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday

**Chart Display**:
- **X-Axis**: `day` (Day names: Monday through Sunday)
- **Y-Axis**: `sales` (Total sales)
- **Sort Order**: Monday first, Sunday last

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Extract day of week from `Day` column:
   - If `Day` is a string, convert to date
   - Get day of week number (1=Sunday, 2=Monday, etc.)
3. Group by day of week number
4. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
5. Convert day numbers to day names
6. Sort by display order (Monday first)

---

### 2.9 Monthly Sales & Customer Trends (Combo Chart)

**Chart Type**: Combo Chart (Bars + Line)  
**Data Source**: `monthlyTrend`

**MongoDB Aggregation**:
```javascript
{
  '$match': {
    **base_match,
    'Year': {'$ne': None, '$exists': True, '$type': 'number'},
    'Month': {'$ne': None, '$exists': True, '$type': 'number'}
  },
  '$group': {
    '_id': {'Year': '$Year', 'Month': '$Month'},
    'Total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'Orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'Customer_email': {'$addToSet': '$Customer email'},
    'Orders_first_time': {'$sum': {'$toDouble': {'$ifNull': ['$Orders (first-time)', 0]}}},
    'Orders_returning': {'$sum': {'$toDouble': {'$ifNull': ['$Orders (returning)', 0]}}}
  },
  '$project': {
    'Year': '$_id.Year',
    'Month': '$_id.Month',
    'Total_sales': 1,
    'Orders': 1,
    'Customer_email': {'$size': '$Customer_email'},
    'Orders_first_time': 1,
    'Orders_returning': 1
  },
  '$sort': {'Year': 1, 'Month': 1}
}
```

**CSV Columns Used**:
- `Year` - Groups by this field (must be numeric)
- `Month` - Groups by this field (must be numeric, 1-12)
- `Total sales` - Sum for each month
- `Orders` - Sum for each month
- `Customer email` - Count unique customers per month
- `Orders (first-time)` - Sum for each month
- `Orders (returning)` - Sum for each month

**Chart Display**:
- **X-Axis**: Month labels (e.g., "January 2025", "February 2025")
- **Y-Axis (Left)**: Sales amount (for bars)
- **Y-Axis (Right)**: Customer count (for line)
- **Bars**: `Total_sales` (light beige) and `Orders_first_time` (dark grey)
- **Line**: `Orders_returning` (darker grey line)

**Month Label Format**:
- Format: `{MonthName} {Year}` (e.g., "January 2025")
- Month names: Full month names (January, February, etc.)

**CSV Verification Steps**:
1. Filter data by Year/Month if selected (but keep all months for trend)
2. Ensure `Year` and `Month` are valid numbers
3. Group by `Year` and `Month`
4. For each month:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
   - Sum `Orders (first-time)`
   - Sum `Orders (returning)`
5. Sort by Year ascending, then Month ascending
6. Format labels as "{MonthName} {Year}"

---

### 2.10 Referring Platform Analysis (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `platformAnalysis`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Referring platform': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': '$Referring platform',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'platform': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1},
  '$limit': 10
}
```

**CSV Columns Used**:
- `Referring platform` - Groups by this field (must not be null)
- `Total sales` - Sum for each platform
- `Orders` - Sum for each platform
- `Customer email` - Count unique customers per platform

**Chart Display**:
- **X-Axis**: `platform` (Referring platform names)
- **Y-Axis**: `sales` (Total sales)
- **Limit**: Top 10 platforms by sales

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Referring platform` is null/empty
3. Group by `Referring platform`
4. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
5. Sort by sales descending
6. Take top 10

---

### 2.11 Traffic Type Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `trafficType`

**MongoDB Aggregation**:
```javascript
// Step 1: Normalize traffic type case (prevents "Unknown" vs "unknown" duplicates)
{
  '$addFields': {
    'traffic_type_lower': {'$toLower': {'$ifNull': ['$Traffic type', '']}},
    'traffic_type_original': {'$ifNull': ['$Traffic type', '']}
  }
}

// Step 2: Create normalized traffic type
{
  '$addFields': {
    'normalized_traffic_type': {
      '$cond': {
        'if': {
          '$or': [
            {'$eq': ['$traffic_type_lower', 'unknown']},
            {'$eq': ['$traffic_type_original', '']},
            {'$eq': ['$traffic_type_original', None]}
          ]
        },
        'then': 'Unknown',  // Standardize to "Unknown" with capital U
        'else': {
          '$concat': [
            {'$toUpper': {'$substr': ['$traffic_type_original', 0, 1]}},  // First letter uppercase
            {'$toLower': {'$substr': ['$traffic_type_original', 1, ...]}}  // Rest lowercase
          ]
        }
      }
    }
  }
}

// Step 3: Group by normalized traffic type
{
  '$group': {
    '_id': '$normalized_traffic_type',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'type': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1}
}
```

**CSV Columns Used**:
- `Traffic type` - Groups by this field (case-normalized)
- `Total sales` - Sum for each traffic type
- `Orders` - Sum for each traffic type
- `Customer email` - Count unique customers per traffic type

**Case Normalization Rules**:
- "unknown" (any case) → "Unknown"
- Empty/null values → "Unknown"
- Other values → Title case (first letter uppercase, rest lowercase)
  - Example: "organic" → "Organic", "DIRECT" → "Direct"

**Chart Display**:
- **X-Axis**: `type` (Normalized traffic type names)
- **Y-Axis**: `sales` (Total sales)
- **Sort**: By sales descending

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Traffic type` is null/empty
3. **Normalize case**:
   - Convert "unknown" (any case) to "Unknown"
   - Convert other values to title case
4. Group by normalized `Traffic type`
5. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
6. Sort by sales descending

**Important**: This chart has case normalization to prevent duplicate "Unknown" entries!

---

### 2.12 Hour of Day Shopping Patterns (Line Chart)

**Chart Type**: Line Chart  
**Data Source**: `hourlyPatterns`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Hour of day': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': {'$toInt': {'$ifNull': ['$Hour of day', 0]}},
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'hour': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'hour': 1}
}
```

**CSV Columns Used**:
- `Hour of day` - Groups by this field (must not be null, converted to integer)
- `Total sales` - Sum for each hour
- `Orders` - Sum for each hour
- `Customer email` - Count unique customers per hour

**Chart Display**:
- **X-Axis**: `hour` (0-23, representing hours of the day)
- **Y-Axis (Left)**: `sales` (Total sales)
- **Y-Axis (Right)**: `orders` (Number of orders)
- **Lines**: Two lines - one for sales, one for orders
- **Labels**: Format as "{hour}:00" (e.g., "0:00", "1:00", ..., "23:00")

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Hour of day` is null/empty
3. Convert `Hour of day` to integer (0-23)
4. Group by hour (0-23)
5. For each hour:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
6. Sort by hour ascending (0 to 23)

---

### 2.13 Country Distribution (Donut Chart)

**Chart Type**: Donut Chart  
**Data Source**: `countryDistribution`

**MongoDB Aggregation**:
```javascript
{
  '$match': base_match,
  '$group': {
    '_id': '$Shipping country',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'country': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1}
}
```

**CSV Columns Used**:
- `Shipping country` - Groups by this field
- `Total sales` - Sum for each country
- `Orders` - Sum for each country
- `Customer email` - Count unique customers per country

**Chart Display**:
- **Labels**: `country` (Shipping country names)
- **Values**: `sales` (Total sales per country)
- **Tooltip**: Shows `sales` with percentage of total

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Shipping country`
3. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
4. Sort by sales descending
5. Calculate percentage: `(country_sales / total_sales) * 100`

---

### 2.14 SMS Subscription Status (Donut Chart)

**Chart Type**: Donut Chart  
**Data Source**: `smsSubscription`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Customer SMS subscription status': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': '$Customer SMS subscription status',
    'unique_customers': {'$addToSet': '$Customer email'},
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
  },
  '$project': {
    'status': '$_id',
    'unique_customers': {'$size': '$unique_customers'},
    'sales': 1,
    'orders': 1
  }
}
```

**CSV Columns Used**:
- `Customer SMS subscription status` - Groups by this field (must not be null)
- `Customer email` - Count unique customers per status
- `Total sales` - Sum for each status
- `Orders` - Sum for each status

**Chart Display**:
- **Labels**: `status` (SMS subscription status values)
- **Values**: `unique_customers` (Number of unique customers per status)
- **Tooltip**: Shows `unique_customers` with percentage

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Customer SMS subscription status` is null/empty
3. Group by `Customer SMS subscription status`
4. For each group:
   - Count unique `Customer email` values
   - Sum `Total sales`
   - Sum `Orders`
5. Calculate percentage: `(group_customers / total_customers) * 100`

---

### 2.15 Referring Medium Analysis (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `mediumAnalysis`

**MongoDB Aggregation**:
```javascript
{
  '$match': {**base_match, 'Referring medium': {'$ne': None, '$exists': True}},
  '$group': {
    '_id': '$Referring medium',
    'sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'customers': {'$addToSet': '$Customer email'}
  },
  '$project': {
    'medium': '$_id',
    'sales': 1,
    'orders': 1,
    'customers': {'$size': '$customers'}
  },
  '$sort': {'sales': -1}
}
```

**CSV Columns Used**:
- `Referring medium` - Groups by this field (must not be null)
- `Total sales` - Sum for each medium
- `Orders` - Sum for each medium
- `Customer email` - Count unique customers per medium

**Chart Display**:
- **X-Axis**: `medium` (Referring medium names)
- **Y-Axis**: `sales` (Total sales)
- **Sort**: By sales descending

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Filter out rows where `Referring medium` is null/empty
3. Group by `Referring medium`
4. For each group:
   - Sum `Total sales`
   - Sum `Orders`
   - Count unique `Customer email`
5. Sort by sales descending

---

### 2.16 Return Rate Trend Over Time (Area/Line Chart)

**Chart Type**: Area/Line Chart  
**Data Source**: `returnTrend`

**MongoDB Aggregation**:
```javascript
// Step 1: Get return data by month
{
  '$match': {
    **monthly_match,
    'Order or return': 'return'
  },
  '$group': {
    '_id': {'Year': '$Year', 'Month': '$Month'},
    'Total returns': {'$sum': {'$abs': {'$toDouble': {'$ifNull': ['$Total returns', 0]}}}},
    'Orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}}
  }
}

// Step 2: Get monthly sales for return rate calculation
{
  '$match': monthly_match,
  '$group': {
    '_id': {'Year': '$Year', 'Month': '$Month'},
    'Total sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}}
  }
}

// Step 3: Calculate return rate
Return Rate (%) = (Total returns / Total sales) * 100
```

**CSV Columns Used**:
- `Year` - Groups by this field
- `Month` - Groups by this field
- `Order or return` - Filters for "return" only
- `Total returns` - Sum for returns (absolute value)
- `Total sales` - Sum for all orders (for return rate calculation)

**Formula**:
```
Return Rate (%) = (Total Returns / Total Sales) * 100
```

**Chart Display**:
- **X-Axis**: Month labels (e.g., "January 2025", "February 2025")
- **Y-Axis**: Return Rate (%) (0-100)
- **Line**: Shows return rate trend over time

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. **For Returns**:
   - Filter where `Order or return` = "return"
   - Group by `Year` and `Month`
   - For each month: Sum ABS(`Total returns`)
3. **For Sales**:
   - Group by `Year` and `Month` (all orders)
   - For each month: Sum `Total sales`
4. **Calculate Return Rate**:
   - For each month: `Return Rate = (Total Returns / Total Sales) * 100`
   - If Total Sales = 0, Return Rate = 0
5. Sort by Year ascending, then Month ascending
6. Format labels as "{MonthName} {Year}"

---

## 3. Top 20 Customers Table

**Table Location**: Bottom of the screen  
**Data Source**: `topCustomers`

**MongoDB Aggregation**:
```javascript
{
  '$match': base_match,
  '$group': {
    '_id': {'email': '$Customer email', 'name': '$Customer name'},
    'total_sales': {'$sum': {'$toDouble': {'$ifNull': ['$Total sales', 0]}}},
    'total_orders': {'$sum': {'$toDouble': {'$ifNull': ['$Orders', 0]}}},
    'lifetime_orders': {'$max': {'$toDouble': {'$ifNull': ['$Customer number of orders', 0]}}}
  },
  '$project': {
    'email': '$_id.email',
    'name': '$_id.name',
    'total_sales': 1,
    'total_orders': 1,
    'lifetime_orders': 1
  },
  '$sort': {'total_sales': -1},
  '$limit': 20
}
```

**CSV Columns Used**:
- `Customer email` - Groups by this field (unique identifier)
- `Customer name` - Gets name for each customer
- `Total sales` - Sum for each customer
- `Orders` - Sum for each customer
- `Customer number of orders` - Gets MAX value per customer (lifetime orders)

**Table Columns**:
1. **Customer Name**: `name` (from `Customer name` column)
2. **Email**: `email` (from `Customer email` column)
3. **Total Sales**: `total_sales` (Sum of `Total sales` for that customer)
4. **Orders**: `total_orders` (Sum of `Orders` for that customer)
5. **Lifetime Orders**: `lifetime_orders` (MAX of `Customer number of orders` for that customer)

**CSV Verification Steps**:
1. Filter data by Year/Month if selected
2. Group by `Customer email` and `Customer name`
3. For each customer:
   - Sum `Total sales` → `total_sales`
   - Sum `Orders` → `total_orders`
   - Get MAX(`Customer number of orders`) → `lifetime_orders`
4. Sort by `total_sales` descending
5. Take top 20 customers

**Important Notes**:
- `lifetime_orders` uses MAX, not SUM, because it represents the customer's lifetime order count
- Customers are sorted by total sales (highest first)
- Table shows top 20 customers only

---

## 4. Summary Metrics (Used in Summary Object)

The summary object contains aggregated metrics used throughout the dashboard:

**Summary Fields**:
- `totalCustomers`: Count of unique customers (see 1.1)
- `totalOrders`: Sum of all orders (see 1.2)
- `totalSales`: Sum of all sales (see 1.3)
- `avgOrderValue`: Average order value (see 1.4)
- `newCustomers`: Count of new customer orders (see below)
- `returningCustomers`: Count of returning customer orders (see below)

### 4.1 New Customers Count

**Formula**:
```
New Customers = COUNT(rows where 'New or returning customer' = 'New')
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'newCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'New']}, 1, 0]}}
  }
}
```

**CSV Verification**:
- Column: `New or returning customer`
- Action: Count rows where value = "New"
- Filter: Apply Year/Month filters if selected

**Note**: This counts order rows, not unique customers. Each order row with "New" is counted.

---

### 4.2 Returning Customers Count

**Formula**:
```
Returning Customers = COUNT(rows where 'New or returning customer' = 'Returning')
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'returningCustomers': {'$sum': {'$cond': [{'$eq': ['$New or returning customer', 'Returning']}, 1, 0]}}
  }
}
```

**CSV Verification**:
- Column: `New or returning customer`
- Action: Count rows where value = "Returning"
- Filter: Apply Year/Month filters if selected

**Note**: This counts order rows, not unique customers. Each order row with "Returning" is counted.

---

## 5. CSV Column Reference

### Complete List of CSV Columns Used

| Column Name | Used In | Purpose |
|------------|---------|---------|
| `Year` | Filters, Monthly Trends, Return Trends | Filter and group by year |
| `Month` | Filters, Monthly Trends, Return Trends | Filter and group by month |
| `Customer email` | All metrics | Unique customer identifier, counting unique customers |
| `Customer name` | Top Customers Table | Customer display name |
| `Total sales` | All sales metrics | Sales amount (currency) |
| `Orders` | All order metrics | Number of orders |
| `New or returning customer` | New vs Returning Chart, Summary | Categorize as New or Returning |
| `Order or return` | Channel Performance, Return Trends | Categorize as order or return |
| `Shipping region` | Top Regions Chart | Geographic region |
| `Shipping country` | Country Distribution Chart | Geographic country |
| `Referring channel` | Traffic Source Chart | Traffic source channel |
| `Referring platform` | Platform Analysis Chart | Referring platform |
| `Referring medium` | Medium Analysis Chart | Referring medium |
| `Traffic type` | Traffic Type Chart | Traffic type (case-normalized) |
| `Customer email subscription status` | Email Subscription Chart | Email subscription status |
| `Customer SMS subscription status` | SMS Subscription Chart | SMS subscription status |
| `Customer number of orders` | Customer Lifetime Value, Top Customers | Lifetime order count per customer |
| `Orders (first-time)` | Monthly Trends Chart | First-time orders |
| `Orders (returning)` | Monthly Trends Chart | Returning orders |
| `Product variant SKU` | Top Products Chart | Product identifier |
| `Quantity ordered` | Top Products Chart | Quantity sold |
| `Hour of day` | Hourly Patterns Chart | Hour of day (0-23) |
| `Day` | Day of Week Chart | Date field (converted to day of week) |
| `Total returns` | Return Trends Chart | Return amount (absolute value used) |
| `Net returns` | Order Return Analysis | Net returns amount |

---

## 6. Common Calculations and Formulas

### 6.1 Unique Customer Count
```
Unique Customers = COUNT(DISTINCT Customer email)
```
- Uses `$addToSet` in MongoDB to get unique set
- Uses `$size` to count the set

### 6.2 Sum with Null Handling
```
Sum = SUM(column_value) where null/empty = 0
```
- MongoDB: `{'$sum': {'$toDouble': {'$ifNull': ['$column', 0]}}}`
- CSV: Sum all non-null values, treat null/empty as 0

### 6.3 Percentage Calculation
```
Percentage = (Part / Total) * 100
```
- Used in donut charts for segment percentages
- Example: `(group_sales / total_sales) * 100`

### 6.4 Average Calculation
```
Average = Sum / Count
```
- Used for Avg Order Value: `Total Sales / Total Orders`
- Division by zero protection: Returns 0 if count = 0

### 6.5 Case Normalization (Traffic Type)
```
If value.lower() == 'unknown' or value == '' or value == null:
    normalized = 'Unknown'
Else:
    normalized = value[0].upper() + value[1:].lower()
```

### 6.6 Day of Week Extraction
```
If Day is string:
    dayDate = convert_string_to_date(Day)
Else:
    dayDate = Day

dayOfWeek = dayOfWeek(dayDate)  // 1=Sunday, 2=Monday, ..., 7=Saturday
dayName = map_day_number_to_name(dayOfWeek)
```

### 6.7 Return Rate Calculation
```
Return Rate (%) = (Total Returns / Total Sales) * 100
```
- Total Returns: Sum of `Total returns` where `Order or return` = "return" (absolute value)
- Total Sales: Sum of `Total sales` for all orders in that month
- If Total Sales = 0, Return Rate = 0

---

## 7. Filtering Logic

### 7.1 Year Filter
- **Column**: `Year` (numeric)
- **Filter Type**: `$in` operator
- **Example**: If years = "2023,2024", filter: `Year IN [2023, 2024]`
- **CSV**: Filter rows where `Year` column matches selected years

### 7.2 Month Filter
- **Column**: `Month` (numeric, 1-12)
- **Filter Type**: `$in` operator
- **Month Name Mapping**:
  - "January" or "Jan" → 1
  - "February" or "Feb" → 2
  - "March" or "Mar" → 3
  - ... (and so on)
- **Example**: If months = "January,February", filter: `Month IN [1, 2]`
- **CSV**: Filter rows where `Month` column matches selected months

### 7.3 Combined Filters
- Filters are combined with AND logic
- Example: Year=2024 AND Month=1 (January 2024)
- All aggregations respect these filters via `base_match`

---

## 8. Data Type Conversions

### 8.1 Numeric Conversions
- All numeric columns are converted using `$toDouble` or `parseFloat()`
- Null/empty values are treated as 0 using `$ifNull` or default values

### 8.2 Date Conversions
- `Day` field may be string or date object
- If string: Convert using `$dateFromString`
- If date: Use as-is
- Extract day of week using `$dayOfWeek`

### 8.3 String Normalization
- Traffic Type: Case normalization (see 6.5)
- All string comparisons are case-sensitive unless normalized

---

## 9. Sorting and Limits

### 9.1 Default Sorting
- **By Sales**: Most charts sort by sales descending (`$sort: {'sales': -1}`)
- **By Time**: Time-based charts sort chronologically (`$sort: {'Year': 1, 'Month': 1}`)
- **By Hour**: Hourly charts sort by hour ascending (`$sort: {'hour': 1}`)
- **By Day**: Day of week sorted by display order (Monday first)

### 9.2 Limits
- **Top Regions**: Limit 10
- **Top Products**: Limit 15
- **Top Customers**: Limit 20
- **Top Platforms**: Limit 10
- **Top Traffic Sources**: Limit 10
- **Hourly Patterns**: Limit 24 (all hours)

---

## 10. Testing Checklist

### 10.1 KPI Verification
- [ ] Total Customers: Count unique `Customer email` values
- [ ] Total Orders: Sum `Orders` column
- [ ] Total Sales: Sum `Total sales` column
- [ ] Avg Order Value: `Total Sales / Total Orders`

### 10.2 Chart Verification
- [ ] New vs Returning: Group by `New or returning customer`, sum sales
- [ ] Sales Channel: Group by `Order or return`, sum sales
- [ ] Top Regions: Group by `Shipping region`, sum sales, top 10
- [ ] Traffic Source: Group by `Referring channel`, sum sales, top 10
- [ ] Customer Lifetime Value: Group by customer, bucket by order count, aggregate
- [ ] Email Subscription: Group by `Customer email subscription status`, count customers
- [ ] Top Products: Group by `Product variant SKU`, sum sales, top 15
- [ ] Day of Week: Extract day from `Day`, group by day, sum sales
- [ ] Monthly Trends: Group by Year+Month, aggregate all metrics
- [ ] Platform Analysis: Group by `Referring platform`, sum sales, top 10
- [ ] Traffic Type: Group by `Traffic type` (case-normalized), sum sales
- [ ] Hourly Patterns: Group by `Hour of day`, sum sales and orders
- [ ] Country Distribution: Group by `Shipping country`, sum sales
- [ ] SMS Subscription: Group by `Customer SMS subscription status`, count customers
- [ ] Medium Analysis: Group by `Referring medium`, sum sales
- [ ] Return Rate Trend: Filter returns, group by month, calculate return rate

### 10.3 Table Verification
- [ ] Top 20 Customers: Group by `Customer email`, sum sales, sort descending, top 20
- [ ] Verify `lifetime_orders` uses MAX, not SUM

### 10.4 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Combined filters: AND logic (both must match)

### 10.5 Edge Cases
- [ ] Null/empty values treated as 0
- [ ] Division by zero protection (returns 0)
- [ ] Case normalization for Traffic Type
- [ ] Date string conversion for Day field
- [ ] Unique customer counting (not double-counting)

---

## 11. Common Issues and Solutions

### 11.1 Duplicate "Unknown" in Traffic Type
**Issue**: Two "Unknown" entries (capital U and lowercase u)  
**Solution**: Case normalization (see 6.5) - all "unknown" variations → "Unknown"

### 11.2 Day of Week Not Showing
**Issue**: Day field might be string instead of date  
**Solution**: Convert string to date using `$dateFromString` before extracting day of week

### 11.3 Return Rate Calculation
**Issue**: Return rate might be incorrect  
**Solution**: 
- Use absolute value of `Total returns`
- Calculate: `(Total Returns / Total Sales) * 100`
- Ensure Total Sales includes all orders (not just returns)

### 11.4 Customer Lifetime Value Buckets
**Issue**: Buckets might not match expected ranges  
**Solution**: 
- Use MAX(`Customer number of orders`) per customer (not SUM)
- Bucket logic: <=1, <=3, <=5, <=10, <=20, >20

---

## 12. CSV File Structure Reference

### Expected CSV Columns (Shopify Data Export)

The CSV file should contain the following columns (exact names may vary slightly):

**Required Columns**:
- `Year` (numeric)
- `Month` (numeric, 1-12)
- `Customer email` (string, unique identifier)
- `Customer name` (string)
- `Total sales` (numeric, currency)
- `Orders` (numeric)
- `New or returning customer` (string: "New" or "Returning")
- `Order or return` (string: "order" or "return")
- `Shipping region` (string)
- `Shipping country` (string)
- `Referring channel` (string)
- `Referring platform` (string)
- `Referring medium` (string)
- `Traffic type` (string)
- `Customer email subscription status` (string)
- `Customer SMS subscription status` (string)
- `Customer number of orders` (numeric)
- `Orders (first-time)` (numeric)
- `Orders (returning)` (numeric)
- `Product variant SKU` (string)
- `Quantity ordered` (numeric)
- `Hour of day` (numeric, 0-23)
- `Day` (date or string)
- `Total returns` (numeric, may be negative)
- `Net returns` (numeric)

**Note**: Column names in MongoDB may have spaces (e.g., "Total sales") or may be stored with different casing. The aggregation pipelines handle this.

---

## 13. Verification Examples

### Example 1: Verify Total Customers
```
CSV Steps:
1. Filter by Year=2024 if selected
2. Filter by Month=1 if selected
3. Get unique values from "Customer email" column
4. Count the unique values
5. Result should match "Total Customers" KPI
```

### Example 2: Verify Traffic Type Chart
```
CSV Steps:
1. Filter by Year/Month if selected
2. Filter out rows where "Traffic type" is null/empty
3. Normalize case:
   - "unknown" → "Unknown"
   - "organic" → "Organic"
   - "DIRECT" → "Direct"
4. Group by normalized "Traffic type"
5. For each group:
   - Sum "Total sales"
   - Sum "Orders"
   - Count unique "Customer email"
6. Sort by sales descending
7. Results should match chart data
```

### Example 3: Verify Return Rate Trend
```
CSV Steps:
1. Filter by Year/Month if selected
2. For Returns:
   - Filter where "Order or return" = "return"
   - Group by Year and Month
   - Sum ABS("Total returns") for each month
3. For Sales:
   - Group by Year and Month (all orders)
   - Sum "Total sales" for each month
4. For each month:
   - Return Rate = (Total Returns / Total Sales) * 100
5. Sort by Year, then Month
6. Results should match chart data
```

---

## 14. Notes for Testers

### 14.1 Data Filtering
- All calculations respect Year and Month filters
- If no filters selected, all data is included
- Filters are applied at the aggregation level (not after)

### 14.2 Null Handling
- Null/empty values are treated as 0 for numeric calculations
- Null values are excluded from unique customer counts
- Null values are filtered out for charts that require the field

### 14.3 Currency
- All sales values are in Euros (€)
- Format: €X,XXX.XX or €X.XXk or €X.XXM

### 14.4 Rounding
- Percentages: Rounded to 1 decimal place (e.g., 45.6%)
- Currency: Formatted with appropriate precision
- Averages: May show decimal places

### 14.5 Case Sensitivity
- Most fields are case-sensitive
- Exception: Traffic Type is case-normalized
- "Unknown" vs "unknown" are treated as the same (after normalization)

### 14.6 Date Handling
- Day field may be string or date object
- String dates are converted to date objects
- Day of week extraction uses MongoDB `$dayOfWeek` (1=Sunday, 2=Monday, etc.)

---

## 15. Quick Reference: Chart → CSV Columns

| Chart Name | Primary Grouping Column | Value Column | Additional Columns |
|------------|------------------------|--------------|-------------------|
| New vs Returning | `New or returning customer` | `Total sales` | `Orders`, `Customer email` |
| Sales Channel | `Order or return` | `Total sales` | `Orders`, `Customer email` |
| Top Regions | `Shipping region` | `Total sales` | `Orders`, `Customer email` |
| Traffic Source | `Referring channel` | `Total sales` | `Orders`, `Customer email` |
| Customer Lifetime Value | `Customer email` (then bucket) | `Total sales` | `Customer number of orders` |
| Email Subscription | `Customer email subscription status` | `Customer email` (count) | `Total sales`, `Orders` |
| Top Products | `Product variant SKU` | `Total sales` | `Orders`, `Quantity ordered` |
| Day of Week | `Day` (extract day of week) | `Total sales` | `Orders`, `Customer email` |
| Monthly Trends | `Year` + `Month` | `Total sales` | `Orders`, `Customer email`, `Orders (first-time)`, `Orders (returning)` |
| Platform Analysis | `Referring platform` | `Total sales` | `Orders`, `Customer email` |
| Traffic Type | `Traffic type` (normalized) | `Total sales` | `Orders`, `Customer email` |
| Hourly Patterns | `Hour of day` | `Total sales` | `Orders`, `Customer email` |
| Country Distribution | `Shipping country` | `Total sales` | `Orders`, `Customer email` |
| SMS Subscription | `Customer SMS subscription status` | `Customer email` (count) | `Total sales`, `Orders` |
| Medium Analysis | `Referring medium` | `Total sales` | `Orders`, `Customer email` |
| Return Rate Trend | `Year` + `Month` | Return Rate (%) | `Total returns`, `Total sales` |

---

## 16. Contact and Support

If you find discrepancies between the dashboard values and CSV calculations:
1. Check filter settings (Year/Month)
2. Verify column names match exactly
3. Check for null/empty value handling
4. Verify case normalization for Traffic Type
5. Ensure date conversion for Day field
6. Check sorting and limit settings

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

