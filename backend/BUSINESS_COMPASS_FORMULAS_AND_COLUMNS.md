# Business Compass (Dashboard) - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Business Compass (Dashboard) screen. Use this document to verify values against the CSV/business data file.

---

## Data Source
**Collection**: `business_data` (MongoDB)  
**CSV File**: Business data export

---

## Filtering
All calculations respect the following filters:
- **Year Filter**: Filters by `Year` column (numeric)
- **Month Filter**: Filters by `Month_Name` column (string: "January", "February", etc.)
- **Business Filter**: Filters by `Business` column (string)
- **Channel Filter**: Filters by `Channel` column (string)
- **Brand Filter**: Filters by `Brand` column (string)

**Filter Application**: All aggregations use `match_stage` which includes these filters.

---

## 1. Key Performance Indicators (KPIs) - Top Row

### 1.1 Total Sales (Revenue)
**Display**: Large number card (e.g., "€59.0M")

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
- Filter: Apply Year/Month/Business/Channel/Brand filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

**Notes**:
- Sums all revenue amounts
- Currency format: € (Euros)

---

### 1.2 Gross Profit
**Display**: Large number card (e.g., "€18.0M")

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
- Filter: Apply Year/Month/Business/Channel/Brand filters if selected
- Null Handling: Treat null/empty as 0
- Currency: Values are in Euros (€)

**Notes**:
- Sums all gross profit amounts
- Currency format: € (Euros)

---

### 1.3 Cases Sold (Units)
**Display**: Large number card (e.g., "16.9k")

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
- Filter: Apply Year/Month/Business/Channel/Brand filters if selected
- Null Handling: Treat null/empty as 0

**Notes**:
- Sums all units/cases sold
- Format: Whole numbers (e.g., 16,900 cases)

---

### 1.4 Avg. Margin
**Display**: Large number card (e.g., "30.4%")

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
- Step 2: Calculate Total Gross Profit (see 1.2)
- Step 3: Divide Total Gross Profit by Total Sales
- Step 4: Multiply by 100 to get percentage
- If Total Sales = 0, then Avg. Margin = 0
- Format: Percentage with 1 decimal place (e.g., 30.4%)

**Notes**:
- Division by zero protection: Returns 0 if no revenue
- Percentage format: Shows as "X.X%"

---

### 1.5 YoY Growth (Year-over-Year Growth)
**Display**: Percentage below Total Sales card (e.g., "+15.2%")

**Formula**:
```
YoY Growth (%) = ((Current Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100
```

**Calculation Steps**:
1. Get yearly performance data (grouped by Year)
2. Sort years in descending order
3. Get latest year (first in sorted list)
4. Get previous year (second in sorted list)
5. Calculate: `((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) × 100`

**MongoDB Aggregation**:
```javascript
// Yearly performance aggregation
{
  '$group': {
    '_id': '$Year',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}}
  }
}
// Sort by Year descending, then calculate growth
```

**CSV Verification**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Group by `Year`
3. For each year: Sum `Revenue`
4. Sort by Year descending
5. Get latest year and previous year
6. Calculate: `((Latest Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100`
7. If Previous Year Revenue = 0, then YoY Growth = 0

**Notes**:
- Requires at least 2 years of data
- Shows positive growth as "+X.X%" and negative as "-X.X%"
- Color: Green for positive, red for negative

---

### 1.6 Revenue Growth (Period-over-Period)
**Display**: Percentage below Total Sales card (e.g., "+8.2%")

**Formula**:
```
Revenue Growth (%) = ((Current Period Revenue - Previous Period Revenue) / Previous Period Revenue) × 100
```

**Calculation Steps**:
1. Get monthly trend data (grouped by Month_Name)
2. Sort months chronologically
3. Get current period (last month in sorted list)
4. Get previous period (second-to-last month)
5. Calculate: `((currentPeriod.Revenue - previousPeriod.Revenue) / previousPeriod.Revenue) × 100`

**MongoDB Aggregation**:
```javascript
// Monthly trend aggregation (for current year)
{
  '$match': {**query, 'Year': current_year},
  '$group': {
    '_id': '$Month_Name',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}}
  }
}
// Sort by month order, then calculate growth
```

**CSV Verification**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Filter to current year (max year in data)
3. Group by `Month_Name`
4. For each month: Sum `Revenue`
5. Sort months chronologically (January, February, ..., December)
6. Get current month (last in sorted list) and previous month
7. Calculate: `((Current Month Revenue - Previous Month Revenue) / Previous Month Revenue) × 100`
8. If Previous Month Revenue = 0, then Revenue Growth = 0

**Notes**:
- Requires at least 2 months of data
- Shows positive growth as "+X.X%" and negative as "-X.X%"
- Color: Green for positive, red for negative

