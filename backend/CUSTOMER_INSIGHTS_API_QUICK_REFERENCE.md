# Customer Deep Intelligence API - Quick Reference

## 🚀 Quick Start

### 1. Access Swagger Documentation
```
http://localhost:8000/docs
```

### 2. Get Your Token
Login to the application and copy your JWT token from the browser's local storage or network tab.

### 3. Test the API

#### Using cURL:
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

#### Using Python:
```python
import requests

url = "http://localhost:8000/api/analytics/customer-insights/view-insights/chat"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "message": "What is the total sales?",
    "context": {},
    "conversation_history": []
}
response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

## 📋 All Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/analytics/customer-insights/filters` | Get filter options | ✅ Yes |
| GET | `/api/analytics/customer-insights` | Get customer insights data | ✅ Yes |
| POST | `/api/analytics/customer-insights/chat` | Main chatbot | ✅ Yes |
| POST | `/api/analytics/customer-insights/view-insights/chat` | View insights chatbot | ✅ Yes |
| GET | `/api/analytics/customer-insights/chat/health` | Health check | ❌ No |
| GET | `/api/analytics/customer-insights/chat/test` | Test endpoint | ✅ Yes |

---

## 💬 Common Questions & Examples

### Question Types Supported:

1. **Sales Questions**
   - "What is the total gross sales?"
   - "What are the sales for January 2025?"
   - "Show me sales by month"

2. **Channel Questions**
   - "What are the top performing channels?"
   - "Which channel has the highest conversion rate?"
   - "Compare Google vs Facebook performance"

3. **Customer Questions**
   - "How many new customers do we have?"
   - "What is the customer lifetime value?"
   - "Show me new vs returning customers"

4. **Geographic Questions**
   - "Which countries have the highest sales?"
   - "What are the sales by region?"
   - "Show me geographic distribution"

5. **Trend Questions**
   - "What are the sales trends over time?"
   - "Show me month-over-month growth"
   - "Compare 2024 vs 2025 sales"

---

## 🔧 Request Examples

### Example 1: Simple Question
```json
{
  "message": "What is the total sales?",
  "context": {},
  "conversation_history": []
}
```

### Example 2: With Filters
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

### Example 3: With Chart Context
```json
{
  "message": "Why is Google performing better?",
  "chart_title": "Sales Channel Performance",
  "context": {
    "selectedYears": [2025]
  },
  "conversation_history": []
}
```

### Example 4: Follow-up Question
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

---

## 📊 Response Structure

```json
{
  "response": "AI-generated answer...",
  "timestamp": "01:30 PM IST on November 29, 2025",
  "context": "Data context used...",
  "data": {
    "pivot_table": [...],
    "columns": ["Total sales", "Orders"],
    "filters": {...},
    "is_trend_query": false,
    "total_rows": 15972,
    "chart_title": "Sales Channel Performance"
  }
}
```

---

## 🧪 Testing Tools

### 1. Swagger UI
- URL: `http://localhost:8000/docs`
- Interactive API testing
- Try it out directly in the browser

### 2. Postman Collection
- File: `Customer_Deep_Intelligence_API.postman_collection.json`
- Import into Postman
- Pre-configured requests

### 3. Python Test Script
- File: `test_customer_insights_api.py`
- Run: `python test_customer_insights_api.py`
- Automated testing

---

## ⚠️ Common Issues

### Issue: 401 Unauthorized
**Solution:** Make sure you're including the Bearer token in the Authorization header

### Issue: 404 File Not Found
**Solution:** Ensure `shopify_data.csv` exists in the backend folder

### Issue: 500 Internal Server Error
**Solution:** Check server logs for detailed error messages

### Issue: Serialization Error
**Solution:** Already fixed - numpy types are automatically converted

---

## 📝 Notes

- All monetary values are in Euros (€)
- Dates are in IST timezone
- Filters are case-sensitive for month names
- Conversation history helps with follow-up questions
- Chart title provides additional context for chart-specific questions

---

## 🔗 Related Files

- **API Documentation:** `CUSTOMER_INSIGHTS_API_DOCS.md`
- **Test Script:** `test_customer_insights_api.py`
- **Postman Collection:** `Customer_Deep_Intelligence_API.postman_collection.json`
- **FastAPI Module:** `customer_insights_fastapi.py`
- **Server Integration:** `server.py`

---

## 📞 Support

For issues:
1. Check server logs
2. Verify CSV file exists
3. Check API key configuration
4. Review error messages in response

