# Categories Screen - Formulas, Column Names, and Calculations

## Document Purpose
This document provides a comprehensive reference for all formulas, column names, and calculations used in the Categories screen. Use this document to verify values against the CSV/business data file.

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
- **Sub-Category Filter**: Filters by `Sub_Cat` or `Sub_Category` column (string)

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

### 1.3 Active Categories
**Display**: Large number card

**Formula**:
```
Active Categories = COUNT(DISTINCT Category) WHERE Category != "Unknown"
```

**MongoDB Aggregation**:
```javascript
// Get distinct categories with same filters (excluding Category filter itself)
{
  '$group': {'_id': '$Category'}
}
// Normalize and deduplicate (case-insensitive)
// Count categories excluding "Unknown"
active_categories = COUNT(normalized_categories WHERE category != "Unknown")
```

**CSV Verification**:
- Column: `Category`
- Action: Count distinct category names
- Filter: Apply all filters except Category filter
- Normalization: Category names are normalized to title case (case-insensitive)
- Exclusions: Exclude "Unknown" categories
- Deduplication: Merge categories with same name (different case)

**Important**: 
- Category names are normalized to title case (case-insensitive matching)
- Categories with same name but different case are merged
- Excludes only "Unknown" categories

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

### 2.1 Category Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `category_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Category',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}},
    'Units': {'$sum': {'$toDouble': {'$ifNull': ['$Units', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
// Normalize and merge categories with same name (different case)
```

**CSV Columns Used**:
- `Category` - Groups by this field
- `Revenue` - Sum for each category
- `Gross_Profit` - Sum for each category
- `Units` - Sum for each category

**Category Normalization**:
- Category names are normalized to title case
- Categories with same name but different case are merged
- Example: "category1" and "Category1" are merged into "Category1"

**Chart Display**:
- **X-Axis**: `Category` (Normalized category names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Sort**: By revenue descending

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Sub-Category if selected
2. Group by `Category`
3. For each category:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. **Normalize category names** to title case
5. **Merge duplicate categories** (same name, different case)
6. Sort by Revenue descending

---

### 2.2 Sub-Category Performance (Bar Chart)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `subcategory_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': {
      'Sub_Cat': {'$ifNull': ['$Sub_Cat', '$Sub_Category']},
      'Category': '$Category'
    },
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}},
    'Units': {'$sum': {'$toDouble': {'$ifNull': ['$Units', 0]}}}
  },
  '$sort': {'Revenue': -1}
}
```

**CSV Columns Used**:
- `Sub_Cat` or `Sub_Category` - Groups by this field (uses Sub_Cat if available, otherwise Sub_Category)
- `Category` - Groups by this field (with Sub-Category)
- `Revenue` - Sum for each Sub-Category-Category combination
- `Gross_Profit` - Sum for each Sub-Category-Category combination
- `Units` - Sum for each Sub-Category-Category combination

**Sub-Category Field Handling**:
- Uses `Sub_Cat` field if available
- Falls back to `Sub_Category` field if `Sub_Cat` is null/empty
- Formula: `$ifNull(['$Sub_Cat', '$Sub_Category'])`

**Chart Display**:
- **X-Axis**: `Sub_Category` (Sub-category names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Sort**: By revenue descending

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Sub-Category if selected
2. Group by `Sub_Cat` (or `Sub_Category` if Sub_Cat is null) AND `Category`
3. For each Sub-Category-Category combination:
   - Sum `Revenue`
   - Sum `Gross_Profit`
   - Sum `Units`
4. Sort by Revenue descending

---

### 2.3 Board Category Performance (Bar Chart - Optional)

**Chart Type**: Vertical Bar Chart  
**Data Source**: `board_category_performance`

**MongoDB Aggregation**:
```javascript
{
  '$group': {
    '_id': '$Board_Category',
    'Revenue': {'$sum': {'$toDouble': {'$ifNull': ['$Revenue', 0]}}},
    'Gross_Profit': {'$sum': {'$toDouble': {'$ifNull': ['$Gross_Profit', 0]}}}
  },
  '$match': {'_id': {'$ne': None}},
  '$sort': {'Revenue': -1}
}
```

**CSV Columns Used**:
- `Board_Category` - Groups by this field
- `Revenue` - Sum for each board category
- `Gross_Profit` - Sum for each board category

**Chart Display**:
- **X-Axis**: `Board_Category` (Board category names)
- **Y-Axis**: `Revenue` (Total revenue)
- **Filter**: Excludes null board categories
- **Sort**: By revenue descending

**CSV Verification Steps**:
1. Filter data by Year/Month/Business/Channel/Category/Sub-Category if selected
2. Filter out rows where `Board_Category` is null
3. Group by `Board_Category`
4. For each board category:
   - Sum `Revenue`
   - Sum `Gross_Profit`
5. Sort by Revenue descending

**Note**: This chart may not always be displayed if `Board_Category` data is not available.

---

## 3. CSV Column Reference

### Complete List of CSV Columns Used

| Column Name | Used In | Purpose |
|------------|---------|---------|
| `Year` | Filters | Filter by year |
| `Month_Name` | Filters | Filter by month |
| `Business` | Filters | Filter by business |
| `Channel` | Filters | Filter by channel |
| `Category` | Filters, Category Performance | Filter and group by category (case-insensitive) |
| `Sub_Cat` | Filters, Sub-Category Performance | Filter and group by sub-category (primary field) |
| `Sub_Category` | Filters, Sub-Category Performance | Filter and group by sub-category (fallback field) |
| `Board_Category` | Board Category Performance | Group by board category |
| `Revenue` | All metrics and charts | Sales amount (currency) |
| `Gross_Profit` | All metrics and charts | Gross profit amount (currency) |
| `Units` | Category Performance, Sub-Category Performance | Cases/units sold (numeric) |

---

## 4. Common Calculations and Formulas

### 4.1 Category Normalization
```
Category Name Normalization:
  1. Convert to title case (first letter uppercase, rest lowercase)
  2. Merge categories with same normalized name
  3. Example: "category1" and "Category1" → "Category1"
