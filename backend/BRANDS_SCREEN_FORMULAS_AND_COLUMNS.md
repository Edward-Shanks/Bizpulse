# Brands Screen - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Brands screen. Use this document to verify values against the CSV/business data file.

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
- **Category Filter**: Filters by `Category` column (string, case-insensitive)
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

### 1.3 Active Brands
**Display**: Large number card

**Formula**:
```
Active Brands = COUNT(DISTINCT Brand) WHERE Brand IS NOT NULL AND Brand != "Unknown" AND Brand != "" AND Brand.lower() NOT IN ["unknown", "none", "null", ""]
```

**MongoDB Aggregation**:
```javascript
// First get brand performance
{
  '$group': {
    '_id': '$Brand',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}}
  }
}
// Then count brands excluding "Unknown", null, empty, or invalid names
active_brands = COUNT(brands WHERE brand is valid)
```

**CSV Verification**:
- Column: `Brand`
- Action: Count distinct brand names
- Filter: Apply all filters if selected
- Exclusions: Exclude "Unknown", null, empty, or invalid brand names
- Note: Counts all brands that have data (not just revenue > 0)

**Important**: This counts all distinct brands that have data, excluding only "Unknown", null, empty, or invalid brand names. It does NOT require revenue > 0.

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

### 2.1 Top Brands by Revenue (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `brand_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Brand',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}},
    'Units': {'$sum': {'$toDouble': {'$ifNull': ['$Units', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
// Limit to top 15 brands
```

**CSV Columns Used**:
- `Brand` - Groups by this field
- `Revenue` - Sum for each brand
- `Gross_Profit` - Sum for each brand
- `Units` - Sum for each brand

**Chart Display**:
- **X-Axis**: `Brand` (Brand names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Limit**: Top 15 brands by revenue
- **Sort**: By revenue descending

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Brand if selected
2. Group by `Brand`
3. For each brand:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. Sort by Revenue descending
5. Take top 15 brands

---

### 2.2 Brand Performance by Business (Stacked Bar Chart)

**Chart Type**: Stacked Bar Chart  
**Data Source**: `brand_by_business`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': {
      'Brand': '$Brand',
      'Business': '$Business'
    },
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
```

**CSV Columns Used**:
- `Brand` - Groups by this field (with Business)
- `Business` - Groups by this field (with Brand)
- `Revenue` - Sum for each Brand-Business combination
- `Gross_Profit` - Sum for each Brand-Business combination

**Chart Display**:
- **X-Axis**: `Brand` (Brand names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Stacks**: Each stack segment represents a Business
- **Colors**: Different color for each Business

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Brand if selected
2. Group by `Brand` AND `Business` (combination)
3. For each Brand-Business combination:
   - Sum `Revenue`
   - Sum `Gross_Profit`
4. Sort by Revenue descending
5. Display as stacked bars (Business segments within each Brand)

---

### 2.3 Brand Year-over-Year Growth (Line Chart)

**Chart Type**: Line Chart  
**Data Source**: `brand_yoy_growth`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': {
      'Brand': '$Brand',
      'Year': '$Year'
    },
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}}
  },
  '$sort': {'_id.Brand': 1, '_id.Year': 1}
}
```

**CSV Columns Used**:
- `Brand` - Groups by this field (with Year)
- `Year` - Groups by this field (with Brand)
- `Revenue` - Sum for each Brand-Year combination

**Chart Display**:
- **X-Axis**: `Year` (e.g., 2023, 2024, 2025)
- **Y-Axis**: `Revenue` (Total revenue)
- **Lines**: One line per Brand
- **Colors**: Different color for each Brand

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Brand if selected
2. Group by `Brand` AND `Year` (combination)
3. For each Brand-Year combination: Sum `Revenue`
4. Sort by Brand ascending, then Year ascending
5. Plot as line chart (one line per Brand)

---

## 3. CSV Column Reference

### Complete List of CSV Columns Used

| Column Name | Used In | Purpose |
|------------|---------|---------|
| `Year` | Filters, YoY Growth | Filter and group by year |
| `Month_Name` | Filters | Filter by month |
| `Business` | Filters, Brand by Business | Filter and group by business |
| `Channel` | Filters | Filter by channel |
| `Category` | Filters | Filter by category (case-insensitive) |
| `Brand` | Filters, All Charts | Filter and group by brand |
| `Revenue` | All metrics and charts | Sales amount (currency) |
| `Gross_Profit` | All metrics and charts | Gross profit amount (currency) |
| `Units` | Brand Performance | Cases/units sold (numeric) |

---

## 4. Common Calculations and Formulas

### 4.1 Active Brands Count
```
Active Brands = COUNT(DISTINCT Brand) WHERE Brand IS NOT NULL AND Brand != "Unknown" AND Brand != "" AND Brand.lower() NOT IN ["unknown", "none", "null", ""]
```

**Important Notes**:
- Counts all distinct brands that have data
- Does NOT require revenue > 0
- Excludes only "Unknown", null, empty, or invalid brand names
- Case-insensitive exclusion check

### 4.2 Brand Performance Aggregation
```
For each Brand:
  Revenue = SUM(Revenue)
  Gross_Profit = SUM(Gross_Profit)
  Units = SUM(Units)
