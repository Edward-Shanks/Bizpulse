# LLM-Powered Customer Insights Chatbot

## Overview

The Customer Deep Intelligence AI chatbot has been completely refactored to use **LLM-powered query understanding** instead of hardcoded query patterns. This makes it intelligent, flexible, and able to handle ANY question the user asks.

## How It Works

### 4-Step Intelligent Process

1. **LLM Question Understanding** (`llm_understand_question_and_generate_queries`)
   - Uses Perplexity AI to analyze the user's question
   - Determines what data is needed
   - Generates a structured query plan with:
     - Filters to apply (Year, Month, Customer Type, Channel, Country)
     - Aggregations needed (group by, sum, count)
     - Breakdowns requested (monthly, by channel, by customer type)
     - Metrics to calculate (sales, orders, customers, AOV)

2. **MongoDB Query Execution** (`execute_mongodb_queries`)
   - Executes MongoDB aggregation pipelines based on the LLM query plan
   - Fetches:
     - Summary statistics
     - Customer breakdown (New vs Returning)
     - Channel breakdown
     - Geographic breakdown
     - Monthly trends
   - Returns comprehensive data structure

3. **Data Formatting** (`format_data_for_llm`)
   - Formats MongoDB results into readable text
   - Organizes data by sections (Summary, Customer Breakdown, etc.)
   - Includes percentages and calculations
   - Makes data easy for LLM to analyze

4. **LLM Analysis & Answer Generation** (`query_perplexity`)
   - Sends formatted data + question to Perplexity AI
   - LLM analyzes the data and generates:
     - Detailed analysis
     - Key insights and patterns
     - Specific numbers and percentages
     - Actionable recommendations
     - Visual suggestions (charts/tables)

## Key Features

### ✅ Intelligent Question Understanding
- No hardcoded patterns
- Understands ANY question format
- Handles complex queries
- Infers intent from context

### ✅ Dynamic Query Generation
- LLM determines what MongoDB queries to run
- Adapts to different question types
- Handles filters, aggregations, breakdowns
- Optimizes queries based on question

### ✅ Comprehensive Data Analysis
- Fetches all relevant data
- Includes multiple breakdowns
- Calculates metrics automatically
- Provides context-aware insights

### ✅ Smart Answer Generation
- Uses LLM to analyze data
- Generates detailed explanations
- Provides specific numbers
- Includes actionable recommendations

## Example Flow

**User Question:** "Tell me about New vs Returning Customers in detail"

1. **LLM Understanding:**
   ```json
   {
     "filters": {},
     "needs_customer_breakdown": true,
     "needs_monthly_breakdown": false,
     "analysis_type": "comparison"
   }
   ```

2. **MongoDB Queries:**
   - Summary statistics
   - Customer type breakdown (New vs Returning)

3. **Data Formatting:**
   ```
   === SUMMARY STATISTICS ===
   Total Sales: €592,600.00
   Total Orders: 16,900
   Total Customers: 5,600
   
   === NEW VS RETURNING CUSTOMERS ===
   New: €200,108.00 (33.8% of sales), 6,143 orders, 3,871 customers
   Returning: €392,492.00 (66.2% of sales), 10,757 orders, 1,729 customers
   ```

4. **LLM Answer:**
   - Analyzes the data
   - Explains the breakdown
   - Provides insights
   - Gives recommendations

## Benefits

✅ **Flexible:** Handles any question format  
✅ **Intelligent:** Uses LLM to understand intent  
✅ **Accurate:** Queries MongoDB based on understanding  
✅ **Comprehensive:** Fetches all relevant data  
✅ **Actionable:** Provides detailed insights and recommendations  

## Technical Details

### LLM Query Plan Structure
```json
{
  "filters": {
    "Year": [2023, 2024],
    "Month": null,
    "New or returning customer": null
  },
  "group_by": null,
  "metrics": ["Total sales", "Orders", "Customers"],
  "breakdowns": ["by_customer_type"],
  "analysis_type": "comparison",
  "needs_customer_breakdown": true,
  "needs_channel_breakdown": false,
  "needs_geographic_breakdown": false,
  "needs_monthly_breakdown": false
}
```

### MongoDB Query Execution
- Uses aggregation pipelines
- Applies filters dynamically
- Groups and aggregates as needed
- Returns structured results

### Data Formatting
- Converts MongoDB results to readable text
- Includes calculations (percentages, averages)
- Organizes by sections
- Makes data LLM-friendly

## Error Handling

- If LLM query plan parsing fails, uses intelligent defaults
- If MongoDB queries fail, returns error message
- If LLM analysis fails, provides fallback response
- All errors are logged for debugging

## Future Enhancements

- Cache LLM query plans for similar questions
- Support for more complex aggregations
- Multi-step reasoning for complex questions
- Visual chart generation suggestions
- Export data as tables/charts

---

**Status:** ✅ Complete - Ready for Testing  
**Date:** December 2024