---

### 1.7 Profit Growth (Period-over-Period)
**Display**: Percentage below Gross Profit card (e.g., "+5.1%")

**Formula**:
```
Profit Growth (%) = ((Current Period Gross Profit - Previous Period Gross Profit) / Previous Period Gross Profit) × 100
```

**Calculation Steps**:
Same as Revenue Growth (1.6), but using `Gross_Profit` instead of `Revenue`

**CSV Verification**:
Same as Revenue Growth, but use `Gross_Profit` column instead of `Revenue`

**Notes**:
- Same logic as Revenue Growth, but for profit
- Shows positive growth as "+X.X%" and negative as "-X.X%"
- Color: Green for positive, red for negative

---

### 1.8 Units Growth (Period-over-Period)
**Display**: Percentage below Cases Sold card (e.g., "-2.3%")

**Formula**:
```
Units Growth (%) = ((Current Period Units - Previous Period Units) / Previous Period Units) × 100
```

**Calculation Steps**:
Same as Revenue Growth (1.6), but using `Units` instead of `Revenue`

**CSV Verification**:
Same as Revenue Growth, but use `Units` column instead of `Revenue`

**Notes**:
- Same logic as Revenue Growth, but for units
- Shows positive growth as "+X.X%" and negative as "-X.X%"
- Color: Green for positive, red for negative

---

### 1.9 Market Share
**Display**: Large number card (e.g., "28.5%")

**Formula**:
```
Market Share (%) = (Total Revenue / Total Market Revenue) × 100
```

**Calculation Steps**:
1. Get business performance data (grouped by Business)
2. Sum revenue for all businesses: `totalMarketRevenue = SUM(all businesses Revenue)`
3. Calculate: `(totalRevenue / totalMarketRevenue) × 100`

**MongoDB Aggregation**:
```javascript
// Business performance aggregation
{
  '$group': {
    '_id': '$Business',
    'Revenue': {'$sum': {'$toDouble': '$Revenue'}}
  }
}
// Then sum all business revenues
totalMarketRevenue = SUM(all businesses Revenue)
Market Share = (totalRevenue / totalMarketRevenue) × 100
```

**CSV Verification**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Group by `Business`
3. For each business: Sum `Revenue`
4. Sum all business revenues: `totalMarketRevenue = SUM(all businesses Revenue)`
5. Calculate: `(totalRevenue / totalMarketRevenue) × 100`
6. If totalMarketRevenue = 0, then Market Share = 0

**Notes**:
- Relative market share within the dataset
- Shows as percentage with 1 decimal place (e.g., 28.5%)

---

### 1.10 Operational Efficiency
**Display**: Large number card (e.g., "92%")

**Formula**:
```
Operational Efficiency (%) = Avg. Margin = (Total Gross Profit / Total Sales) × 100
```

**Calculation Steps**:
Same as Avg. Margin (1.4)

**CSV Verification**:
Same as Avg. Margin (1.4)

**Notes**:
- Currently uses profit margin as a proxy for operational efficiency
- Same calculation as Avg. Margin
- Shows as percentage with 1 decimal place (e.g., 92.0%)

---

### 1.11 New Customers
**Display**: Large number card (e.g., "245")

**Formula**:
```
New Customers = 0 (Not available in business_data)
```

**Current Status**:
- Currently hardcoded to 0
- Customer data is not available in `business_data` collection
- Would need to fetch from customer analysis endpoint or customer data collection

**Notes**:
- TODO: Fetch from customer data if available
- May need to use `/analytics/customer-analysis` endpoint

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
1. Filter data by Year/Month/Business/Channel/Brand if selected
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
1. Filter data by Year/Month/Business/Channel/Brand if selected
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
1. Filter data by Year/Month/Business/Channel/Brand if selected
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

### 2.4 Business vs Cases (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `business_performance`

**MongoDB Aggregation**:
Same as Business Performance (2.2)

**CSV Columns Used**:
- `Business` - Groups by this field
- `Units` - Sum for each business

**Chart Display**:
- **X-Axis**: `Business` (Business names)
- **Y-Axis**: `Units` (Total cases/units)
- **Bars**: Height represents units amount
- **Filter**: Only shows businesses with Revenue > 0

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Group by `Business`
3. For each business: Sum `Units`
4. Filter out businesses with Revenue = 0
5. Sort by Revenue descending (same order as Business Performance chart)

---

### 2.5 Business vs Sales (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `business_performance`

**MongoDB Aggregation**:
Same as Business Performance (2.2)

**CSV Columns Used**:
- `Business` - Groups by this field
- `Revenue` - Sum for each business

