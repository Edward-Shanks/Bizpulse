# Traffic Type Case Normalization Fix

## Problem
In the "Traffic Type Performance" chart on Customer Deep Intelligence screen, there were two separate entries for "Unknown" - one with capital "U" (Unknown) and one with lowercase "u" (unknown). This caused the data to be split into two different categories when they should be combined into one.

## Root Cause
The MongoDB aggregation pipeline was grouping by `'$Traffic type'` directly without normalizing the case. This meant that "Unknown" and "unknown" (and any other case variations) were treated as different values.

## Solution
Added case normalization in both:
1. **Backend MongoDB aggregation** (`mongodb_customer_insights.py`)
2. **Backend server.py** (for data sync from Azure)

### Changes Made

#### 1. `backend/mongodb_customer_insights.py`
**Before:**
```python
traffic_type_pipeline = [
    {'$match': {**base_match, 'Traffic type': {'$ne': None, '$exists': True}}},
    {'$group': {
        '_id': '$Traffic type',  # Direct grouping - case sensitive!
        ...
    }},
    ...
]
```

**After:**
```python
traffic_type_pipeline = [
    {'$match': {**base_match, 'Traffic type': {'$ne': None, '$exists': True}}},
    {'$addFields': {
        'normalized_traffic_type': {
            '$cond': {
                'if': {
                    '$or': [
                        {'$eq': [{'$toLower': {'$ifNull': ['$Traffic type', '']}}, 'unknown']},
                        {'$eq': [{'$ifNull': ['$Traffic type', '']}, '']},
                        {'$eq': [{'$ifNull': ['$Traffic type', None]}, None]}
                    ]
                },
                'then': 'Unknown',  # Standardize to "Unknown" with capital U
                'else': {
                    '$concat': [
                        {'$toUpper': {'$substr': [{'$ifNull': ['$Traffic type', '']}, 0, 1]}},  # First letter uppercase
                        {'$toLower': {'$substr': [{'$ifNull': ['$Traffic type', '']}, 1, ...]}}  # Rest lowercase
                    ]
                }
            }
        }
    }},
    {'$group': {
        '_id': '$normalized_traffic_type',  # Group by normalized value
        ...
    }},
    ...
]
```

#### 2. `backend/server.py`
**Before:**
```python
traffic_type = df.groupby('Traffic type').agg({
    'Total sales': 'sum',
    'Orders': 'sum',
    'Customer email': 'nunique'
}).reset_index()
```

**After:**
```python
def normalize_traffic_type(value):
    """Normalize traffic type to title case, with special handling for 'unknown'"""
    if pd.isna(value) or value is None or str(value).strip() == '':
        return 'Unknown'
    value_str = str(value).strip()
    if value_str.lower() == 'unknown':
        return 'Unknown'  # Standardize to "Unknown" with capital U
    # Convert to title case (first letter uppercase, rest lowercase)
    return value_str[0].upper() + value_str[1:].lower() if len(value_str) > 1 else value_str.upper()

df['Traffic type normalized'] = df['Traffic type'].apply(normalize_traffic_type)
traffic_type = df.groupby('Traffic type normalized').agg({
    'Total sales': 'sum',
    'Orders': 'sum',
    'Customer email': 'nunique'
}).reset_index()
```

## Normalization Rules

1. **"unknown" (any case)** → **"Unknown"** (standardized)
2. **Empty/null values** → **"Unknown"**
3. **Other values** → **Title case** (first letter uppercase, rest lowercase)
   - "organic" → "Organic"
   - "DIRECT" → "Direct"
   - "Paid Search" → "Paid search" (only first word capitalized)

## Impact

✅ **All traffic type variations are now normalized before grouping**
✅ **"Unknown" and "unknown" are combined into a single "Unknown" entry**
✅ **Consistent case formatting across all traffic types**
✅ **No duplicate entries in the Traffic Type Performance chart**

## Testing

To verify the fix:
1. Open Customer Deep Intelligence screen
2. Navigate to "Traffic Type Performance" chart
3. Verify there is only ONE "Unknown" entry (not two)
4. Check that all traffic types are in title case format
5. Verify the sales/orders/customers values are correctly aggregated

---

**Status**: ✅ Complete
**Last Updated**: Current Session

