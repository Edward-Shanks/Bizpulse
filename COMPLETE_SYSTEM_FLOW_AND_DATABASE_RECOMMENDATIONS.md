# BizPulse Complete System Flow & Database Recommendations

## Document Version: 1.0
**Date:** February 8, 2026  
**Prepared For:** Senior Technical Team  
**Purpose:** Complete system architecture documentation and database migration recommendations

---

## Executive Summary

### Current Architecture
- **Frontend**: React.js with Chart.js visualizations
- **Backend**: Python FastAPI with async operations
- **Database**: MongoDB (business_data & shopify_data collections)
- **AI**: Local LLM (Qwen:32b) running on Mac Studio with 512GB RAM
- **Data Privacy**: ✅ 100% on-premise (no external AI services)

### Critical Requirements Identified

#### 1. **RBAC Implementation (Highest Priority)**
Comprehensive Role-Based Access Control needed across:
- All dashboard screens (Executive, Business Compass, Customer Intelligence, etc.)
- AI Assistant Chatbot (validate access BEFORE querying)
- Multi-dimensional access control: Business, Brand, Channel, Customer, Category, Sub-Category, SKU, Data Types (revenue, profit, finance data)
- **Timeline**: 11-15 weeks for full implementation
- **Security Impact**: CRITICAL - prevents unauthorized data access

#### 2. **Performance Optimization**
Current MongoDB performance issues:
- Complex aggregations: 500-1000ms (slow for dashboards)
- Concurrent users (10+): 2000-3000ms (degradation)
- Need: Sub-100ms query times for better UX

#### 3. **Recommended Solution: ClickHouse Migration**
- **Performance**: 10-50x faster than MongoDB for analytics
- **Cost**: $100/month savings ($400 vs $500)
- **Scalability**: Handles 100x-1000x data growth efficiently
- **RBAC**: Supports native row-level security
- **Timeline**: 3-4 months for full migration

### Key Recommendations

