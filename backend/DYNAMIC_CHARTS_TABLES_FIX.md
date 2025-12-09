# Dynamic Charts/Tables Fix for View Insights Chatbot

## Problem

The view insights chatbot was showing the same graphs/charts/tables for follow-up questions instead of generating new ones based on the current question. For example:
- First question: "Tell me about New vs Returning Customers" → Shows customer breakdown
- Follow-up question: "Show me sales by channel" → Still shows customer breakdown (WRONG!)

## Root Cause

1. **Hardcoded pivot_table generation**: The `pivot_table` was hardcoded to only show customer breakdown data
2. **No dynamic query planning**: Each question wasn't analyzed independently to determine what data to fetch
3. **Missing breakdown detection**: The system wasn't detecting what type of breakdown the question needed

## Solution

### 1. Dynamic Pivot Table Generation

The `pivot_table` is now generated dynamically based on:
- What the question asks for (detected by LLM)
- What breakdowns are available in the data
- Priority order: Customer → Channel → Geographic → Monthly → Summary

**Code Location:** `backend/customer_insights_fastapi.py` lines 640-704

```python
# Determine which breakdown to use based on the query plan and available data
if query_plan.get("needs_customer_breakdown", False) and data.get("customer_breakdown"):
    # Customer breakdown data
elif query_plan.get("needs_channel_breakdown", False) and data.get("channel_breakdown"):
    # Channel breakdown data
elif query_plan.get("needs_geographic_breakdown", False) and data.get("geographic_breakdown"):
    # Geographic breakdown data
elif query_plan.get("needs_monthly_breakdown", False) and data.get("monthly_breakdown"):
    # Monthly breakdown data
```

### 2. LLM-Powered Question Understanding

Each question is analyzed independently by LLM to determine:
- What filters to apply
- What breakdowns are needed
- What metrics to calculate

**Code Location:** `backend/customer_insights_fastapi.py` lines 95-200

**Key Features:**
- Analyzes each question independently
- Doesn't reuse data from previous questions
- Detects breakdown type needed (customer, channel, geographic, monthly)
- Generates fresh MongoDB queries for each question

### 3. All Breakdowns Included in Response

All available breakdowns are included in the response so the frontend can:
- Display the most relevant chart/table
- Switch between different visualizations
- Show multiple breakdowns if needed

**Code Location:** `backend/customer_insights_fastapi.py` lines 706-720

```python
breakdowns = {}
if data.get("customer_breakdown"):
    breakdowns["customer_breakdown"] = convert_to_native_types(data["customer_breakdown"])
if data.get("channel_breakdown"):
    breakdowns["channel_breakdown"] = convert_to_native_types(data["channel_breakdown"])
# ... etc
```

### 4. Enhanced LLM Prompt

The LLM prompt now:
- Emphasizes analyzing each question independently
- Includes conversation history for context (but doesn't reuse data)
- Explicitly states to generate fresh queries for each question

**Code Location:** `backend/customer_insights_fastapi.py` lines 140-176

## How It Works Now

### Example Flow

**Question 1:** "Tell me about New vs Returning Customers"

1. LLM understands: needs customer breakdown
2. MongoDB queries: fetches customer breakdown data
3. Pivot table: Shows customer breakdown (New vs Returning)
4. Response: Includes customer breakdown in `pivot_table` and `breakdowns`

**Question 2:** "Show me sales by channel"

1. LLM understands: needs channel breakdown (NOT customer)
2. MongoDB queries: fetches channel breakdown data (fresh query)
3. Pivot table: Shows channel breakdown (Direct, Organic, etc.)
4. Response: Includes channel breakdown in `pivot_table` and `breakdowns`

**Question 3:** "What are the monthly trends?"

1. LLM understands: needs monthly breakdown
2. MongoDB queries: fetches monthly trend data
3. Pivot table: Shows monthly data (Jan, Feb, Mar, etc.)
4. Response: Includes monthly breakdown in `pivot_table` and `breakdowns`

## Benefits

✅ **Dynamic**: Charts/tables change based on the question  
✅ **Intelligent**: LLM determines what data is needed  
✅ **Fresh**: Each question generates new queries  
✅ **Comprehensive**: All breakdowns included in response  
✅ **Flexible**: Handles any question type  

## Testing

To verify the fix:

1. **Test Customer Question:**
   - Ask: "Tell me about New vs Returning Customers"
   - Verify: Shows customer breakdown table/chart

2. **Test Channel Question:**
   - Ask: "Show me sales by channel"
   - Verify: Shows channel breakdown (NOT customer breakdown)

3. **Test Monthly Question:**
   - Ask: "What are the monthly trends?"
   - Verify: Shows monthly breakdown (NOT customer or channel)

4. **Test Follow-up:**
   - Ask question 1, then question 2
   - Verify: Each question shows different data

## Files Modified

1. **`backend/customer_insights_fastapi.py`**
   - Made `pivot_table` generation dynamic
   - Enhanced LLM query planning
   - Added all breakdowns to response
   - Improved prompt for independent question analysis

## Status

✅ **Fixed** - Ready for Testing

---

**Date:** December 2024  
**Issue:** View insights chatbot showing same charts/tables for different questions  
**Status:** ✅ Resolved

