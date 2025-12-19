# Multi-Dimensional Breakdown Solution

## Problem Statement
The chatbot was not handling complex, multi-dimensional questions properly. When users asked questions like:
- "Compare Q1 gross sales for business Food and KOKA brand in 2023 and 2024"
- "Compare Q1 for Food, KOKA brand, and Grocery channel"

The system was either:
1. Combining data across dimensions (showing totals instead of breakdowns)
2. Not detecting brand/channel filters correctly
3. Removing filters when it shouldn't

## Root Causes

### 1. Month Name Format Mismatch
- **Issue**: Database stores abbreviated months (`Jan`, `Feb`, `Mar`), but query builder was using full names (`January`, `February`, `March`)
- **Fix**: Updated `query_builder.py` to convert full month names to abbreviated format and map quarters to abbreviated months

### 2. Missing Multi-Dimensional Breakdowns
- **Issue**: Quarterly breakdowns only grouped by Year, not by Year + Brand/Channel/Category
- **Fix**: Implemented dynamic dimension detection and multi-dimensional grouping in `data_context.py`

### 3. Incorrect Filter Removal
- **Issue**: Brand filter was being removed when user was filtering BY a specific brand (e.g., "Food and KOKA brand")
- **Fix**: Enhanced comparison detection to distinguish between:
  - "Compare KOKA with other brands" → Remove Brand filter (show all brands)
  - "Compare Q1 for Food and KOKA brand" → Keep Brand filter (filter BY KOKA, compare across years)

## Solution Architecture

### 1. Dynamic Dimension Detection (`data_context.py`)
```python
# Detects which dimensions are requested:
- Year (always for comparison queries)
- Brand (if Brand filter exists and user mentions brand)
- Channel (if Channel filter exists and user mentions channel)
- Category (if Category filter exists and user mentions category)
- Customer (if Customer filter exists and user mentions customer)
```

### 2. Multi-Dimensional Grouping
```python
# For comparison queries with multiple dimensions:
# Groups by: Year + Brand + Channel + Category + Customer (as applicable)
# Example: "Compare Q1 for Food and KOKA brand" → Group by Year + Brand
```

### 3. Smart Filter Preservation (`insights_service.py`)
```python
# Distinguishes between:
- is_asking_for_brands: "top brands", "all brands" → Remove Brand filter
- is_comparing_brand: "KOKA vs other brands" → Remove Brand filter
- is_filtering_by_specific_brand: "Food and KOKA brand" → Keep Brand filter
```

## How It Works

### Example 1: "Compare Q1 gross sales for business Food and KOKA brand in 2023 and 2024"

1. **Query Builder** extracts:
   - Business: Food
   - Brand: KOKA
   - Year: [2023, 2024]
   - Month_Name: [Jan, Feb, Mar] (Q1)

2. **Insights Service** detects:
   - `is_filtering_by_specific_brand = True` (pattern: "and KOKA brand")
   - Keeps Brand filter in `data_context_query`

3. **Data Context** detects dimensions:
   - Year (comparison query)
   - Brand (filter exists + mentioned in message)
   - Creates multi-dimensional breakdown: Group by Year + Brand

4. **Result**: Shows Q1 breakdown by Year and Brand:
   ```
   Q1 Performance by Year and Brand (Jan, Feb, Mar):
     Year: 2023, Brand: KOKA: Revenue €X.XM, Gross Sales €Y.YM, ...
     Year: 2024, Brand: KOKA: Revenue €X.XM, Gross Sales €Y.YM, ...
   ```

### Example 2: "Compare Q1 for Food, KOKA brand, and Grocery channel"

1. **Query Builder** extracts:
   - Business: Food
   - Brand: KOKA
   - Channel: Grocery
   - Year: [2023, 2024] (if mentioned)
   - Month_Name: [Jan, Feb, Mar]

2. **Data Context** detects dimensions:
   - Year (if comparison)
   - Brand
   - Channel
   - Creates breakdown: Group by Year + Brand + Channel

3. **Result**: Shows Q1 breakdown by Year, Brand, and Channel

## Key Features

### 1. Automatic Dimension Detection
- No need to specify breakdown dimensions manually
- System automatically detects from query filters and user message

### 2. Handles Any Combination
- Business + Brand
- Business + Brand + Channel
- Business + Brand + Channel + Category
- Business + Brand + Channel + Category + Customer
- And any other combination

### 3. Works at Any Level
- Business level: "Compare Q1 for Food"
- Brand level: "Compare Q1 for Food and KOKA brand"
- Channel level: "Compare Q1 for Food, KOKA brand, and Grocery channel"
- Category level: "Compare Q1 for Food, KOKA brand, Grocery channel, and Curry category"

## Files Modified

1. **`backend/app/utils/query_builder.py`**:
   - Fixed month name format (full → abbreviated)
   - Fixed quarter mapping (full → abbreviated)
   - Enhanced brand extraction patterns

2. **`backend/app/utils/data_context.py`**:
   - Added dynamic dimension detection
   - Implemented multi-dimensional grouping
   - Enhanced quarterly breakdown for comparisons

3. **`backend/app/services/insights_service.py`**:
   - Enhanced comparison detection
   - Fixed filter preservation logic
   - Improved brand/channel/category detection

## Testing

Test with these questions:
1. "Compare Q1 gross sales for business Food in 2023 and 2024" → Should show Year breakdown
2. "Compare Q1 gross sales for business Food and KOKA brand in 2023 and 2024" → Should show Year + Brand breakdown
3. "Compare Q1 for Food, KOKA brand, and Grocery channel" → Should show Year + Brand + Channel breakdown
4. "Compare Q2 for Kinetica business and Bensons brand" → Should show Year + Brand breakdown

## Future Enhancements

1. Add support for sub-category breakdowns
2. Add support for SKU-level breakdowns
3. Add support for customer group breakdowns
4. Optimize aggregation pipelines for large datasets

