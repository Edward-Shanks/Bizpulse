# Customer Deep Intelligence API Documentation

This document provides comprehensive API documentation for the Customer Deep Intelligence chatbot endpoints.

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <your_jwt_token>
```

---

## API Endpoints

### 1. Get Filter Options
Get available filter options (years and months) from Shopify data.

**Endpoint:** `GET /analytics/customer-insights/filters`

**Authentication:** Required

**Query Parameters:** None

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/customer-insights/filters" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response Example:**
```json
{
  "years": [2024, 2025],
  "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
}
```

**Response Fields:**
- `years` (array of integers): Available years in the data
- `months` (array of strings): Available months in the data

---

### 2. Get Customer Insights Data
Get customer insights data with optional filters.

**Endpoint:** `GET /analytics/customer-insights`

**Authentication:** Required

**Query Parameters:**
- `years` (optional, string): Comma-separated list of years (e.g., "2024,2025")
- `months` (optional, string): Comma-separated list of month names (e.g., "January,February")

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/customer-insights?years=2025&months=January" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response Example:**
```json
{
  "newVsReturning": [
    {"type": "New", "orders": 150, "sales": 5000.50, "unique_customers": 120},
    {"type": "Returning", "orders": 300, "sales": 15000.75, "unique_customers": 200}
  ],
  "channelPerformance": [
    {"channel": "order", "sales": 18000.25, "orders": 400, "customers": 300}
  ],
  "summary": {
    "totalCustomers": 320,
    "totalOrders": 450,
    "totalSales": 20001.25,
    "avgOrderValue": 44.45
  }
}
```

---

### 3. Customer Insights Chat (Main Chatbot)
Main chatbot endpoint for Customer Deep Intelligence page.

**Endpoint:** `POST /analytics/customer-insights/chat`

**Authentication:** Required

**Request Body:**
```json
{
  "message": "What is the total gross sales?",
  "chart_title": null,
  "context": {},
  "session_id": "session_123",
  "conversation_history": []
}
```

**Request Body Fields:**
- `message` (string, required): User's question/message
- `chart_title` (string, optional): Title of the chart being viewed
- `context` (object, optional): Additional context (filters, etc.)
- `session_id` (string, optional): Session identifier
- `conversation_history` (array, optional): Previous conversation messages

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/analytics/customer-insights/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total gross sales?",
    "context": {},
    "conversation_history": []
  }'
```

**Response Example:**
```json
{
  "response": "Based on the Shopify customer data, the total gross sales is €299,132,414.31. This represents the cumulative gross sales across all orders in the dataset...",
  "timestamp": "01:30 PM IST on November 29, 2025",
  "context": "Shopify Customer Data Analysis for 'What is the total gross sales?':\n\nSummary Statistics:\n- Total Sales: €299,132,414.31...",
  "data": {
    "pivot_table": [
      {
        "Total sales": 299132414.31,
        "Orders": 15000,
        "Customers": 5000
      }
    ],
    "columns": ["Total sales"],
    "filters": {},
    "is_trend_query": false,
    "total_rows": 15972,
    "chart_title": null
  }
}
```

---

### 4. Customer Insights View Insights Chat
Chatbot endpoint for the "View Insights" modal in Customer Deep Intelligence.

**Endpoint:** `POST /analytics/customer-insights/view-insights/chat`

**Authentication:** Required

**Request Body:**
```json
{
  "message": "What are the top performing channels?",
  "chart_title": "Sales Channel Performance",
  "context": {
    "year": 2025,
    "selectedYears": [2025],
    "selectedMonths": ["January", "February"],
    "selectedChannels": []
  },
  "session_id": "session_456",
  "conversation_history": [
    {
      "role": "user",
      "content": "What is the total sales?"
    },
    {
      "role": "assistant",
      "content": "The total sales is €299,132,414.31..."
    }
  ]
}
```

**Request Body Fields:**
- `message` (string, required): User's question
- `chart_title` (string, optional): Title of the chart being viewed
- `context` (object, optional): Filter context
  - `year` or `selectedYears`: Year filter
  - `selectedMonths`: Month filter
  - `selectedChannels`: Channel filter
  - `selectedCustomerTypes`: Customer type filter
  - `selectedCountries`: Country filter
- `session_id` (string, optional): Session identifier
- `conversation_history` (array, optional): Previous messages

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/analytics/customer-insights/view-insights/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the top performing channels?",
    "chart_title": "Sales Channel Performance",
    "context": {
      "selectedYears": [2025],
      "selectedMonths": ["January"]
    },
    "conversation_history": []
  }'
