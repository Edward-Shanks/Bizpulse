# Fixes for Dunnes Customer Query Issues

## Problems Identified

1. **Customer extraction patterns too restrictive**: The patterns only matched "customer X" or "customer: X", but not "for X customer" or "X customer" (e.g., "for Dunnes customer", "Dunnes ROI customer")

2. **No fuzzy matching for customers**: Unlike channels and brands, customer extraction didn't have fuzzy matching to handle variations like "Dunnes", "Dunnes ROI", "Dunnes NI"

3. **Missing customer breakdown in data context**: The data context wasn't generating customer breakdowns, so the chatbot had no customer data to work with

4. **External search results being used**: The chatbot was using Perplexity API to search for external information about Dunnes Stores' public financials, which is not relevant to internal business data

## Fixes Applied

### 1. Enhanced Customer Extraction (`query_builder.py`)

**Added patterns to match:**
- "for X customer" (e.g., "for Dunnes customer")
- "X customer" (e.g., "Dunnes customer", "Dunnes ROI customer")
- "and X customer" (e.g., "Food and Dunnes customer")

**Added fuzzy matching:**
- Similar to channel and brand matching
- Handles variations like "Dunnes" matching "Dunnes ROI", "Dunnes NI", etc.
- Uses word-based matching for partial matches (e.g., "Dunnes" in "Dunnes ROI")

**Code changes:**
```python
# Enhanced customer patterns
customer_patterns = [
    r'customer\s+([^,\.\?]+?)(?:\s|,|\.|\?|$|brand|category|in|for|across)',
    r'customer:\s*([^,\.\?]+?)(?:\s|,|\.|\?|$|brand|category|in|for|across)',
    r'for\s+([A-Z][a-zA-Z\s]+?)\s+customer(?:\s|$|,|\.|\?|in|for|across)',
    r'([A-Z][a-zA-Z\s]+?)\s+customer(?:\s|$|,|\.|\?|in|for|across)',
    r'and\s+([A-Z][a-zA-Z\s]+?)\s+customer(?:\s|$|,|\.|\?|in|for|across)',
]

# Added fuzzy matching with word-based partial matching
```

### 2. Added Customer Breakdown (`data_context.py`)

**Added customer performance breakdown:**
- Generates customer breakdown when "customer" is mentioned in the query
- Includes Gross Sales, Revenue, Profit, Margin, and Units
- Sorted by Gross Sales in descending order
- Filters out null/unknown customers

**Code changes:**
```python
# Customer breakdown
if "customer" in user_msg_lower or is_comparison or query.get('Customer'):
    pipeline_customer = [
        match_stage,
        {
            "$group": {
                "_id": "$Customer",
                "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                "Gross_Sales": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Sales", "$Revenue", 0]}}},
            }
        },
        {"$match": {"_id": {"$nin": [None, "", "Unknown", "null", "None"]}}},
        {"$sort": {"Gross_Sales": -1}}
    ]
    # ... generates customer performance breakdown
```

### 3. Prevented External Search (`insights_service.py`)

**Added explicit instructions to NOT use external search:**
- Added to system context: "You MUST NOT search the web or use external APIs"
- Added to user prompt: "Do NOT search the web or use external APIs to find information about customers, businesses, or any entities"
- Emphasized: "ONLY use the data provided in the 'Business Data' section"
- If data shows €0, state it clearly without adding external context

**Code changes:**
```python
# In system context
"You MUST NOT search the web or use external APIs to find information about customers, businesses, or any entities mentioned in the question. "
"ONLY use the data provided in the 'Business Data' section. "
"If the data shows €0 or 'No data found', state that clearly based ONLY on the provided data, without adding external context or search results. "

# In user prompt
f"Do NOT search the web or use external APIs to find information about customers, businesses, or any entities mentioned in the question. "
f"ONLY use the data provided in the 'Business Data' section above. "
f"If the data shows €0 or 'No data found', state that clearly based ONLY on the provided data, without adding external context or search results. "
```

## Expected Behavior After Fixes

1. **Customer extraction**: Should now correctly extract "Dunnes", "Dunnes ROI", "Dunnes NI" from queries like:
   - "What is the gross sales for Dunnes customer in Q2 2024?"
   - "What is the gross sales for Dunnes ROI customer in Q2 2024?"
   - "What is the gross sales for Dunnes NI customer in Q2 2024?"

2. **Customer breakdown**: Data context should now include customer performance breakdown showing:
   - Customer name
   - Gross Sales
   - Revenue
   - Profit
   - Margin
   - Units

3. **No external search**: Chatbot should only use internal business data and not search for external information about Dunnes Stores' public financials

4. **Clear zero values**: If data shows €0, chatbot should state it clearly without adding external context

## Testing

Test with these queries:
1. "What is the gross sales for Dunnes customer in Q2 2024?"
2. "What is the gross sales for Dunnes ROI customer in Q2 2024?"
3. "What is the gross sales for Dunnes NI customer in Q2 2024?"
4. "Compare Q1 gross sales for Dunnes customer in 2023 and 2024"
5. "Show me profit for Food business and Dunnes customer in 2024"

Expected results:
- Customer name should be correctly extracted
- Customer breakdown should appear in data context
- Response should only use internal business data
- If data shows €0, should state it clearly without external context

## Files Modified

1. `backend/app/utils/query_builder.py` - Enhanced customer extraction patterns and added fuzzy matching
2. `backend/app/utils/data_context.py` - Added customer breakdown generation
3. `backend/app/services/insights_service.py` - Added instructions to prevent external search

