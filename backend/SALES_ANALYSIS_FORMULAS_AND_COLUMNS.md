# Sales Analysis Screen - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Sales Analysis screen. Use this document to verify values against the CSV/business data file.

---

## Data Source
**Collection**: `business_data` (MongoDB)  
**CSV File**: Business data export

**Note**: Sales Analysis screen uses the same endpoint as Business Compass (`/analytics/executive-overview`), so the calculations are identical. This document provides a focused reference for the Sales Analysis screen.

---

## Filtering
All calculations respect the following filters:
- **Year Filter**: Filters by `Year` column (numeric)
- **Month Filter**: Filters by `Month_Name` column (string)
- **Business Filter**: Filters by `Business` column (string)
- **Channel Filter**: Filters by `Channel` column (string)

**Filter Application**: All aggregations use `match_stage` which includes these filters.

---

## 1. Key Performance Indicators (KPIs) - Top Row

### 1.1 Total Sales (Revenue)
**Display**: Large number card

**Formula**:
```
Total Sales = SUM(Revenue)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'total_revenue': {'$sum': {'$toDouble': '$Revenue'}}
  }
}
```

**CSV Verification**:
- Column: `Revenue`
- Action: Sum all values in the Revenue column
- Filter: Apply Year/Month/Business/Channel filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

---

### 1.2 Gross Profit
**Display**: Large number card

**Formula**:
```
Gross Profit = SUM(Gross_Profit)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'total_profit': {'$sum': {'$toDouble': '$Gross_Profit'}}
  }
}
```

**CSV Verification**:
- Column: `Gross_Profit`
- Action: Sum all values in the Gross_Profit column
- Filter: Apply Year/Month/Business/Channel filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

---

### 1.3 Cases Sold (Units)
**Display**: Large number card

**Formula**:
```
Cases Sold = SUM(Units)
```

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': None,
    'total_units': {'$sum': {'$toDouble': '$Units'}}
  }
}
```

**CSV Verification**:
- Column: `Units`
- Action: Sum all values in the Units column
- Filter: Apply Year/Month/Business/Channel filters if selected
- Null Handling: Treat null/empty as 0

---

### 1.4 Avg. Margin
**Display**: Large number card

**Formula**:
```
Avg. Margin (%) = (Total Gross Profit / Total Sales) × 100
```

**MongoDB Aggregation**:
```javascript
// First calculate totals
{
  '$group': {
    '_id': None,
    'total_revenue': {'$sum': {'$toDouble': '$Revenue'}},
    'total_profit': {'$sum': {'$toDouble': '$Gross_Profit'}}
  }
}
// Then calculate margin
Avg. Margin = (total_profit / total_revenue) × 100
```

**CSV Verification**:
- Step 1: Calculate Total Sales (see 1.1)
- Step 2: Calculate Gross Profit (see 1.2)
- Step 3: Divide Gross Profit by Total Sales
- Step 4: Multiply by 100 to get percentage
- If Total Sales = 0, then Avg. Margin = 0
- Format: Percentage with 1 decimal place

---

## 2. Charts and Visualizations

### 2.1 Yearly Performance (Line Chart)

**Chart Type**: Line Chart  
**Data Source**: `yearly_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Year',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}},
    'Gross_Profit': {'$sum': {'$toDouble': '$Gross_Profit'}},
    'Units': {'$sum': {'$toDouble': '$Units'}}
  }
}
// Sort by Year ascending
```

**CSV Columns Used**:
- `Year` - Groups by this field
- `Revenue` - Sum for each year
- `Gross_Profit` - Sum for each year
- `Units` - Sum for each year

**Chart Display**:
- **X-Axis**: `Year` (e.g., 2023, 2024, 2025)
- **Y-Axis (Left)**: Revenue (for Revenue line)
- **Y-Axis (Right)**: Units (for Units line)
- **Lines**: 
  - Revenue line (one color)
  - Units line (different color, right axis)

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel if selected
2. Group by `Year`
3. For each year:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. Sort by Year ascending
5. Plot Revenue and Units as separate lines

---

### 2.2 Business Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `business_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Business',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}},
    'Gross_Profit': {'$sum': {'$toDouble': '$Gross_Profit'}},
    'Units': {'$sum': {'$toDouble': '$Units'}}
  }
}
// Sort by Revenue descending
```

**CSV Columns Used**:
- `Business` - Groups by this field
- `Revenue` - Sum for each business
- `Gross_Profit` - Sum for each business
- `Units` - Sum for each business

**Chart Display**:
- **X-Axis**: `Business` (Business names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Bars**: Height represents revenue amount
- **Filter**: Only shows businesses with Revenue > 0

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel if selected
2. Group by `Business`
3. For each business:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. Filter out businesses with Revenue = 0
5. Sort by Revenue descending

---

### 2.3 Monthly Trend (Line Chart)

**Chart Type**: Line Chart  
**Data Source**: `monthly_trend`

**MongoDB Aggregation**:
```javascript
// Get current year (max year in data)
{
  '$group': {'_id': None, 'maxYear': {'$max': {'$toDouble': '$Year'}}}
}

