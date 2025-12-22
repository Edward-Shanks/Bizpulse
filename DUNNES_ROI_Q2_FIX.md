# Fix for Dunnes ROI Q2 2024 Query Issue

## Problem

The chatbot is returning €0 for "What is the gross sales for Dunnes ROI customer in Q2 2024?" even though the dashboard clearly shows data exists (€6.4M revenue, €1.7M profit, 250.6k cases for 2024 with Dunnes ROI selected).

## Root Causes Identified

1. **Quarter label check bug**: The quarter label check was looking for full month names ('April', 'May', 'June') but the database uses abbreviated names ('Apr', 'May', 'Jun'), so Q2 label wasn't being added to data context.

2. **Customer extraction might not be matching correctly**: The pattern might be extracting "Dunnes ROI" but the database might have it stored differently.

3. **Customer filter might not be preserved**: Need to ensure Customer filter is not removed from data_context_query like Brand/Business filters are.

## Fixes Applied

### 1. Fixed Quarter Label Check (`data_context.py`)

**Changed from:**
```python
if any(m in ['April', 'May', 'June'] for m in month_filter):
```

**Changed to:**
```python
# CRITICAL: Database uses abbreviated month names (Apr, May, Jun), not full names
if any(m in ['Apr', 'May', 'Jun', 'April', 'May', 'June'] for m in month_filter):
```

**Applied to all quarters:**
- Q1: Now checks for both 'Jan', 'Feb', 'Mar' and 'January', 'February', 'March'
- Q2: Now checks for both 'Apr', 'May', 'Jun' and 'April', 'May', 'June'
- Q3: Now checks for both 'Jul', 'Aug', 'Sep' and 'July', 'August', 'September'
- Q4: Now checks for both 'Oct', 'Nov', 'Dec' and 'October', 'November', 'December'

### 2. Enhanced Customer Extraction Logging

Added better logging to track customer extraction:
- Logs when customer is extracted
- Logs when customer is matched
- Logs when customer is added to query

### 3. Ensured Customer Filter is Preserved

Verified that Customer filter is NOT removed from `data_context_query` (unlike Brand/Business filters which are removed when asking FOR brands/businesses).

## Expected Behavior After Fix

1. **Q2 detection**: When user asks for Q2, the system should:
   - Extract Q2 and map to ['Apr', 'May', 'Jun']
   - Add these months to the query
   - Add Q2 label to data context: "📌 Quarter Interpretation: Q2 = April, May, June..."

2. **Customer extraction**: When user asks "for Dunnes ROI customer", the system should:
   - Extract "Dunnes ROI" from the message
   - Match it to database customer (exact or fuzzy match)
   - Add Customer filter to query: `{'Customer': {'$in': ['Dunnes ROI']}}`

3. **Data context**: Should show:
   - Overall Totals with Customer filter applied
   - Q2 Performance breakdown
   - Customer Performance breakdown showing Dunnes ROI data

4. **Response**: Should show actual gross sales data (not €0) if data exists in database

## Testing

Test with:
```
What is the gross sales for Dunnes ROI customer in Q2 2024?
```

**Expected query:**
```python
{
    'Customer': {'$in': ['Dunnes ROI']},
    'Month_Name': {'$in': ['Apr', 'May', 'Jun']},
    'Year': {'$in': [2024]}
}
```

**Expected data context should include:**
- "📌 Quarter Interpretation: Q2 = April, May, June..."
- "Q2 Totals (Apr-Jun):"
  - "Total Gross Sales: €X.XM" (should be > €0 if data exists)
- "Customer Performance:"
  - "Dunnes ROI: Gross Sales €X.XM, Revenue €6.4M, Profit €1.7M..."

## Debugging Steps

If still returning €0, check:

1. **Customer name in database**: Run this query to see exact customer names:
   ```python
   db.business_data.distinct('Customer')
   ```
   Look for variations like "Dunnes ROI", "DunnesROI", "Dunnes Stores ROI", etc.

2. **Check query being built**: Look at logs for:
   ```
   ✅ Matched customer: 'Dunnes ROI' -> '...'
   🔍 Data context - Query: {...}
   ```

3. **Check data context output**: Look at logs for:
   ```
   📈 Data context preview: ...
   ```
   Should show customer breakdown with actual values.

4. **Check if Customer filter is in query**: Verify that `'Customer'` key exists in the query dict passed to `get_comprehensive_data_context`.

## Files Modified

1. `backend/app/utils/data_context.py` - Fixed quarter label checks to handle abbreviated month names

## Next Steps

1. Test the query again
2. Check backend logs to see:
   - What customer name was extracted
   - What customer name was matched
   - What query was built
   - What data context was generated
3. If still failing, check database to see exact customer name format