| Priority | Action | Timeline | Impact |
|----------|--------|----------|--------|
| 🔴 **P0** | Implement RBAC in MongoDB | 11-15 weeks | Critical security requirement |
| 🟡 **P1** | MongoDB optimization (indexes, caching) | 2 weeks | 2-3x performance improvement |
| 🟢 **P2** | ClickHouse POC | 3-4 weeks | Validate 10-20x performance gains |
| 🟢 **P3** | Full ClickHouse migration | 3-4 months | Sub-100ms queries, scalability |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Dashboard Data Flow](#2-dashboard-data-flow)
3. [AI Assistant Chatbot Flow](#3-ai-assistant-chatbot-flow)
4. [Current Technology Stack](#4-current-technology-stack)
5. [RBAC (Role-Based Access Control) Implementation](#5-rbac-role-based-access-control-implementation)
6. [Database Migration Recommendations](#6-database-migration-recommendations)
7. [ClickHouse Analysis](#7-clickhouse-analysis)
8. [Alternative Solutions](#8-alternative-solutions)
9. [Migration Strategy](#9-migration-strategy)
10. [Performance Benchmarks](#10-performance-benchmarks)

---

## 1. System Overview

### Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend  │ ───> │    Backend   │ ───> │   MongoDB    │
│  React.js   │ <─── │   FastAPI    │ <─── │   Database   │
└─────────────┘      └──────────────┘      └──────────────┘
                            │
                            ↓
                     ┌──────────────┐
                     │  Local LLM   │
                     │  Qwen:32b    │
                     │ Mac Studio   │
                     │  (512GB RAM) │
                     └──────────────┘
```

### Key Components

1. **Frontend**: React.js with Chart.js for visualizations
2. **Backend**: Python FastAPI for API endpoints
3. **Database**: MongoDB for data storage
4. **AI**: Local LLM (Qwen:32b) running on Mac Studio with 512GB RAM
5. **Infrastructure**: Mac Studio dedicated AI server for private LLM hosting

---

## 2. Dashboard Data Flow

### 2.1 Data Collection & Storage

```
Data Source → MongoDB → Aggregation Pipeline → API Response → Frontend Visualization
```

#### Detailed Flow:

**Step 1: Data Ingestion**
```
Azure Blob Storage → Python Script → MongoDB (business_data & shopify_data collections)
```

- Raw business data stored in Azure
- Sync scripts load data into MongoDB
- Two main collections:
  - `business_data`: Revenue, profit, units, business metrics
  - `shopify_data`: Customer orders, sales, Shopify analytics

**Step 2: Frontend Request**
```javascript
// Example: Executive Dashboard
axios.get(`${API}/analytics/executive-dashboard`, { 
  params: { 
    years: '2024,2025',
    months: 'January,February',
    businesses: 'Business A,Business B'
  } 
})
```

**Step 3: Backend Processing**
```python
# backend/app/api/v1/routes/analytics.py
@router.get("/analytics/executive-dashboard")
async def get_executive_overview(
    years: Optional[str] = None,
    months: Optional[str] = None,
    businesses: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = AnalyticsService(db)
    return await service.get_executive_dashboard(years, months, businesses)
```

**Step 4: MongoDB Aggregation**
```python
# backend/app/services/analytics_service.py
async def get_executive_dashboard(self, years, months, businesses):
    # Build match stage
    match_stage = {"$match": {}}
    if years:
        match_stage["$match"]["Year"] = {"$in": [2024, 2025]}
    
    # Aggregation pipeline
    pipeline = [
        match_stage,
        {
            "$group": {
                "_id": "$Customer",
                "revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "units": {"$sum": {"$toDouble": "$Units"}}
            }
        },
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]
    
    # Execute aggregation
    results = await db.business_data.aggregate(pipeline).to_list(1000)
    return format_results(results)
```

**Step 5: Data Transformation & Response**
```python
# Format data for frontend
{
    "summary": {
        "gross_sales": 343070000,
        "gross_profit": 104390000,
        "margin_pct": 30.43
    },
    "top_contributors": {
        "customers": [...],
        "brands": [...],
        "categories": [...]
    },
    "monthly_trend": [...]
}
```

**Step 6: Frontend Visualization**
```javascript
// Chart.js rendering
<ChartComponent
  type="bar"
  data={{
    labels: data.top_contributors.customers.map(c => c.name),
    datasets: [{
      label: 'Revenue',
      data: data.top_contributors.customers.map(c => c.revenue),
      backgroundColor: '#60a5fa'
    }]
  }}
/>
```

### 2.2 Dashboard Screens & Their Data Flow

#### Executive Dashboard
- **Endpoint**: `/analytics/executive-dashboard`
- **Collections**: `business_data`
- **Aggregations**: Top customers, brands, channels, categories, businesses
- **Complexity**: Medium (multiple group-by operations)
- **Response Time**: 200-500ms

#### Customer Deep Intelligence
- **Endpoint**: `/analytics/customer-insights`
- **Collections**: `shopify_data`
- **Aggregations**: Customer segmentation, geographic analysis, channel analysis
- **Complexity**: High (complex nested aggregations)
- **Response Time**: 500-1000ms

#### Business Compass
- **Endpoint**: `/analytics/executive-overview`
- **Collections**: `business_data`
- **Aggregations**: Yearly trends, business performance, monthly trends
- **Complexity**: Low-Medium
- **Response Time**: 100-300ms

---

## 3. AI Assistant Chatbot Flow

### 3.1 Complete AI Chatbot Pipeline

```
User Question → Context Creation → LLM Query Planning → MongoDB Execution → 
Data Formatting → LLM Analysis → Natural Language Response
```

### 3.2 Step-by-Step Detailed Flow

#### **STEP 1: User Asks a Question**

```javascript
// Frontend: components/AIAssistant.js
const sendMessage = async () => {
  const response = await axios.post(`${API}/insights/chat`, {
    message: "What were the top 5 customers in 2024?",
    chart_title: "Executive Overview",
    context: { years: [2024] },
    conversation_history: previousMessages
  });
};
```

**Example Questions:**
- "What were total sales in January 2025?"
- "Compare new vs returning customers"
- "Show me top 10 brands by profit"
- "How did Q4 2024 perform compared to Q3?"

---

#### **STEP 2: Backend Receives Request & Creates Initial Context**

```python
# backend/server.py or backend/app/api/v1/routes/insights.py
@router.post("/insights/chat")
async def insights_chat(request: InsightsChatRequest):
    user_message = request.message
    chart_title = request.chart_title
    context = request.context  # e.g., {"years": [2024]}
    conversation_history = request.conversation_history
    
    # Process the chat
    result = await process_chat(user_message, context, conversation_history)
    return result
```

---

#### **STEP 3: LLM Query Planning (Context Creation)**

**Purpose:** Use AI to understand what data the user needs

```python
# backend/customer_insights_fastapi.py
async def llm_understand_question_and_generate_queries(
    question: str,
    chart_title: Optional[str],
    context: Optional[Dict],
    conversation_history: Optional[List]
) -> Dict[str, Any]:
    """
    Step 3: Use LLM to understand the question and create a MongoDB query plan
    """
    
    # Build prompt for LLM
    available_fields = """
    Available fields in database:
    - Year (number): e.g., 2023, 2024, 2025
    - Month_Name (string): "January", "February", etc.
    - Customer (string): Customer name
    - Brand (string): Brand name
    - Revenue (number): Sales amount
    - Gross_Profit (number): Profit amount
    - Units (number): Units sold
    - Channel (string): Sales channel
    - Business (string): Business unit
    """
    
    prompt = f"""You are a MongoDB query planner.

User Question: "{question}"
Chart Context: {chart_title}
Available Filters: {json.dumps(context or {})}

{available_fields}

Analyze the question and determine:
1. What filters should be applied (Year, Month, Customer Type, etc.)
2. What aggregations are needed (group by, sum, count, etc.)
3. What breakdowns are requested (by month, by customer, by brand, etc.)
4. What metrics to calculate (total sales, profit, customer count, etc.)

Return a JSON object with this structure:
{{
    "filters": {{
        "Year": [2024, 2025] or null,
        "Month_Name": ["January", "February"] or null,
        "Customer": "Specific Customer" or null
    }},
    "group_by": ["Year", "Month_Name"] or ["Customer"] or null,
    "metrics": ["Revenue", "Gross_Profit", "Units"],
    "breakdowns": ["monthly", "by_customer", "by_brand"],
    "analysis_type": "summary" | "trend" | "comparison" | "breakdown",
    "needs_customer_breakdown": true or false,
    "needs_brand_breakdown": true or false,
    "needs_monthly_breakdown": true or false
}}

Return ONLY valid JSON, no additional text.
"""
    
    # Call Perplexity AI
    response = await query_llm(prompt, conversation_history)
    
    # Parse JSON response
    query_plan = json.loads(response)
    
    return query_plan
```

**Example LLM Response:**
```json
{
  "filters": {
    "Year": [2024],
    "Month_Name": null
  },
  "group_by": ["Customer"],
  "metrics": ["Revenue", "Gross_Profit", "Units"],
  "breakdowns": ["by_customer"],
  "analysis_type": "breakdown",
  "needs_customer_breakdown": true,
  "needs_brand_breakdown": false,
  "needs_monthly_breakdown": false
}
```

---

#### **STEP 4: Execute MongoDB Queries**

**Purpose:** Fetch data from MongoDB based on LLM's query plan

```python
# backend/customer_insights_fastapi.py
async def execute_mongodb_queries(
    db: AsyncIOMotorDatabase,
    query_plan: Dict[str, Any],
    preset_filters: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Step 4: Execute MongoDB aggregation pipelines based on LLM query plan
    """
    
    # Build base match query from filters
    match_query = {}
    
    # Apply filters from query plan
    if query_plan.get("filters"):
        filters = query_plan["filters"]
        
        if filters.get("Year"):
            match_query["Year"] = {"$in": filters["Year"]}
        
        if filters.get("Month_Name"):
            match_query["Month_Name"] = {"$in": filters["Month_Name"]}
        
        if filters.get("Customer"):
            match_query["Customer"] = filters["Customer"]
    
    # Execute summary aggregation
    summary_pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": {"$toDouble": "$Revenue"}},
                "total_profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "total_units": {"$sum": {"$toDouble": "$Units"}},
                "unique_customers": {"$addToSet": "$Customer"}
            }
        },
        {
            "$project": {
                "total_sales": 1,
                "total_profit": 1,
                "total_units": 1,
                "customer_count": {"$size": "$unique_customers"}
            }
        }
    ]
    
    summary_result = await db.business_data.aggregate(summary_pipeline).to_list(1)
    summary = summary_result[0] if summary_result else {}
    
    # Execute customer breakdown if needed
    customer_breakdown = []
    if query_plan.get("needs_customer_breakdown"):
        customer_pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$Customer",
                    "revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                    "units": {"$sum": {"$toDouble": "$Units"}}
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        
        customer_breakdown = await db.business_data.aggregate(customer_pipeline).to_list(10)
    
    # Execute monthly breakdown if needed
    monthly_breakdown = []
    if query_plan.get("needs_monthly_breakdown"):
        monthly_pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": {"Year": "$Year", "Month": "$Month_Name"},
                    "revenue": {"$sum": {"$toDouble": "$Revenue"}},
                    "profit": {"$sum": {"$toDouble": "$Gross_Profit"}}
                }
            },
            {"$sort": {"_id.Year": 1, "_id.Month": 1}}
        ]
        
        monthly_breakdown = await db.business_data.aggregate(monthly_pipeline).to_list(100)
    
    # Return comprehensive data structure
    return {
        "summary": summary,
        "customer_breakdown": customer_breakdown,
        "monthly_breakdown": monthly_breakdown,
        "filters_applied": match_query
    }
```

**Example MongoDB Query Output:**
```json
{
  "summary": {
    "total_sales": 45600000,
    "total_profit": 13800000,
    "total_units": 1250000,
    "customer_count": 156
  },
  "customer_breakdown": [
    {"_id": "Musgrave ROI", "revenue": 45672000, "profit": 13723000, "units": 345000},
    {"_id": "Dunnes ROI", "revenue": 38426000, "profit": 11532000, "units": 289000}
  ],
  "monthly_breakdown": [...]
}
```

---

#### **STEP 5: Format Data for LLM Analysis**

**Purpose:** Convert MongoDB results into human-readable text for LLM

```python
# backend/customer_insights_fastapi.py
def format_data_for_llm(data: Dict[str, Any]) -> str:
    """
    Step 5: Format MongoDB results into human-readable text for LLM analysis
    """
    
    formatted_sections = []
    
    # Format summary
    if data.get("summary"):
        summary = data["summary"]
        formatted_sections.append(f"""
=== SUMMARY STATISTICS ===
Total Sales: €{summary.get('total_sales', 0):,.2f}
Total Profit: €{summary.get('total_profit', 0):,.2f}
Total Units: {summary.get('total_units', 0):,.0f}
Customer Count: {summary.get('customer_count', 0):,}
Profit Margin: {(summary.get('total_profit', 0) / summary.get('total_sales', 1) * 100):.2f}%
        """)
    
    # Format customer breakdown
    if data.get("customer_breakdown"):
        formatted_sections.append("\n=== TOP CUSTOMERS BY REVENUE ===")
        for idx, customer in enumerate(data["customer_breakdown"], 1):
            formatted_sections.append(f"""
{idx}. {customer['_id']}
   Revenue: €{customer['revenue']:,.2f}
   Profit: €{customer['profit']:,.2f}
   Units: {customer['units']:,.0f}
   Margin: {(customer['profit'] / customer['revenue'] * 100):.2f}%
            """)
    
    # Format monthly breakdown
    if data.get("monthly_breakdown"):
        formatted_sections.append("\n=== MONTHLY TREND ===")
        for month in data["monthly_breakdown"]:
            formatted_sections.append(f"""
{month['_id']['Month']} {month['_id']['Year']}: 
Revenue €{month['revenue']:,.2f}, Profit €{month['profit']:,.2f}
            """)
    
    return "\n".join(formatted_sections)
```

**Example Formatted Output:**
```
=== SUMMARY STATISTICS ===
Total Sales: €45,600,000.00
Total Profit: €13,800,000.00
Total Units: 1,250,000
Customer Count: 156
Profit Margin: 30.26%

=== TOP CUSTOMERS BY REVENUE ===
1. Musgrave ROI
   Revenue: €45,672,000.00
   Profit: €13,723,000.00
   Units: 345,000
   Margin: 30.04%

2. Dunnes ROI
   Revenue: €38,426,000.00
   Profit: €11,532,000.00
   Units: 289,000
   Margin: 30.01%
```

---

#### **STEP 6: LLM Analysis & Answer Generation**

**Purpose:** Use AI to analyze the data and provide business insights

```python
# backend/server.py
async def generate_ai_response(
    user_question: str,
    formatted_data: str,
    chart_context: str,
    conversation_history: List
) -> str:
    """
    Step 6: Use LLM to analyze data and generate comprehensive answer
    """
    
    # Build system prompt
    system_context = """
You are Vector AI, a strategic business intelligence analyst for ThriveBrands.
You provide business insights and recommendations to executives and managers.

CRITICAL RULES:
- NEVER mention technical terms like 'MongoDB', 'database', 'query', 'API'
- Speak ONLY in business language
- Focus on business outcomes, strategies, and actionable insights
- Provide comprehensive analysis including:
  1. Key insights and patterns in the data
  2. What these numbers mean for the business
  3. Specific, actionable recommendations (3-5 items)
  4. Potential risks or opportunities
  5. Next steps the user should take

Do NOT just list the data - analyze it, interpret it, and provide strategic guidance.
    """
    
    # Build user prompt
    user_prompt = f"""
Chart Context: {chart_context}

Business Data:
{formatted_data}

User Question: {user_question}

Provide a comprehensive business analysis answering the user's question.
Include specific numbers, percentages, insights, and actionable recommendations.
    """
    
    # Call Perplexity AI with conversation history
    messages = [
        {"role": "system", "content": system_context},
        *conversation_history,  # Include previous conversation
        {"role": "user", "content": user_prompt}
    ]
    
    response = await query_perplexity_api(messages)
    
    return response
```

**Example LLM Response:**
```
Based on your 2024 performance data, here's a comprehensive analysis:

KEY INSIGHTS:
Your business generated €45.6M in revenue with a healthy 30.26% profit margin 
across 156 customers. This indicates strong pricing power and efficient operations.

TOP PERFORMERS:
1. Musgrave ROI leads with €45.7M (30.04% margin) - your anchor customer
2. Dunnes ROI at €38.4M (30.01% margin) - consistently strong performer

Both maintain margins above 30%, suggesting premium positioning is working well.

ACTIONABLE RECOMMENDATIONS:

1. CUSTOMER CONCENTRATION RISK
   WHY: Your top 2 customers represent 84% of revenue
   ACTION: Diversify by targeting 5-10 mid-size accounts (€5-10M potential)
   TIMELINE: Q1 2025

2. MARGIN OPTIMIZATION
   WHY: Consistent 30% margins across top accounts
   ACTION: Test 1-2% price increases on top-performing SKUs
   EXPECTED IMPACT: +€450K annual profit with minimal volume risk

3. VOLUME GROWTH OPPORTUNITY
   WHY: 1.25M units suggests capacity for 20-30% growth
   ACTION: Launch targeted promotions in Q2 when seasonality favors volume

RISKS TO WATCH:
- Heavy reliance on top 2 customers (monitor relationship health)
- Need to understand what drives the 30% margin ceiling

NEXT STEPS:
1. Schedule quarterly business reviews with Musgrave and Dunnes
2. Develop account acquisition plan for 5 new mid-market customers
3. Analyze SKU-level performance to identify margin expansion opportunities
```

---

#### **STEP 7: Return Response to Frontend**

```python
# Backend sends structured response
return {
    "response": llm_analysis_text,
    "data_summary": {
        "total_sales": 45600000,
        "total_profit": 13800000,
        "customer_count": 156
    },
    "conversation_id": "conv_123",
    "timestamp": "2026-02-08T10:30:00Z"
}
```

```javascript
// Frontend displays response
<div className="ai-response">
  {response.response}  {/* Formatted markdown/text */}
</div>
```

---

### 3.3 AI Chatbot Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER ASKS QUESTION                          │
│              "What were top 5 customers in 2024?"                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: BACKEND RECEIVES                         │
│     - User message                                                  │
│     - Chart context (optional)                                      │
│     - Conversation history (for follow-ups)                         │
│     - Current filters (year, month, etc.)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 2: LLM QUERY PLANNING (Context Creation)              │
│                                                                     │
│  Input to LLM:                                                      │
│    - User question                                                  │
│    - Available database fields                                      │
│    - Conversation history                                           │
│    - Chart context                                                  │
│                                                                     │
│  LLM Analyzes & Returns:                                            │
│    {                                                                │
│      "filters": {"Year": [2024]},                                   │
│      "group_by": ["Customer"],                                      │
│      "metrics": ["Revenue", "Profit"],                              │
│      "needs_customer_breakdown": true,                              │
│      "analysis_type": "breakdown"                                   │
│    }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│            STEP 3: EXECUTE MONGODB AGGREGATIONS                     │
│                                                                     │
│  Based on LLM plan, run queries:                                    │
│    1. Summary aggregation (totals, averages)                        │
│    2. Customer breakdown (if needed)                                │
│    3. Brand breakdown (if needed)                                   │
│    4. Monthly trends (if needed)                                    │
│    5. Geographic breakdown (if needed)                              │
│                                                                     │
│  MongoDB Pipeline Example:                                          │
│    [                                                                │
│      {"$match": {"Year": 2024}},                                    │
│      {"$group": {"_id": "$Customer",                                │
│                  "revenue": {"$sum": "$Revenue"}}},                 │
│      {"$sort": {"revenue": -1}},                                    │
│      {"$limit": 5}                                                  │
│    ]                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│         STEP 4: FORMAT DATA FOR LLM (Human Readable)                │
│                                                                     │
│  Convert JSON to readable text:                                     │
│                                                                     │
│  === SUMMARY STATISTICS ===                                         │
│  Total Sales: €45.6M                                                │
│  Total Profit: €13.8M                                               │
│  Customer Count: 156                                                │
│                                                                     │
│  === TOP 5 CUSTOMERS ===                                            │
│  1. Musgrave ROI: €45.7M revenue, 30% margin                        │
│  2. Dunnes ROI: €38.4M revenue, 30% margin                          │
│  ...                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│      STEP 5: LLM ANALYSIS & INSIGHT GENERATION                      │
│                                                                     │
│  Input to LLM:                                                      │
│    - User question                                                  │
│    - Formatted data (from Step 4)                                   │
│    - Business context                                               │
│    - Conversation history                                           │
│                                                                     │
│  System Prompt:                                                     │
│    "You are a business analyst. Analyze this data and provide:      │
│     1. Key insights                                                 │
│     2. What it means for the business                               │
│     3. Actionable recommendations                                   │
│     4. Risks and opportunities                                      │
│     NEVER mention technical terms like MongoDB or database"         │
│                                                                     │
│  LLM Generates:                                                     │
│    - Comprehensive business analysis                                │
│    - Specific numbers and percentages                               │
│    - Strategic recommendations                                      │
│    - Action items                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│            STEP 6: RETURN TO USER (Frontend Display)                │
│                                                                     │
│  Response Format:                                                   │
│    {                                                                │
│      "response": "Your top 5 customers in 2024...",                 │
│      "data_summary": {...},                                         │
│      "timestamp": "2026-02-08T10:30:00Z"                            │
│    }                                                                │
│                                                                     │
│  Frontend renders formatted response with markdown support          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Key Features of AI Chatbot

#### ✅ **Intelligent Understanding**
- No hardcoded query patterns
- Understands ANY question format
- Handles complex multi-part questions
- Uses conversation context for follow-ups

#### ✅ **Dynamic Query Generation**
- LLM determines what MongoDB queries to run
- Adapts to user's specific needs
- Handles filters, groupings, and aggregations automatically

#### ✅ **Comprehensive Analysis**
- Provides key insights and patterns
- Explains what numbers mean for business
- Offers 3-5 actionable recommendations
- Identifies risks and opportunities

#### ✅ **Non-Technical Language**
- Never mentions "MongoDB", "database", "query"
- Speaks in business terms executives understand
- Focuses on outcomes, not technical implementation

---

## 4. Current Technology Stack

### 4.1 Frontend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React.js 18 | UI components and state management |
| Charts | Chart.js 4 | Data visualizations |
| HTTP Client | Axios | API communication |
| Styling | Tailwind CSS | UI styling |
| Build Tool | Vite | Fast development and build |

### 4.2 Backend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI (Python) | RESTful API endpoints |
| Database Driver | Motor (async) | MongoDB async operations |
| AI Integration | Local LLM (Qwen:32b) | Intelligent chatbot analysis |
| AI Infrastructure | Mac Studio (512GB RAM) | Dedicated LLM hosting server |
| Auth | JWT | User authentication |
| Async Runtime | asyncio | Concurrent operations |

### 4.3 AI/LLM Infrastructure

| Component | Details | Purpose |
|-----------|---------|---------|
| **Model** | Qwen:32b (32 billion parameters) | Large language model for business intelligence |
| **Hardware** | Mac Studio with 512GB RAM | On-premise AI inference server |
| **Deployment** | Self-hosted (local) | Data privacy and security |
| **Interface** | Ollama / LLM API | Model serving and API interface |
| **Latency** | ~2-5 seconds per query | Local inference (no network latency) |
| **Cost** | Zero per-query cost | One-time hardware investment |
| **Data Privacy** | ✅ 100% Private | No data leaves your infrastructure |

#### Advantages of Local LLM:
1. **Data Privacy**: All business data stays on-premise, never sent to external APIs
2. **Cost Efficiency**: No per-token or per-query charges
3. **Unlimited Usage**: No rate limits or usage caps
4. **Customization**: Can fine-tune model on your specific business data
5. **Compliance**: Meets data residency and privacy requirements
6. **Low Latency**: Local processing eliminates network round-trips

#### Advantages of Local LLM:
1. **Data Privacy**: All business data stays on-premise, never sent to external APIs
2. **Cost Efficiency**: No per-token or per-query charges
3. **Unlimited Usage**: No rate limits or usage caps
4. **Customization**: Can fine-tune model on your specific business data
5. **Compliance**: Meets data residency and privacy requirements
6. **Low Latency**: Local processing eliminates network round-trips

### 4.4 Database Stack

| Component | Technology | Details |
|-----------|-----------|---------|
| Database | MongoDB 6.0+ | Document-oriented NoSQL |
| Driver | Motor (PyMongo async) | Async MongoDB driver |
| Collections | 2 main collections | `business_data`, `shopify_data` |
| Indexes | Compound indexes | Year, Month, Customer, Brand |
| Hosting | MongoDB Atlas | Cloud-hosted |

### 4.5 Data Structure

#### business_data Collection
```json
{
  "_id": ObjectId,
  "Year": 2024,
  "Month": 1,
  "Month_Name": "January",
  "Customer": "Musgrave ROI",
  "Brand": "Brand A",
  "Business": "Business Unit 1",
  "Channel": "Direct",
  "Category": "Category 1",
  "Revenue": 450000.0,
  "Gross_Profit": 135000.0,
  "Units": 12500.0,
  "Price_Downs": 5000.0,
  "Group_Cost": 10000.0,
  "LTA": 2000.0
}
```

#### shopify_data Collection
```json
{
  "_id": ObjectId,
  "Year": 2025,
  "Month": 1,
  "Day": "2025-01-15",
  "Customer email": "customer@example.com",
  "Customer name": "John Doe",
  "Total sales": 150.50,
  "Orders": 1,
  "New or returning customer": "New",
  "Referring channel": "google",
  "Shipping country": "United Kingdom",
  "Hour of day": 14,
  "Orders (first-time)": 1,
  "Orders (returning)": 0
}
```

---

## 5. RBAC (Role-Based Access Control) Implementation

### 5.1 Overview

**Critical Requirement**: Implement comprehensive Role-Based Access Control (RBAC) across **all levels** of data access in both **Dashboards** and **AI Assistant Chatbot**.

### 5.2 Access Control Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LOGIN                              │
│              (JWT Token with User Permissions)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RBAC PERMISSION CHECK                         │
│                                                                 │
│  User has access to:                                            │
│    ✅ Businesses: ["Business A", "Business C"]                  │
│    ✅ Brands: ["Brand X", "Brand Y", "Brand Z"]                 │
│    ✅ Channels: ["Direct", "Online"]                            │
│    ✅ Customers: ["Customer 1", "Customer 5"]                   │
│    ✅ Categories: ["Category A", "Category B"]                  │
│    ✅ Sub-Categories: ["Sub-Cat 1", "Sub-Cat 2"]                │
│    ✅ SKUs: ["SKU-001", "SKU-002", "SKU-100"]                   │
│    ✅ Data Types: ["revenue", "units", "profit"]                │
│    ❌ Restricted: ["finance_data", "cost_data"]                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  APPLY FILTERS TO ALL QUERIES                   │
│                                                                 │
│  MongoDB Query Example:                                         │
│    {                                                            │
│      "$match": {                                                │
│        "Business": {"$in": ["Business A", "Business C"]},       │
│        "Brand": {"$in": ["Brand X", "Brand Y", "Brand Z"]},     │
│        "Channel": {"$in": ["Direct", "Online"]},                │
│        "Customer": {"$in": ["Customer 1", "Customer 5"]},       │
│        "Year": 2024                                             │
│      }                                                          │
│    }                                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│           USER SEES ONLY AUTHORIZED DATA                        │
│     (In Dashboard Charts & AI Chatbot Responses)                │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 RBAC Dimensions

BizPulse requires multi-dimensional access control:

| Dimension | Description | Example Use Case |
|-----------|-------------|------------------|
| **Business** | Business unit access | Sales team only sees "Business A" |
| **Brand** | Brand-level access | Brand manager sees only their brands |
| **Channel** | Sales channel access | Online team can't see Direct channel |
| **Customer** | Customer account access | Account manager sees only their customers |
| **Category** | Product category access | Category manager sees only their category |
| **Sub-Category** | Sub-category access | Fine-grained product access |
| **SKU** | Individual product access | Product specialist sees specific SKUs |
| **Data Type** | Metric access (revenue, profit, cost) | Sales team can't see financial cost data |
| **Geographic** | Region/country access | EU manager sees only EU customers |
| **Time Period** | Historical data access | New users see only recent data |

### 5.4 User Roles & Permissions

#### Role Definitions

```python
# Example User Permission Structure
user_permissions = {
    "user_id": "user123",
    "email": "john.doe@company.com",
    "role": "brand_manager",
    "permissions": {
        "businesses": ["Business A", "Business C"],
        "brands": ["Brand X", "Brand Y"],
        "channels": ["Direct", "Online", "Retail"],
        "customers": "*",  # "*" means all customers
        "categories": ["Electronics", "Accessories"],
        "sub_categories": "*",
        "skus": "*",
        "data_access": {
            "revenue": True,
            "units": True,
            "gross_profit": True,
            "transfer_cost": False,  # ❌ No access
            "group_cost": False,     # ❌ No access
            "finance_data": False    # ❌ No access
        },
        "time_access": {
            "years": [2023, 2024, 2025],
            "all_historical": False  # Can't access data before 2023
        }
    }
}
```

#### Common Role Examples

| Role | Access Level | Typical Permissions |
|------|-------------|---------------------|
| **Admin** | Full access | All businesses, brands, customers, all data types |
| **Executive** | Multi-business | Multiple businesses, all brands, revenue + profit + finance |
| **Business Manager** | Business-level | Single business, all brands under it, revenue + profit |
| **Brand Manager** | Brand-level | Specific brands only, revenue + units + profit (no costs) |
| **Sales Team** | Customer-level | Assigned customers, revenue + units only (no profit/cost) |
| **Category Manager** | Category-level | Specific categories, revenue + units + profit |
| **Finance Team** | Financial data | All businesses, all financial metrics including costs |
| **External Partner** | Limited | Specific brands/customers, revenue only |

### 5.5 RBAC Implementation in Dashboards

#### Flow for Dashboard Queries

```
User Opens Dashboard → Extract User Permissions from JWT → 
Apply RBAC Filters → Query MongoDB with Filters → Return Filtered Data
```

#### Implementation Example

```python
# backend/app/middleware/rbac.py

async def apply_rbac_filters(
    user_email: str,
    base_query: Dict,
    db: AsyncIOMotorDatabase
) -> Dict:
    """
    Apply RBAC filters to MongoDB queries based on user permissions
    """
    # Get user permissions from database
    user = await db.users.find_one({"email": user_email})
    permissions = user.get("permissions", {})
    
    # Build RBAC filter
    rbac_filter = {}
    
    # Business access
    if permissions.get("businesses") and permissions["businesses"] != "*":
        rbac_filter["Business"] = {"$in": permissions["businesses"]}
    
    # Brand access
    if permissions.get("brands") and permissions["brands"] != "*":
        rbac_filter["Brand"] = {"$in": permissions["brands"]}
    
    # Channel access
    if permissions.get("channels") and permissions["channels"] != "*":
        rbac_filter["Channel"] = {"$in": permissions["channels"]}
    
    # Customer access
    if permissions.get("customers") and permissions["customers"] != "*":
        rbac_filter["Customer"] = {"$in": permissions["customers"]}
    
    # Category access
    if permissions.get("categories") and permissions["categories"] != "*":
        rbac_filter["Category"] = {"$in": permissions["categories"]}
    
    # Merge RBAC filters with base query
    final_query = {**base_query, **rbac_filter}
    
    return final_query


# Example: Executive Dashboard with RBAC
@router.get("/analytics/executive-dashboard")
async def get_executive_dashboard(
    years: Optional[str] = None,
    months: Optional[str] = None,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Base query from user filters
    base_query = {}
    if years:
        base_query["Year"] = {"$in": parse_years(years)}
    
    # ✅ APPLY RBAC FILTERS
    final_query = await apply_rbac_filters(email, base_query, db)
    
    # Execute query with RBAC filters
    service = AnalyticsService(db)
    return await service.get_executive_dashboard(final_query)
```

#### Data Type Access Control

```python
# Filter out restricted financial fields
async def filter_restricted_fields(
    data: Dict,
    user_permissions: Dict
) -> Dict:
    """
    Remove fields user doesn't have access to
    """
    data_access = user_permissions.get("data_access", {})
    
    # Remove restricted fields from response
    if not data_access.get("transfer_cost", False):
        data.pop("transfer_cost", None)
        data.pop("Transfer_Cost", None)
    
    if not data_access.get("group_cost", False):
        data.pop("group_cost", None)
        data.pop("Group_Cost", None)
    
    if not data_access.get("finance_data", False):
        # Remove all finance-related metrics
        data.pop("LTA", None)
        data.pop("Price_Downs", None)
    
    return data
```

### 5.6 RBAC Implementation in AI Assistant Chatbot

#### Critical Challenge: Intent-Based Access Control

The AI chatbot must:
1. **Understand what the user is asking for**
2. **Check if user has access to that data BEFORE querying**
3. **Block unauthorized requests early**
4. **Provide clear access denial messages**

#### Enhanced AI Chatbot Flow with RBAC

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER ASKS QUESTION                           │
│     "What were top 5 customers for Brand X in 2024?"            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          STEP 1: EXTRACT USER PERMISSIONS                       │
│                                                                 │
│  Get user's JWT token and extract permissions:                  │
│    - Allowed businesses                                         │
│    - Allowed brands                                             │
│    - Allowed data types                                         │
│    - Allowed customers                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│    STEP 2: LLM UNDERSTANDS QUESTION & EXTRACTS INTENT           │
│                                                                 │
│  Send question to LLM with special prompt:                      │
│    "Analyze this question and extract:                          │
│     1. What brands is user asking about?                        │
│     2. What customers is user asking about?                     │
│     3. What data types (revenue, profit, cost)?                 │
│     4. What businesses?                                         │
│     5. What channels?"                                          │
│                                                                 │
│  LLM Response:                                                  │
│    {                                                            │
│      "requested_brands": ["Brand X"],                           │
│      "requested_customers": ["all"],                            │
│      "requested_data_types": ["revenue", "customer_count"],     │
│      "requested_businesses": ["Business A"]                     │
│    }                                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         STEP 3: RBAC VALIDATION (BEFORE QUERYING!)              │
│                                                                 │
│  Check if user has access to requested resources:               │
│                                                                 │
│  ✅ Brand X: User has access                                    │
│  ✅ Business A: User has access                                 │
│  ✅ Revenue data: User has access                               │
│  ❌ Cost data: User does NOT have access                        │
│                                                                 │
│  Decision:                                                      │
│    IF all requested resources are authorized:                   │
│      → Proceed to Step 4 (Query MongoDB)                        │
│    ELSE:                                                        │
│      → STOP and return access denied message                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│    STEP 4: EXECUTE MONGODB QUERY WITH RBAC FILTERS              │
│                                                                 │
│  Build MongoDB query with AUTOMATIC RBAC filters:               │
│    {                                                            │
│      "$match": {                                                │
│        "Brand": "Brand X",  # From question                     │
│        "Business": {"$in": ["Business A", "Business C"]},       │
│                            # ↑ From user permissions            │
│        "Year": 2024                                             │
│      }                                                          │
│    }                                                            │
│                                                                 │
│  Execute query and return only authorized data                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│    STEP 5: FORMAT DATA & SEND TO LLM FOR ANALYSIS              │
│    STEP 6: RETURN RESPONSE TO USER                             │
│                                                                 │
│  Response includes only data user has access to                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementation: Intent Extraction with LLM

```python
# backend/app/services/rbac_chatbot_service.py

async def extract_data_access_intent(
    question: str,
    conversation_history: List
) -> Dict[str, Any]:
    """
    Use LLM to understand what data the user is trying to access
    """
    prompt = f"""You are a data access analyzer. Extract what data the user is requesting.

User Question: "{question}"

Analyze and extract:
1. What BRANDS is the user asking about? (list or "all")
2. What BUSINESSES is the user asking about? (list or "all")
3. What CHANNELS is the user asking about? (list or "all")
4. What CUSTOMERS is the user asking about? (list or "all")
5. What CATEGORIES is the user asking about? (list or "all")
6. What DATA TYPES is the user asking about?
   - revenue (sales data)
   - profit (profit/margin data)
   - cost (cost data like transfer cost, group cost)
   - finance (financial metrics like LTA, price downs)
   - units (volume data)

Return ONLY valid JSON:
{{
  "requested_brands": ["Brand X"] or "all",
  "requested_businesses": ["Business A"] or "all",
  "requested_channels": ["Direct"] or "all",
  "requested_customers": ["Customer 1"] or "all",
  "requested_categories": ["Electronics"] or "all",
  "requested_data_types": ["revenue", "profit", "units"]
}}

CRITICAL: If user asks about costs, margins, financial data, include "finance" in data_types.
If user asks about sales or revenue, include "revenue".
If user asks about profit or margin, include "profit".
"""
    
    # Call local LLM (Qwen:32b)
    llm_response = await query_local_llm(prompt, conversation_history)
    
    # Parse JSON response
    intent = json.loads(llm_response)
    
    return intent


async def validate_rbac_access(
    user_email: str,
    intent: Dict[str, Any],
    db: AsyncIOMotorDatabase
) -> Tuple[bool, str]:
    """
    Validate if user has access to requested data
    Returns: (has_access: bool, denial_reason: str)
    """
    # Get user permissions
    user = await db.users.find_one({"email": user_email})
    permissions = user.get("permissions", {})
    data_access = permissions.get("data_access", {})
    
    # Check brand access
    requested_brands = intent.get("requested_brands", "all")
    if requested_brands != "all":
        allowed_brands = permissions.get("brands", [])
        if allowed_brands != "*":
            unauthorized_brands = set(requested_brands) - set(allowed_brands)
            if unauthorized_brands:
                return False, f"You don't have access to brands: {', '.join(unauthorized_brands)}"
    
    # Check business access
    requested_businesses = intent.get("requested_businesses", "all")
    if requested_businesses != "all":
        allowed_businesses = permissions.get("businesses", [])
        if allowed_businesses != "*":
            unauthorized_businesses = set(requested_businesses) - set(allowed_businesses)
            if unauthorized_businesses:
                return False, f"You don't have access to businesses: {', '.join(unauthorized_businesses)}"
    
    # Check data type access (CRITICAL for finance data)
    requested_data_types = intent.get("requested_data_types", [])
    
    if "finance" in requested_data_types and not data_access.get("finance_data", False):
        return False, "You don't have access to financial data. Please contact your administrator."
    
    if "cost" in requested_data_types and not data_access.get("transfer_cost", False):
        return False, "You don't have access to cost data. Please contact your administrator."
    
    if "profit" in requested_data_types and not data_access.get("gross_profit", False):
        return False, "You don't have access to profit data. Please contact your administrator."
    
    # Check customer access
    requested_customers = intent.get("requested_customers", "all")
    if requested_customers != "all":
        allowed_customers = permissions.get("customers", [])
        if allowed_customers != "*":
            unauthorized_customers = set(requested_customers) - set(allowed_customers)
            if unauthorized_customers:
                return False, f"You don't have access to customers: {', '.join(unauthorized_customers)}"
    
    # All checks passed
    return True, ""


# Enhanced chatbot endpoint with RBAC
@router.post("/insights/chat")
async def insights_chat_with_rbac(
    request: InsightsChatRequest,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    AI Chatbot with comprehensive RBAC validation
    """
    user_message = request.message
    conversation_history = request.conversation_history or []
    
    # STEP 1: Extract intent from question
    logger.info(f"🔍 Extracting data access intent from question...")
    intent = await extract_data_access_intent(user_message, conversation_history)
    logger.info(f"📋 Intent: {intent}")
    
    # STEP 2: Validate RBAC access BEFORE querying database
    logger.info(f"🔒 Validating RBAC access...")
    has_access, denial_reason = await validate_rbac_access(email, intent, db)
    
    if not has_access:
        # ❌ ACCESS DENIED
        logger.warning(f"❌ Access denied for {email}: {denial_reason}")
        return {
            "response": f"⛔ Access Denied\n\n{denial_reason}\n\nIf you believe this is an error, please contact your administrator.",
            "access_denied": True,
            "reason": denial_reason
        }
    
    # ✅ ACCESS GRANTED - Proceed with query
    logger.info(f"✅ Access granted for {email}")
    
    # STEP 3: Get user permissions for query filters
    user = await db.users.find_one({"email": email})
    permissions = user.get("permissions", {})
    
    # STEP 4: Continue with normal chatbot flow (with RBAC filters applied)
    # ... (existing chatbot logic: LLM query planning, MongoDB execution, analysis)
    
    # Ensure all MongoDB queries include RBAC filters
    base_query = {}
    final_query = await apply_rbac_filters(email, base_query, db)
    
    # Execute queries and generate response
    response = await process_chat_with_filters(
        user_message,
        final_query,
        conversation_history,
        db
    )
    
    return response
```

### 5.7 User Permission Management

#### Database Schema: users Collection

```json
{
  "_id": ObjectId("..."),
  "email": "john.doe@company.com",
  "name": "John Doe",
  "role": "brand_manager",
  "department": "Sales",
  "created_at": "2025-01-15T10:00:00Z",
  "permissions": {
    "businesses": ["Business A", "Business C"],
    "brands": ["Brand X", "Brand Y", "Brand Z"],
    "channels": ["Direct", "Online", "Retail"],
    "customers": "*",
    "categories": ["Electronics", "Home Goods"],
    "sub_categories": "*",
    "skus": "*",
    "data_access": {
      "revenue": true,
      "units": true,
      "gross_profit": true,
      "transfer_cost": false,
      "group_cost": false,
      "finance_data": false,
      "lta": false,
      "price_downs": false
    },
    "time_access": {
      "years": [2023, 2024, 2025],
      "all_historical": false
    },
    "geographic_access": {
      "countries": "*",
      "regions": "*"
    }
  },
  "active": true
}
```

#### Admin UI for Permission Management

Create an admin interface where admins can:
1. Create/edit user accounts
2. Assign roles (with pre-defined permission templates)
3. Customize permissions per user
4. Audit user access logs
5. Revoke/grant access in real-time

### 5.8 Audit Logging

```python
# Log all data access attempts
async def log_data_access(
    user_email: str,
    action: str,
    resource_type: str,
    resource_ids: List[str],
    access_granted: bool,
    query: Dict,
    db: AsyncIOMotorDatabase
):
    """
    Log all data access for compliance and security
    """
    await db.access_logs.insert_one({
        "user_email": user_email,
        "action": action,  # "dashboard_view", "chatbot_query", "report_download"
        "resource_type": resource_type,  # "brand", "customer", "financial_data"
        "resource_ids": resource_ids,
        "access_granted": access_granted,
        "timestamp": datetime.utcnow(),
        "query": query,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    })
```

### 5.9 RBAC Benefits

| Benefit | Impact |
|---------|--------|
| **Data Security** | Users only see data they're authorized to access |
| **Compliance** | Meets GDPR, SOC2 requirements for access control |
| **Competitive Protection** | Prevent unauthorized access to sensitive data |
| **Role Clarity** | Clear separation of responsibilities |
| **Audit Trail** | Complete visibility into who accessed what data |
| **Scalability** | Easy to onboard new users with appropriate permissions |

### 5.10 Implementation Checklist

#### Phase 1: Foundation (2-3 weeks)
- [ ] Design user permission schema
- [ ] Create `users` collection with permission structure
- [ ] Implement JWT token with embedded permissions
- [ ] Create RBAC middleware for API endpoints
- [ ] Add `apply_rbac_filters()` function

#### Phase 2: Dashboard RBAC (2-3 weeks)
- [ ] Apply RBAC to Executive Dashboard
- [ ] Apply RBAC to Business Compass
- [ ] Apply RBAC to Customer Deep Intelligence
- [ ] Apply RBAC to Sales Analysis
- [ ] Test with different user roles

#### Phase 3: Chatbot RBAC (3-4 weeks)
- [ ] Implement intent extraction with LLM
- [ ] Create `validate_rbac_access()` function
- [ ] Add access denial responses
- [ ] Test with edge cases (e.g., "show me all financial data")
- [ ] Implement audit logging

#### Phase 4: Admin UI (2-3 weeks)
- [ ] Create user management interface
- [ ] Role templates (Admin, Manager, Sales, etc.)
- [ ] Permission editor
- [ ] Access log viewer
- [ ] Bulk permission updates

#### Phase 5: Testing & Rollout (2 weeks)
- [ ] Security testing
- [ ] User acceptance testing
- [ ] Performance testing (RBAC shouldn't slow queries)
- [ ] Documentation
- [ ] Training for admins

**Total Timeline: 11-15 weeks**

### 5.11 Performance Considerations

#### Optimize RBAC Queries

```python
# ✅ GOOD: Use MongoDB indexes
# Create compound index for RBAC filters
await db.business_data.create_index([
    ("Business", 1),
    ("Brand", 1),
    ("Customer", 1),
    ("Year", -1)
])

# ✅ GOOD: Cache user permissions
# Cache permissions in Redis for 5 minutes
user_permissions = await redis.get(f"permissions:{user_email}")
if not user_permissions:
    user_permissions = await db.users.find_one({"email": user_email})
    await redis.setex(f"permissions:{user_email}", 300, json.dumps(user_permissions))

# ❌ BAD: Fetching permissions on every request without caching
```

#### Expected Performance Impact

| Scenario | Without RBAC | With RBAC (optimized) | Overhead |
|----------|-------------|----------------------|----------|
| Dashboard load | 300ms | 320ms | +20ms (7%) |
| Chatbot query | 2500ms | 2550ms | +50ms (2%) |
| Filter options | 100ms | 110ms | +10ms (10%) |

**Conclusion**: RBAC adds minimal overhead (2-10%) when properly optimized with caching and indexes.

---

## 6. Database Migration Recommendations

### 6.1 Current MongoDB Performance Issues

#### Pain Points:
1. **Aggregation Performance**: Complex aggregations on large datasets (1M+ records) take 500-1000ms
2. **Multiple Collections**: Need to join data across `business_data` and `shopify_data`
3. **Real-time Analytics**: Dashboard queries block when multiple users access simultaneously
4. **Memory Usage**: Large working sets require significant RAM for aggregations
5. **Scalability**: Vertical scaling only (limited horizontal scaling for analytics)

#### Query Performance Benchmarks (Current):
```
Simple aggregation (group by):           100-200ms
Complex aggregation (multiple stages):   500-1000ms
Top N queries with sorting:              200-400ms
Time series aggregations:                800-1500ms
Concurrent users (10+):                  2000-3000ms (degradation)
```

### 6.2 Why Consider Migration?

1. **Faster Analytics**: OLAP databases are optimized for analytical queries
2. **Better Concurrency**: Handle multiple simultaneous dashboard queries
3. **Lower Costs**: More efficient resource utilization
4. **Improved UX**: Sub-100ms query times for better user experience
5. **Scalability**: Better horizontal scaling for growing data volumes

---

## 7. ClickHouse Analysis

### 7.1 What is ClickHouse?

**ClickHouse** is an open-source **columnar OLAP database** designed for real-time analytical queries on large datasets.

#### Key Characteristics:
- **Columnar Storage**: Stores data by column, not row (perfect for analytics)
- **Extremely Fast**: 100-1000x faster than traditional databases for analytical queries
- **Horizontally Scalable**: Add nodes to scale linearly
- **Real-time Ingestion**: Can handle millions of inserts per second
- **SQL Support**: Standard SQL with analytics extensions
- **Compression**: 10-100x better compression than row-based databases

### 7.2 ClickHouse vs MongoDB: Feature Comparison

| Feature | MongoDB | ClickHouse | Winner |
|---------|---------|-----------|--------|
| **Read Performance (Analytics)** | Good | Excellent (100x faster) | ✅ ClickHouse |
| **Write Performance** | Excellent | Very Good | ⚖️ Tie |
| **Aggregations** | Good (with indexes) | Excellent (native) | ✅ ClickHouse |
| **Concurrent Queries** | Moderate | Excellent | ✅ ClickHouse |
| **Data Compression** | Good (2-5x) | Excellent (10-100x) | ✅ ClickHouse |
| **Schema Flexibility** | Excellent (schemaless) | Moderate (schema required) | ✅ MongoDB |
| **Horizontal Scaling** | Limited (sharding) | Excellent (native) | ✅ ClickHouse |
| **Real-time Updates** | Excellent | Moderate (eventual consistency) | ✅ MongoDB |
| **Joins** | Limited (lookup) | Excellent (SQL joins) | ✅ ClickHouse |
| **Learning Curve** | Moderate | Moderate | ⚖️ Tie |
| **Cost** | Moderate | Low (open-source) | ✅ ClickHouse |
| **Community & Support** | Excellent | Very Good | ✅ MongoDB |
| **RBAC Support** | Native (built-in) | Native (SQL-based) | ⚖️ Tie |

**Important Note on RBAC**: Both MongoDB and ClickHouse support row-level security, but implementation differs:
- **MongoDB**: Use aggregation pipeline with `$match` filters based on user permissions
- **ClickHouse**: Use SQL `WHERE` clauses with user permission filters, or use ClickHouse's native row-level security policies

### 7.3 Performance Benchmarks: MongoDB vs ClickHouse

Based on industry benchmarks and similar use cases:

#### Query Performance Comparison

| Query Type | MongoDB | ClickHouse | Speed Improvement |
|-----------|---------|-----------|-------------------|
| Simple aggregation (SUM, COUNT) | 100-200ms | 5-20ms | **10-20x faster** |
| GROUP BY with aggregation | 500-1000ms | 20-50ms | **25-50x faster** |
| Top N queries (ORDER BY + LIMIT) | 200-400ms | 10-30ms | **10-20x faster** |
| Time series analysis | 800-1500ms | 30-80ms | **20-40x faster** |
| Multi-table joins | 1000-2000ms | 50-150ms | **15-30x faster** |
| Complex nested aggregations | 2000-5000ms | 100-300ms | **20-40x faster** |

#### Concurrency Performance (10 simultaneous users)

| Metric | MongoDB | ClickHouse | Improvement |
|--------|---------|-----------|-------------|
| Average query time | 2000-3000ms | 50-150ms | **20-40x faster** |
| 95th percentile | 4000ms | 200ms | **20x faster** |
| Throughput (queries/sec) | 5-10 | 200-500 | **40-50x higher** |

#### Data Compression

| Data Size | MongoDB | ClickHouse | Savings |
|-----------|---------|-----------|---------|
| Raw CSV (10GB) | 8GB | 0.8GB | **90% savings** |
| With indexes | 12GB | 1.2GB | **90% savings** |

### 7.4 ClickHouse Advantages for BizPulse

#### ✅ **Perfect Fit for Use Case**

1. **Dashboard Queries**: ClickHouse excels at aggregations, GROUP BY, TOP N
2. **Time Series Data**: Native support for date/time queries and windowing
3. **Concurrent Users**: No performance degradation with multiple dashboards open
4. **Large Datasets**: Can handle billions of rows without performance issues

#### ✅ **Specific Benefits**

```sql
-- Example: Top 10 Customers Query
-- MongoDB Aggregation Pipeline: ~500ms
-- ClickHouse SQL: ~20ms (25x faster)

SELECT 
    Customer,
    SUM(Revenue) as total_revenue,
    SUM(Gross_Profit) as total_profit,
    COUNT(*) as order_count
FROM business_data
WHERE Year = 2024
GROUP BY Customer
ORDER BY total_revenue DESC
LIMIT 10
```

#### ✅ **Cost Savings**

- **Storage**: 90% reduction due to compression
- **Compute**: 10-50x less CPU for same queries
- **Scaling**: Horizontal scaling is cheaper than MongoDB sharding

### 7.5 ClickHouse Disadvantages

#### ⚠️ **Considerations**

1. **Schema Required**: Must define schema upfront (unlike MongoDB's flexible schema)
2. **Update/Delete Performance**: Not optimized for frequent updates (eventual consistency)
3. **Transactional Support**: Limited ACID transactions (not for OLTP)
4. **Learning Curve**: Team needs to learn ClickHouse-specific SQL
5. **Ecosystem**: Smaller ecosystem compared to MongoDB

#### ⚠️ **When NOT to Use ClickHouse**

- High-frequency updates/deletes on same records
- Need for immediate consistency
- Complex document structures that change frequently
- Transactional operations (e.g., order processing)

### 7.6 Recommendation: Hybrid Approach

#### **Best Architecture: Use Both MongoDB + ClickHouse**

```
┌─────────────┐
│  Data Source│
│  (Azure)    │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│         ETL Pipeline                    │
│  (Load data from Azure to both DBs)     │
└────┬─────────────────────────┬──────────┘
     │                         │
     ↓                         ↓
┌──────────┐            ┌─────────────┐
│ MongoDB  │            │ ClickHouse  │
│          │            │             │
│ - Flexible│            │ - Analytics │
│ - Updates│            │ - Dashboards│
│ - OLTP   │            │ - Reporting │
└──────────┘            └─────────────┘
     │                         │
     │                         │
     ↓                         ↓
┌──────────┐            ┌─────────────┐
│ AI Chat  │            │  Dashboards │
│ Real-time│            │  (All views)│
└──────────┘            └─────────────┘
```

#### **Data Split Strategy**:

| Use Case | Database | Reason |
|----------|----------|--------|
| **Dashboards** (Executive, Business Compass, etc.) | ✅ ClickHouse | Fast aggregations, concurrent queries |
| **Customer Deep Intelligence** | ✅ ClickHouse | Time series analysis, complex aggregations |
| **AI Chatbot** | ⚖️ Both | Use ClickHouse for analytics, MongoDB for real-time context |
| **Data Ingestion** | ✅ MongoDB → ClickHouse | Load to MongoDB first, sync to ClickHouse |
| **User Sessions & Auth** | ✅ MongoDB | Transactional, frequent updates |

---

## 8. Alternative Solutions

### 8.1 Alternative OLAP Databases

#### **Option 1: TimescaleDB (PostgreSQL Extension)**

**Pros:**
- SQL-based (easier migration from MongoDB)
- Excellent time-series support
- ACID compliance
- Strong ecosystem

**Cons:**
- Not as fast as ClickHouse for pure analytics
- Vertical scaling primarily
- Higher memory requirements

**Performance:**
- 5-10x faster than MongoDB
- 3-5x slower than ClickHouse

**Recommendation:** ⭐⭐⭐ Good option if you need ACID and prefer PostgreSQL

---

#### **Option 2: Apache Druid**

**Pros:**
- Sub-second query latency
- Real-time streaming ingestion
- Excellent for time-series data
- Good for customer-facing dashboards

**Cons:**
- Complex setup and operations
- Steeper learning curve
- Limited community compared to ClickHouse

**Performance:**
- Similar to ClickHouse (10-50x faster than MongoDB)

**Recommendation:** ⭐⭐⭐⭐ Great for real-time analytics, but more complex

---

#### **Option 3: Google BigQuery**

**Pros:**
- Fully managed (no ops)
- Scales to petabytes
- SQL-based
- Excellent for data warehousing

**Cons:**
- Cloud vendor lock-in
- Higher costs for frequent queries
- Network latency (data in Google Cloud)
- Query costs can be unpredictable

**Performance:**
- Excellent for large datasets
- Similar to ClickHouse for most queries

**Recommendation:** ⭐⭐⭐⭐ Great if you want managed service and can accept costs

---

#### **Option 4: DuckDB**

**Pros:**
- Embedded database (no server)
- Extremely fast for local analytics
- SQL-based
- Perfect for development/testing

**Cons:**
- Not suitable for production multi-user environment
- Single-machine only
- No concurrent write support

**Performance:**
- Faster than ClickHouse for single-machine use
- Not suitable for multi-user dashboards

**Recommendation:** ⭐⭐ Good for local development, not for production

---

#### **Option 5: Stay with MongoDB + Optimizations**

**Pros:**
- No migration needed
- Team already knows it
- Flexible schema
- Good for current data volumes

**Cons:**
- Performance ceiling already reached
- Won't scale efficiently for 10x data growth
- Higher costs for equivalent performance

**Optimization Strategies:**
- Add more indexes (Year + Month + Customer compound indexes)
- Use MongoDB aggregation pipeline optimization
- Implement caching layer (Redis)
- Use read replicas for dashboards

**Performance Improvement:**
- 2-3x faster with optimizations
- Still 10-20x slower than ClickHouse

**Recommendation:** ⭐⭐⭐ Acceptable for near-term if budget is tight

---

### 8.2 Comparison Matrix

| Database | Speed | Scalability | Cost | Complexity | Fit for BizPulse | Overall Rating |
|----------|-------|-------------|------|------------|------------------|----------------|
| **ClickHouse** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **🏆 #1 Choice** |
| **BigQuery** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **#2 Choice** |
| **Druid** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | **#3 Choice** |
| **TimescaleDB** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | #4 Choice |
| **MongoDB (optimized)** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Current |

---

## 9. Migration Strategy

### 9.1 Phase 1: Proof of Concept (2-3 weeks)

#### Goals:
- Validate ClickHouse performance with actual data
- Test migration scripts
- Benchmark query performance
- Verify AI chatbot integration

#### Tasks:
1. **Setup ClickHouse instance** (ClickHouse Cloud or self-hosted)
2. **Create schema** for business_data and shopify_data tables
3. **Migrate 1 month of data** (test dataset)
4. **Convert 10 key queries** from MongoDB to ClickHouse SQL
5. **Run performance benchmarks**
6. **Test AI chatbot** with ClickHouse data
7. **Test RBAC implementation** with ClickHouse row-level security

#### Success Criteria:
- ✅ Queries are 10x faster than MongoDB
- ✅ Data accuracy matches MongoDB results
- ✅ AI chatbot works with ClickHouse
- ✅ RBAC filters work correctly (users only see authorized data)
- ✅ No show-stopping issues identified

---

### 9.2 Phase 2: Hybrid Setup (1-2 months)

#### Goals:
- Run MongoDB and ClickHouse in parallel
- Migrate dashboards one by one
- Ensure data consistency

#### Architecture:
```
Azure Data → MongoDB (primary) → ClickHouse (sync)
                ↓                       ↓
         AI Chatbot              Dashboards
```

#### Tasks:
1. **Setup ETL pipeline** (sync MongoDB → ClickHouse)
2. **Migrate Executive Dashboard** to ClickHouse
3. **Migrate Business Compass** to ClickHouse
4. **Migrate Customer Deep Intelligence** to ClickHouse
5. **Update AI chatbot** to use ClickHouse for analytics
6. **Monitor performance and accuracy**

---

### 9.3 Phase 3: Full Migration (1-2 months)

#### Goals:
- Complete migration of all features
- Decommission MongoDB (or keep for non-analytics use)
- Optimize ClickHouse configuration

#### Tasks:
1. **Migrate remaining dashboards**
2. **Implement data retention policies** in ClickHouse
3. **Setup monitoring and alerts**
4. **Train team** on ClickHouse operations
5. **Document new architecture**

---

### 9.4 Migration Scripts

#### MongoDB to ClickHouse Data Sync

```python
# Python script to sync data from MongoDB to ClickHouse
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from clickhouse_driver import Client as ClickHouseClient

async def sync_mongodb_to_clickhouse():
    # MongoDB connection
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    mongo_db = mongo_client["bizpulse"]
    
    # ClickHouse connection
    ch_client = ClickHouseClient(host='localhost')
    
    # Create ClickHouse table (if not exists)
    ch_client.execute("""
    CREATE TABLE IF NOT EXISTS business_data (
        Year UInt16,
        Month UInt8,
        Month_Name String,
        Customer String,
        Brand String,
        Business String,
        Channel String,
        Category String,
        Revenue Float64,
        Gross_Profit Float64,
        Units Float64,
        created_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (Year, Month, Customer)
    """)
    
    # Fetch data from MongoDB
    cursor = mongo_db.business_data.find({})
    
    # Batch insert into ClickHouse
    batch = []
    async for doc in cursor:
        batch.append((
            doc.get('Year'),
            doc.get('Month'),
            doc.get('Month_Name'),
            doc.get('Customer'),
            doc.get('Brand'),
            doc.get('Business'),
            doc.get('Channel'),
            doc.get('Category'),
            doc.get('Revenue', 0),
            doc.get('Gross_Profit', 0),
            doc.get('Units', 0)
        ))
        
        # Insert in batches of 10,000
        if len(batch) >= 10000:
            ch_client.execute(
                'INSERT INTO business_data VALUES',
                batch
            )
            batch = []
    
    # Insert remaining records
    if batch:
        ch_client.execute('INSERT INTO business_data VALUES', batch)
    
    print(f"✅ Sync completed!")

# Run sync
asyncio.run(sync_mongodb_to_clickhouse())
```

#### Query Conversion Examples

**MongoDB Aggregation:**
```python
# MongoDB: Top 10 Customers by Revenue
pipeline = [
    {"$match": {"Year": 2024}},
    {
        "$group": {
            "_id": "$Customer",
            "revenue": {"$sum": "$Revenue"},
            "profit": {"$sum": "$Gross_Profit"}
        }
    },
    {"$sort": {"revenue": -1}},
    {"$limit": 10}
]

results = await db.business_data.aggregate(pipeline).to_list(10)
```

**ClickHouse SQL:**
```sql
-- ClickHouse: Top 10 Customers by Revenue
SELECT 
    Customer,
    SUM(Revenue) as revenue,
    SUM(Gross_Profit) as profit
FROM business_data
WHERE Year = 2024
GROUP BY Customer
ORDER BY revenue DESC
LIMIT 10
```

#### RBAC Implementation in ClickHouse

**Option 1: Application-Level RBAC (Recommended)**
```python
# Apply RBAC filters in Python (same as MongoDB approach)
async def get_clickhouse_data_with_rbac(
    user_email: str,
    base_query: str,
    db: AsyncIOMotorDatabase
):
    # Get user permissions from MongoDB
    user = await db.users.find_one({"email": user_email})
    permissions = user.get("permissions", {})
    
    # Build WHERE clause with RBAC filters
    rbac_conditions = []
    
    if permissions.get("businesses") and permissions["businesses"] != "*":
        businesses = "','".join(permissions["businesses"])
        rbac_conditions.append(f"Business IN ('{businesses}')")
    
    if permissions.get("brands") and permissions["brands"] != "*":
        brands = "','".join(permissions["brands"])
        rbac_conditions.append(f"Brand IN ('{brands}')")
    
    # Combine with base query
    if rbac_conditions:
        where_clause = " AND ".join(rbac_conditions)
        if "WHERE" in base_query:
            final_query = base_query.replace("WHERE", f"WHERE {where_clause} AND")
        else:
            final_query = base_query + f" WHERE {where_clause}"
    else:
        final_query = base_query
    
    # Execute ClickHouse query
    result = clickhouse_client.execute(final_query)
    return result
```

**Option 2: ClickHouse Row-Level Security (Native)**
```sql
-- Create row policy for user (ClickHouse native RBAC)
CREATE ROW POLICY brand_manager_policy ON business_data
FOR SELECT
USING (
    Business IN ('Business A', 'Business C') 
    AND Brand IN ('Brand X', 'Brand Y')
)
TO brand_manager_user;

-- Now when brand_manager_user queries, ClickHouse automatically filters:
SELECT * FROM business_data WHERE Year = 2024;
-- ClickHouse internally adds: AND Business IN (...) AND Brand IN (...)
```

---

## 10. Performance Benchmarks

### 10.1 Expected Performance Improvements

Based on ClickHouse migration:

| Dashboard Screen | Current (MongoDB) | After Migration (ClickHouse) | Improvement |
|-----------------|-------------------|------------------------------|-------------|
| Executive Dashboard | 500ms | 25ms | **20x faster** |
| Business Compass | 300ms | 15ms | **20x faster** |
| Customer Deep Intelligence | 1000ms | 50ms | **20x faster** |
| Top 10 Charts (all 4) | 800ms | 40ms | **20x faster** |
| AI Chatbot queries | 600ms | 30ms | **20x faster** |

### 10.2 Cost Analysis

#### Current MongoDB Atlas Costs (estimated):
```
Instance: M30 (8GB RAM, 2 vCPU)
Storage: 100GB
Cost: ~$500/month
```

#### ClickHouse Cloud Costs (estimated):
```
Instance: Medium (8GB RAM, 2 vCPU)
Storage: 10GB (compressed from 100GB)
Cost: ~$200/month

Savings: $300/month = $3,600/year
```

### 10.3 Scalability Projection

| Data Volume | MongoDB Performance | ClickHouse Performance |
|-------------|-------------------|----------------------|
| Current (1M records) | 500ms | 25ms |
| 10M records (10x growth) | 3000ms | 80ms |
| 100M records (100x growth) | 20000ms | 300ms |
| 1B records (1000x growth) | Requires sharding | 1000ms |

---

## 10. Final Recommendations

### 🏆 **Recommended Approach: Hybrid MongoDB + ClickHouse**

#### **Phase 1 (Now):** Keep MongoDB, Optimize
- Add compound indexes
- Implement Redis caching for frequently accessed data
- **Timeline:** 1-2 weeks
- **Cost:** Minimal
- **Benefit:** 2-3x performance improvement

#### **Phase 2 (Q2 2026):** Proof of Concept with ClickHouse
- Setup ClickHouse instance
- Migrate Executive Dashboard
- Run parallel for 1 month
- **Timeline:** 3-4 weeks
- **Cost:** ~$200/month
- **Benefit:** Validate 10-20x performance gains

#### **Phase 3 (Q3 2026):** Full Migration
- Migrate all dashboards to ClickHouse
- Keep MongoDB for AI chatbot context and user sessions
- **Timeline:** 2-3 months
- **Cost:** $200/month (ClickHouse) + $200/month (MongoDB, reduced tier)
- **Benefit:** Sub-100ms queries, better UX, scalability

---

### 📊 **Summary Decision Matrix**

| Factor | MongoDB (Optimized) | ClickHouse Migration |
|--------|-------------------|---------------------|
| **Performance** | ⭐⭐⭐ (Good) | ⭐⭐⭐⭐⭐ (Excellent) |
| **Cost** | $500/month | $400/month (hybrid) |
| **Migration Risk** | ✅ None | ⚠️ Medium |
| **Team Learning** | ✅ None | ⚠️ Required |
| **Scalability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Time to Implement** | 2 weeks | 3-4 months |

---

### ✅ **Action Items for Senior Technical Team**

#### Immediate Priority (Within 2 weeks):
1. **Review this document** and discuss tradeoffs
2. **Prioritize RBAC implementation** (critical security requirement)
3. **Plan MongoDB optimization** as interim solution for performance
4. **Approve POC budget** for ClickHouse testing (~$500)
5. **Assign RBAC lead** to architect permission system

#### Short-term (1-3 months):
6. **Implement RBAC** in current MongoDB setup (see Section 5)
7. **Setup ClickHouse POC** with sample data
8. **Test RBAC** with ClickHouse row-level security
9. **Benchmark performance** gains
10. **Schedule decision meeting** after POC results

#### Critical Notes:
- **RBAC is mandatory** and should be implemented FIRST (regardless of database choice)
- **Local LLM (Qwen:32b)** is excellent for data privacy - keep this architecture
- **ClickHouse migration** can happen in parallel with RBAC (they're independent)

---

## Appendix

### A. Useful Resources

#### ClickHouse Documentation
- Official Docs: https://clickhouse.com/docs
- Performance Tuning: https://clickhouse.com/docs/en/operations/performance
- Migration Guide: https://clickhouse.com/docs/en/guides/developer/migrating-to-clickhouse

#### MongoDB Optimization
- Aggregation Pipeline Optimization: https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/
- Index Strategies: https://www.mongodb.com/docs/manual/indexes/

#### Benchmarking Tools
- ClickHouse Benchmark: https://github.com/ClickHouse/ClickBench
- MongoDB Performance: https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/

### B. Contact Information

For questions about this document:
- **Technical Lead:** [Your Name]
- **Database Team:** [Team Email]
- **AI/ML Team:** [Team Email]

---

**Document End**