```

**Normalization Function**:
- Converts category names to title case
- Merges duplicate categories (case-insensitive)
- Ensures consistent category names across the dataset

### 4.2 Sub-Category Field Selection
```
Sub-Category Field = IF Sub_Cat IS NOT NULL THEN Sub_Cat ELSE Sub_Category
```

**Field Priority**:
1. Use `Sub_Cat` if available (not null/empty)
2. Fall back to `Sub_Category` if `Sub_Cat` is null/empty
3. MongoDB: `{'$ifNull': ['$Sub_Cat', '$Sub_Category']}`

### 4.3 Active Categories Count
```
Active Categories = COUNT(DISTINCT normalized_Category) WHERE normalized_Category != "Unknown"
```

**Important Notes**:
- Categories are normalized to title case before counting
- Duplicate categories (different case) are merged
- Excludes only "Unknown" categories
- Count is based on filtered data (excluding Category filter itself)

---

## 5. Filtering Logic

### 5.1 Category Filter (Case-Insensitive)
- **Column**: `Category` (string)
- **Filter Type**: `$regex` with case-insensitive option
- **Normalization**: Category names are normalized to title case
- **Example**: If categories = "Category1,Category2", filter uses regex: `Category IN ["Category1", "Category2"]` (case-insensitive)
- **CSV**: Filter rows where `Category` column matches selected categories (case-insensitive)

### 5.2 Sub-Category Filter
- **Columns**: `Sub_Cat` or `Sub_Category` (string)
- **Filter Type**: `$or` with `$in` operator
- **Example**: If sub_categories = "SubCat1,SubCat2", filter: `(Sub_Cat IN ["SubCat1", "SubCat2"] OR Sub_Category IN ["SubCat1", "SubCat2"])`
- **CSV**: Filter rows where `Sub_Cat` OR `Sub_Category` column matches selected sub-categories

### 5.3 Other Filters
- Same as Business Compass screen (Year, Month, Business, Channel)

---

## 6. Testing Checklist

### 6.1 KPI Verification
- [ ] Total Revenue: Sum `Revenue` column
- [ ] Total Gross Profit: Sum `Gross_Profit` column
- [ ] Active Categories: Count distinct normalized `Category` values (excluding "Unknown")
- [ ] Avg. Margin: `(Total Gross Profit / Total Revenue) × 100`

### 6.2 Chart Verification
- [ ] Category Performance: Group by `Category`, normalize names, merge duplicates, sum Revenue, Gross_Profit, Units, sort by Revenue descending
- [ ] Sub-Category Performance: Group by `Sub_Cat` (or `Sub_Category`) AND `Category`, sum Revenue, Gross_Profit, Units, sort by Revenue descending
- [ ] Board Category Performance: Group by `Board_Category`, filter out null, sum Revenue, Gross_Profit, sort by Revenue descending

### 6.3 Filter Verification
- [ ] Year filter: Only includes data from selected years
- [ ] Month filter: Only includes data from selected months
- [ ] Business filter: Only includes data from selected businesses
- [ ] Channel filter: Only includes data from selected channels
- [ ] Category filter: Only includes data from selected categories (case-insensitive)
- [ ] Sub-Category filter: Only includes data from selected sub-categories (checks both Sub_Cat and Sub_Category)
- [ ] Combined filters: AND logic (all must match)

### 6.4 Edge Cases
- [ ] Null/empty values treated as 0
- [ ] Division by zero protection (returns 0)
- [ ] Category normalization (case-insensitive merging)
- [ ] Sub-Category field selection (Sub_Cat vs Sub_Category)
- [ ] Active categories count excludes "Unknown" and uses normalized names

---

## 7. Quick Reference: Chart → CSV Columns

| Chart Name | Primary Grouping Column | Value Column | Additional Columns |
|------------|------------------------|--------------|-------------------|
| Category Performance | `Category` (normalized) | `Revenue` | `Gross_Profit`, `Units` |
| Sub-Category Performance | `Sub_Cat` (or `Sub_Category`) + `Category` | `Revenue` | `Gross_Profit`, `Units` |
| Board Category Performance | `Board_Category` | `Revenue` | `Gross_Profit` |

---

## 8. Notes for Testers

### 8.1 Category Normalization
- **Important**: Category names are normalized to title case (case-insensitive)
- Categories with same name but different case are merged
- Example: "category1" and "Category1" are treated as the same category
- Normalization ensures consistent category names across the dataset

### 8.2 Sub-Category Field Handling
- Uses `Sub_Cat` field if available
- Falls back to `Sub_Category` field if `Sub_Cat` is null/empty
- Both fields are checked when filtering by sub-category

### 8.3 Active Categories Count
- Counts distinct normalized categories
- Excludes only "Unknown" categories
- Based on filtered data (excluding Category filter itself)
- Ensures count matches what's shown in the filter dropdown

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Maintained By**: Development Team