**Chart Display**:
- **X-Axis**: `Business` (Business names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Bars**: Height represents revenue amount
- **Filter**: Only shows businesses with Revenue > 0

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Group by `Business`
3. For each business: Sum `Revenue`
4. Filter out businesses with Revenue = 0
5. Sort by Revenue descending

---

### 2.6 Business vs Gross Profit (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `business_performance`

**MongoDB Aggregation**:
Same as Business Performance (2.2)

**CSV Columns Used**:
- `Business` - Groups by this field
- `Gross_Profit` - Sum for each business

**Chart Display**:
- **X-Axis**: `Business` (Business names)
- **Y-Axis**: `Gross_Profit` (Total gross profit)
- **Bars**: Height represents profit amount
- **Filter**: Only shows businesses with Revenue > 0

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Brand if selected
2. Group by `Business`
3. For each business: Sum `Gross_Profit`
4. Filter out businesses with Revenue = 0
5. Sort by Revenue descending (same order as Business Performance chart)

---

### 2.7 Channel Distribution (Donut Chart)

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
1. Filter data by Year/Month/Business/Channel/Brand if selected
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
| `Business` | Filters, Business Performance Charts | Filter and group by business |
| `Channel` | Filters, Channel Distribution | Filter and group by channel |
| `Brand` | Filters | Filter by brand |
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
- Used for Avg. Margin, Market Share, Channel Distribution percentages
- Example: `(totalProfit / totalRevenue) × 100`

### 4.3 Growth Calculation
```
Growth (%) = ((Current - Previous) / Previous) × 100
```
- Used for YoY Growth, Revenue Growth, Profit Growth, Units Growth
- Division by zero protection: Returns 0 if Previous = 0

### 4.4 Month Abbreviation
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

### 5.5 Brand Filter
- **Column**: `Brand` (string)
- **Filter Type**: `$in` operator
- **Example**: If brands = "Brand1,Brand2", filter: `Brand IN ["Brand1", "Brand2"]`
- **CSV**: Filter rows where `Brand` column matches selected brands

### 5.6 Combined Filters
- Filters are combined with AND logic
- Example: Year=2024 AND Month=January AND Business=Business1
- All aggregations respect these filters via `match_stage`

---

## 6. Testing Checklist

### 6.1 KPI Verification
- [ ] Total Sales: Sum `Revenue` column
- [ ] Gross Profit: Sum `Gross_Profit` column
- [ ] Cases Sold: Sum `Units` column
- [ ] Avg. Margin: `(Total Gross Profit / Total Sales) × 100`
- [ ] YoY Growth: `((Latest Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100`
- [ ] Revenue Growth: `((Current Month Revenue - Previous Month Revenue) / Previous Month Revenue) × 100`
- [ ] Profit Growth: `((Current Month Gross Profit - Previous Month Gross Profit) / Previous Month Gross Profit) × 100`
- [ ] Units Growth: `((Current Month Units - Previous Month Units) / Previous Month Units) × 100`
- [ ] Market Share: `(Total Revenue / Total Market Revenue) × 100`
- [ ] Operational Efficiency: Same as Avg. Margin

### 6.2 Chart Verification
- [ ] Yearly Performance: Group by `Year`, sum Revenue, Gross_Profit, Units
- [ ] Business Performance: Group by `Business`, sum Revenue, Gross_Profit, Units
- [ ] Monthly Trend: Filter to current year, group by `Month_Name`, sum Revenue, Gross_Profit, Units
- [ ] Business vs Cases: Group by `Business`, sum Units
- [ ] Business vs Sales: Group by `Business`, sum Revenue
- [ ] Business vs Gross Profit: Group by `Business`, sum Gross_Profit
- [ ] Channel Distribution: Group by `Channel`, sum Revenue

### 6.3 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Business filter: Only includes data from selected businesses
- [ ] Channel filter: Only includes data from selected channels
- [ ] Brand filter: Only includes data from selected brands
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
| Business vs Cases | `Business` | `Units` | `Revenue` (for filtering) |
| Business vs Sales | `Business` | `Revenue` | `Gross_Profit`, `Units` |
| Business vs Gross Profit | `Business` | `Gross_Profit` | `Revenue` (for filtering) |
| Channel Distribution | `Channel` | `Revenue` | `Gross_Profit`, `Units` |

---

## 8. Notes for Testers

### 8.1 Data Filtering
- All calculations respect Year, Month, Business, Channel, and Brand filters
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
- Growth percentages: Rounded to 1 decimal place

### 8.5 Month Formatting
- Full month names in data: "January", "February", etc.
- Display format: Abbreviated "Jan", "Feb", "Mar", etc.
- Sort order: Chronological (January first, December last)

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