```

**Response Example:**
```json
{
  "response": "Based on the customer data for January 2025, the top performing channels are:\n\n1. **Google** - €45,234.56 in sales with 234 orders\n2. **Direct** - €32,123.45 in sales with 189 orders\n3. **Facebook** - €28,987.65 in sales with 156 orders...",
  "timestamp": "01:35 PM IST on November 29, 2025",
  "context": "Shopify Customer Data Analysis for 'What are the top performing channels?':\n\nSummary Statistics:\n- Total Sales: €106,345.66...",
  "data": {
    "pivot_table": [
      {
        "Referring channel": "Google",
        "Total sales": 45234.56,
        "Orders": 234,
        "Customers": 200
      },
      {
        "Referring channel": "Direct",
        "Total sales": 32123.45,
        "Orders": 189,
        "Customers": 150
      }
    ],
    "columns": ["Total sales", "Orders"],
    "filters": {
      "Year": 2025,
      "MonthName": "January"
    },
    "is_trend_query": false,
    "total_rows": 1234,
    "chart_title": "Sales Channel Performance"
  }
}
```

---

### 5. Health Check
Check if the customer insights chat endpoint is accessible.

**Endpoint:** `GET /analytics/customer-insights/chat/health`

**Authentication:** Not required

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/customer-insights/chat/health"
```

**Response Example:**
```json
{
  "status": "ok",
  "message": "Customer insights chat route is registered",
  "path": "/api/analytics/customer-insights/chat"
}
```

---

### 6. Test Endpoint
Simple test endpoint for customer insights chat.

**Endpoint:** `GET /analytics/customer-insights/chat/test`

**Authentication:** Required

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/customer-insights/chat/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response Example:**
```json
{
  "status": "ok",
  "message": "Customer insights chat endpoint is accessible",
  "endpoint": "/api/analytics/customer-insights/chat",
  "method": "POST"
}
```

---

## Example Use Cases

### Example 1: Simple Question
**Question:** "What is the total sales?"

**Request:**
```json
{
  "message": "What is the total sales?",
  "context": {},
  "conversation_history": []
}
```

### Example 2: Question with Filters
**Question:** "What are the sales for January 2025?"

**Request:**
```json
{
  "message": "What are the sales for January 2025?",
  "context": {
    "selectedYears": [2025],
    "selectedMonths": ["January"]
  },
  "conversation_history": []
}
```

### Example 3: Follow-up Question
**Question:** "What about February?"

**Request:**
```json
{
  "message": "What about February?",
  "context": {
    "selectedYears": [2025]
  },
  "conversation_history": [
    {
      "role": "user",
      "content": "What are the sales for January 2025?"
    },
    {
      "role": "assistant",
      "content": "The sales for January 2025 were €45,234.56..."
    }
  ]
}
```

### Example 4: Chart-Specific Question
**Question:** "Why is Google performing better than other channels?"

**Request:**
```json
{
  "message": "Why is Google performing better than other channels?",
  "chart_title": "Sales Channel Performance",
  "context": {
    "selectedYears": [2025]
  },
  "conversation_history": []
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "shopify_data.csv file not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error processing customer view insights chat: <error_message>"
}
```

---

## Data Schema

### CustomerInsightsChatRequest
```typescript
{
  message: string;                    // Required: User's question
  chart_title?: string;               // Optional: Chart title
  context?: {                         // Optional: Filter context
    year?: number;
    selectedYears?: number[];
    selectedMonths?: string[];
    selectedChannels?: string[];
    selectedCustomerTypes?: string[];
    selectedCountries?: string[];
  };
  session_id?: string;                // Optional: Session ID
  conversation_history?: Array<{      // Optional: Conversation history
    role: "user" | "assistant";
    content: string;
  }>;
}
```

### CustomerInsightsChatResponse
```typescript
{
  response: string;                   // AI-generated response
  timestamp?: string;                 // Response timestamp
  context?: string;                   // Data context used
  data?: {                            // Additional data
    pivot_table?: Array<Record<string, any>>;
    columns?: string[];
    filters?: Record<string, any>;
    is_trend_query?: boolean;
    total_rows?: number;
    chart_title?: string;
  };
}
```

---

## Testing with Postman

### Import Collection
1. Open Postman
2. Create a new collection: "Customer Deep Intelligence APIs"
3. Add environment variables:
   - `base_url`: `http://localhost:8000/api`
   - `token`: Your JWT token

### Example Postman Request
**Method:** POST  
**URL:** `{{base_url}}/analytics/customer-insights/view-insights/chat`  
**Headers:**
```
Authorization: Bearer {{token}}
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
  "message": "What is the total gross sales?",
  "context": {},
  "conversation_history": []
}
```

---

## Testing with cURL

### Get Filters
```bash
curl -X GET "http://localhost:8000/api/analytics/customer-insights/filters" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Chat Request
```bash
curl -X POST "http://localhost:8000/api/analytics/customer-insights/view-insights/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total sales?",
    "context": {},
    "conversation_history": []
  }'
```

---

## Swagger/OpenAPI Documentation

Access interactive API documentation at:
```
http://localhost:8000/docs
```

Or ReDoc documentation at:
```
http://localhost:8000/redoc
```

---

## Notes

1. **Data Source:** All endpoints use `shopify_data.csv` from the backend folder
2. **AI Model:** Uses Perplexity AI (sonar-pro model) for generating responses
3. **Filtering:** Filters are applied to the Shopify data before analysis
4. **Conversation History:** Maintains context across multiple messages
5. **Numpy Types:** All numpy types are automatically converted to native Python types for JSON serialization

---

## Support

For issues or questions, check the server logs or contact the development team.