```

### 4.3 Brand by Business Aggregation
```
For each Brand-Business combination:
  Revenue = SUM(Revenue)
  Gross_Profit = SUM(Gross_Profit)
```

### 4.4 Brand YoY Aggregation
```
For each Brand-Year combination:
  Revenue = SUM(Revenue)
```

---

## 5. Filtering Logic

### 5.1 Category Filter (Case-Insensitive)
- **Column**: `Category` (string)
- **Filter Type**: `$regex` with case-insensitive option
- **Normalization**: Category names are normalized to title case
- **Example**: If categories = "Category1,Category2", filter uses regex: `Category IN ["Category1", "Category2"]` (case-insensitive)
- **CSV**: Filter rows where `Category` column matches selected categories (case-insensitive)

### 5.2 Other Filters
- Same as Business Compass screen (Year, Month, Business, Channel, Brand)

---

## 6. Testing Checklist

### 6.1 KPI Verification
- [ ] Total Revenue: Sum `Revenue` column
- [ ] Total Gross Profit: Sum `Gross_Profit` column
- [ ] Active Brands: Count distinct `Brand` values (excluding "Unknown", null, empty)
- [ ] Avg. Margin: `(Total Gross Profit / Total Revenue) × 100`

### 6.2 Chart Verification
- [ ] Top Brands by Revenue: Group by `Brand`, sum Revenue, Gross_Profit, Units, sort by Revenue descending, top 15
- [ ] Brand Performance by Business: Group by `Brand` AND `Business`, sum Revenue, Gross_Profit
- [ ] Brand YoY Growth: Group by `Brand` AND `Year`, sum Revenue

### 6.3 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Business filter: Only includes data from selected businesses
- [ ] Channel filter: Only includes data from selected channels
- [ ] Category filter: Only includes data from selected categories (case-insensitive)
- [ ] Brand filter: Only includes data from selected brands
- [ ] Combined filters: AND logic (all must match)

### 6.4 Edge Cases
- [ ] Null/empty values treated as 0
- [ ] Division by zero protection (returns 0)
- [ ] Active brands count excludes "Unknown", null, empty, or invalid names
- [ ] Category filter is case-insensitive
- [ ] Brand names are case-sensitive

---

## 7. Quick Reference: Chart → CSV Columns

| Chart Name | Primary Grouping Column | Value Column | Additional Columns |
|------------|------------------------|--------------|-------------------|
| Top Brands by Revenue | `Brand` | `Revenue` | `Gross_Profit`, `Units` |
| Brand Performance by Business | `Brand` + `Business` | `Revenue` | `Gross_Profit` |
| Brand YoY Growth | `Brand` + `Year` | `Revenue` | None |

---

## 8. Notes for Testers

### 8.1 Active Brands Count
- **Important**: This counts all distinct brands that have data, NOT just brands with revenue > 0
- Excludes only "Unknown", null, empty, or invalid brand names
- Case-insensitive exclusion check (e.g., "unknown" = "Unknown")

### 8.2 Category Filter
- Category filter is case-insensitive
- Category names are normalized to title case
- Example: "category1" matches "Category1" in the data

### 8.3 Brand Performance
- Top 15 brands are shown by default
- Sorted by revenue descending
- All brands with data are included in calculations (not just top 15)

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

