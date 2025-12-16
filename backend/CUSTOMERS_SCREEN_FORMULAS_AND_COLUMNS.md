# Customers Screen - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Customers screen. Use this document to verify values against the CSV/business data file.

---

## Data Source
**Collection**: `business_data` (MongoDB)  
**CSV File**: Business data export

---

## Filtering
All calculations respect the following filters:
- **Year Filter**: Filters by `Year` column (numeric)
- **Month Filter**: Filters by `Month_Name` column (string)
- **Business Filter**: Filters by `Business` column (string)
- **Channel Filter**: Filters by `Channel` column (string)
- **Customer Filter**: Filters by `Customer` column (string)
- **Brand Filter**: Filters by `Brand` column (string)

**Filter Application**: All aggregations use `match_stage` which includes these filters.

---

## 1. Key Performance Indicators (KPIs) - Top Row

### 1.1 Total Revenue
**Display**: Large number card

**Formula**:
```
Total Revenue = SUM(Revenue)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'total_revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}}
  }
}
```

**CSV Verification**:
- Column: `Revenue`
- Action: Sum all values in the Revenue column
- Filter: Apply all filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

---

### 1.2 Total Gross Profit
**Display**: Large number card

**Formula**:
```
Total Gross Profit = SUM(Gross_Profit)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'total_profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}}
  }
}
```

**CSV Verification**:
- Column: `Gross_Profit`
- Action: Sum all values in the Gross_Profit column
- Filter: Apply all filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

---

### 1.3 Active Channels
**Display**: Large number card

**Formula**:
```
Active Channels = COUNT(DISTINCT Channel) WHERE Channel != "Unknown" AND Revenue > 0
```

**MongoDB Aggregation**:
```javascript
// First get channel performance
{
  '$group': {
    '_id': '$Channel',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}}
  }
}
// Then count channels excluding "Unknown" with Revenue > 0
active_channels = COUNT(channels WHERE Channel != "Unknown" AND Revenue > 0)
```

**CSV Verification**:
- Column: `Channel`
- Action: Count distinct channel names
- Filter: Apply all filters if selected
- Exclusions: Exclude "Unknown" channels
- Requirement: Only count channels with Revenue > 0

**Important**: This counts only channels that have Revenue > 0 and are not "Unknown".

---

### 1.4 Avg. Margin
**Display**: Large number card

**Formula**:
```
Avg. Margin (%) = (Total Gross Profit / Total Revenue) × 100
```

**MongoDB Aggregation**:
```javascript
// First calculate totals
{
  '$group': {
    '_id': None,
    'total_revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'total_profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}}
  }
}
// Then calculate margin
Avg. Margin = (total_profit / total_revenue) × 100
```

**CSV Verification**:
- Step 1: Calculate Total Revenue (see 1.1)
- Step 2: Calculate Total Gross Profit (see 1.2)
- Step 3: Divide Total Gross Profit by Total Revenue
- Step 4: Multiply by 100 to get percentage
- If Total Revenue = 0, then Avg. Margin = 0
- Format: Percentage with 1 decimal place

---

## 2. Charts and Visualizations