// Monthly trend for current year
{
  '$match': {**query, 'Year': current_year},
  '$group': {
    '_id': '$Month_Name',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}},
    'Gross_Profit': {'$sum': {'$toDouble': '$Gross_Profit'}},
    'Units': {'$sum': {'$toDouble': '$Units'}}
  }
}
// Sort by month order (January, February, ..., December)
```

**CSV Columns Used**:
- `Year` - Filters to current year (max year)
- `Month_Name` - Groups by this field (e.g., "January", "February")
- `Revenue` - Sum for each month
- `Gross_Profit` - Sum for each month
- `Units` - Sum for each month

**Chart Display**:
- **X-Axis**: Month names (Jan, Feb, Mar, ..., Dec)
- **Y-Axis (Left)**: Revenue (for Revenue line)
- **Y-Axis (Right)**: Units (for Units line)
- **Lines**: 
  - Revenue line (one color)
  - Units line (different color, right axis)

**Month Order**:
- Chronological order: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
- Month names are abbreviated: "January" → "Jan", "February" → "Feb", etc.

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel if selected
2. Get max year: `current_year = MAX(Year)`
3. Filter to current year: `Year = current_year`
4. Group by `Month_Name`
5. For each month:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
6. Sort months chronologically (January first, December last)
7. Format month names as abbreviations (Jan, Feb, Mar, etc.)
8. Plot Revenue and Units as separate lines

---

### 2.4 Channel Distribution (Donut Chart)

**Chart Type**: Donut Chart  
**Data Source**: `channel_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Channel',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}},
    'Gross_Profit': {'$sum': {'$toDouble': '$Gross_Profit'}},
    'Units': {'$sum': {'$toDouble': '$Units'}}
  }
}
```

**CSV Columns Used**:
- `Channel` - Groups by this field
- `Revenue` - Sum for each channel

**Chart Display**:
- **Labels**: `Channel` (Channel names)
- **Values**: `Revenue` (Total revenue per channel)
- **Tooltip**: Shows revenue with percentage of total

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel if selected
2. Group by `Channel`
3. For each channel: Sum `Revenue`
4. Calculate percentage: `(channel_revenue / total_revenue) × 100`
5. Display as donut chart with percentages

---

## 3. CSV Column Reference

### Complete List of CSV Columns Used

| Column Name | Used In | Purpose |
|------------|---------|---------|
| `Year` | Filters, Yearly Performance, Monthly Trend | Filter and group by year |
| `Month_Name` | Filters, Monthly Trend | Filter and group by month |
| `Business` | Filters, Business Performance | Filter and group by business |
| `Channel` | Filters, Channel Distribution | Filter and group by channel |
| `Revenue` | All metrics and charts | Sales amount (currency) |
| `Gross_Profit` | All metrics and charts | Gross profit amount (currency) |
| `Units` | All metrics and charts | Cases/units sold (numeric) |

---

## 4. Common Calculations and Formulas

### 4.1 Sum with Null Handling
```
Sum = SUM(column_value) where null/empty = 0
```
- MongoDB: `{'$sum': {'$toDouble': '$column'}}`
- CSV: Sum all non-null values, treat null/empty as 0

### 4.2 Percentage Calculation
```
Percentage = (Part / Total) × 100
```
- Used for Avg. Margin, Channel Distribution percentages
- Example: `(totalProfit / totalRevenue) × 100`

### 4.3 Month Abbreviation
```
Full Month Name → Abbreviation
"January" → "Jan"
"February" → "Feb"
"March" → "Mar"
... (and so on)
```

---

## 5. Filtering Logic

### 5.1 Year Filter
- **Column**: `Year` (numeric)
- **Filter Type**: `$in` operator
- **Example**: If years = "2023,2024", filter: `Year IN [2023, 2024]`
- **CSV**: Filter rows where `Year` column matches selected years

### 5.2 Month Filter
- **Column**: `Month_Name` (string: "January", "February", etc.)
- **Filter Type**: `$in` operator
- **Example**: If months = "January,February", filter: `Month_Name IN ["January", "February"]`
- **CSV**: Filter rows where `Month_Name` column matches selected months

### 5.3 Business Filter
- **Column**: `Business` (string)
- **Filter Type**: `$in` operator or complex business filter
- **Example**: If businesses = "Business1,Business2", filter: `Business IN ["Business1", "Business2"]`
- **CSV**: Filter rows where `Business` column matches selected businesses

### 5.4 Channel Filter
- **Column**: `Channel` (string)
- **Filter Type**: `$in` operator
- **Example**: If channels = "Channel1,Channel2", filter: `Channel IN ["Channel1", "Channel2"]`
- **CSV**: Filter rows where `Channel` column matches selected channels

### 5.5 Combined Filters
- Filters are combined with AND logic
- Example: Year=2024 AND Month=January AND Business=Business1
- All aggregations respect these filters via `match_stage`

---

## 6. Testing Checklist

### 6.1 KPI Verification
- [ ] Total Sales: Sum `Revenue` column
- [ ] Gross Profit: Sum `Gross_Profit` column
- [ ] Cases Sold: Sum `Units` column
- [ ] Avg. Margin: `(Gross Profit / Total Sales) × 100`

### 6.2 Chart Verification
- [ ] Yearly Performance: Group by `Year`, sum Revenue, Gross_Profit, Units
- [ ] Business Performance: Group by `Business`, sum Revenue, Gross_Profit, Units
- [ ] Monthly Trend: Filter to current year, group by `Month_Name`, sum Revenue, Gross_Profit, Units
- [ ] Channel Distribution: Group by `Channel`, sum Revenue

### 6.3 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Business filter: Only includes data from selected businesses
- [ ] Channel filter: Only includes data from selected channels
- [ ] Combined filters: AND logic (all must match)

### 6.4 Edge Cases
- [ ] Null/empty values treated as 0
- [ ] Division by zero protection (returns 0)
- [ ] Month abbreviation formatting
- [ ] Year sorting (ascending for charts)
- [ ] Business filtering (only Revenue > 0)

---

## 7. Quick Reference: Chart → CSV Columns

| Chart Name | Primary Grouping Column | Value Column | Additional Columns |
|------------|------------------------|--------------|-------------------|
| Yearly Performance | `Year` | `Revenue`, `Units` | `Gross_Profit` |
| Business Performance | `Business` | `Revenue` | `Gross_Profit`, `Units` |
| Monthly Trend | `Month_Name` (current year) | `Revenue`, `Units` | `Gross_Profit` |
| Channel Distribution | `Channel` | `Revenue` | `Gross_Profit`, `Units` |

---

## 8. Notes for Testers

### 8.1 Data Filtering
- All calculations respect Year, Month, Business, and Channel filters
- If no filters selected, all data is included
- Filters are applied at the aggregation level (not after)

### 8.2 Null Handling
- Null/empty values are treated as 0 for numeric calculations
- Null values are excluded from grouping

### 8.3 Currency
- All revenue and profit values are in Euros (€)
- Format: €X,XXX.XX or €X.XXk or €X.XXM

### 8.4 Rounding
- Percentages: Rounded to 1 decimal place (e.g., 30.4%)
- Currency: Formatted with appropriate precision

### 8.5 Month Formatting
- Full month names in data: "January", "February", etc.
- Display format: Abbreviated "Jan", "Feb", "Mar", etc.
- Sort order: Chronological (January first, December last)

### 8.6 Relationship to Business Compass
- Sales Analysis screen uses the same endpoint as Business Compass
- Calculations are identical to Business Compass screen
- Refer to Business Compass documentation for detailed formulas

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