### 2.1 Channel Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `channel_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Channel',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}},
    'Units': {'$sum': {'$toDouble': {'$ifNull': ['$Units', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
```

**CSV Columns Used**:
- `Channel` - Groups by this field
- `Revenue` - Sum for each channel
- `Gross_Profit` - Sum for each channel
- `Units` - Sum for each channel

**Chart Display**:
- **X-Axis**: `Channel` (Channel names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Sort**: By revenue descending

**Profit Margin Calculation**:
```javascript
For each channel:
  Profit_Margin (%) = (Gross_Profit / Revenue) × 100
```

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Customer/Brand if selected
2. Group by `Channel`
3. For each channel:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
   - Calculate `Profit_Margin = (Gross_Profit / Revenue) × 100`
4. Sort by Revenue descending

---

### 2.2 Top Customers (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `customer_performance` (top 50)

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Customer',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}},
    'Units': {'$sum': {'$toDouble': {'$ifNull': ['$Units', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
// Limit to top 50 customers
```

**CSV Columns Used**:
- `Customer` - Groups by this field
- `Revenue` - Sum for each customer
- `Gross_Profit` - Sum for each customer
- `Units` - Sum for each customer

**Chart Display**:
- **X-Axis**: `Customer` (Customer names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Limit**: Top 50 customers by revenue
- **Sort**: By revenue descending

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Customer/Brand if selected
2. Group by `Customer`
3. For each customer:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. Sort by Revenue descending
5. Take top 50 customers

---

## 3. CSV Column Reference

### Complete List of CSV Columns Used

| Column Name | Used In | Purpose |
|------------|---------|---------|
| `Year` | Filters | Filter by year |
| `Month_Name` | Filters | Filter by month |
| `Business` | Filters | Filter by business |
| `Channel` | Filters, Channel Performance | Filter and group by channel |
| `Customer` | Filters, Top Customers | Filter and group by customer |
| `Brand` | Filters | Filter by brand |
| `Revenue` | All metrics and charts | Sales amount (currency) |
| `Gross_Profit` | All metrics and charts | Gross profit amount (currency) |
| `Units` | Channel Performance, Top Customers | Cases/units sold (numeric) |

---

## 4. Common Calculations and Formulas

### 4.1 Channel Profit Margin
```
For each Channel:
  Profit_Margin (%) = (Gross_Profit / Revenue) × 100
```

**Notes**:
- Calculated for each channel individually
- Division by zero protection: Returns 0 if Revenue = 0

### 4.2 Customer Performance Aggregation
```
For each Customer:
  Revenue = SUM(Revenue)
  Gross_Profit = SUM(Gross_Profit)
  Units = SUM(Units)
```

### 4.3 Active Channels Count
```
Active Channels = COUNT(DISTINCT Channel) WHERE Channel != "Unknown" AND Revenue > 0
```

**Important Notes**:
- Only counts channels with Revenue > 0
- Excludes "Unknown" channels
- Requires both conditions: Channel != "Unknown" AND Revenue > 0

---

## 5. Filtering Logic

### 5.1 Customer Filter
- **Column**: `Customer` (string)
- **Filter Type**: `$in` operator
- **Example**: If customers = "Customer1,Customer2", filter: `Customer IN ["Customer1", "Customer2"]`
- **CSV**: Filter rows where `Customer` column matches selected customers

### 5.2 Other Filters
- Same as Business Compass screen (Year, Month, Business, Channel, Brand)

---

## 6. Testing Checklist

### 6.1 KPI Verification
- [ ] Total Revenue: Sum `Revenue` column
- [ ] Total Gross Profit: Sum `Gross_Profit` column
- [ ] Active Channels: Count distinct `Channel` values (excluding "Unknown", Revenue > 0)
- [ ] Avg. Margin: `(Total Gross Profit / Total Revenue) × 100`

### 6.2 Chart Verification
- [ ] Channel Performance: Group by `Channel`, sum Revenue, Gross_Profit, Units, calculate Profit_Margin, sort by Revenue descending
- [ ] Top Customers: Group by `Customer`, sum Revenue, Gross_Profit, Units, sort by Revenue descending, top 50

### 6.3 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Business filter: Only includes data from selected businesses
- [ ] Channel filter: Only includes data from selected channels
- [ ] Customer filter: Only includes data from selected customers
- [ ] Brand filter: Only includes data from selected brands
- [ ] Combined filters: AND logic (all must match)

### 6.4 Edge Cases
- [ ] Null/empty values treated as 0
- [ ] Division by zero protection (returns 0)
- [ ] Active channels count excludes "Unknown" and requires Revenue > 0
- [ ] Profit margin calculation per channel
- [ ] Top 50 customers limit

---

## 7. Quick Reference: Chart → CSV Columns

| Chart Name | Primary Grouping Column | Value Column | Additional Columns |
|------------|------------------------|--------------|-------------------|
| Channel Performance | `Channel` | `Revenue` | `Gross_Profit`, `Units`, `Profit_Margin` |
| Top Customers | `Customer` | `Revenue` | `Gross_Profit`, `Units` |

---

## 8. Notes for Testers

### 8.1 Active Channels Count
- **Important**: This counts only channels that have Revenue > 0 AND are not "Unknown"
- Both conditions must be met: Channel != "Unknown" AND Revenue > 0

### 8.2 Channel Profit Margin
- Profit margin is calculated per channel
- Formula: `(Channel Gross_Profit / Channel Revenue) × 100`
- Shows profitability of each channel individually

### 8.3 Top Customers
- Shows top 50 customers by revenue
- Sorted by revenue descending
- All customers with data are included in calculations (not just top 50)

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

