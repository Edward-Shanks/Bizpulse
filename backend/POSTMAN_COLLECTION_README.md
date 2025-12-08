# BizPulse API Postman Collection

## Overview

This Postman collection contains all API endpoints for the BizPulse backend application. It's organized into logical folders and includes authentication, example requests, and documentation.

## File Location

**Collection File:** `backend/BizPulse_API_Collection.postman_collection.json`

## How to Import

1. **Open Postman**
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose `BizPulse_API_Collection.postman_collection.json`
5. Click **Import**

## Collection Structure

### 📁 Folders:

1. **Authentication**
   - Login (auto-saves token)
   - Signup

2. **Users**
   - Get All Users
   - Get Users by Department
   - Get Current User

3. **Data Management**
   - Sync Data from Azure
   - Get Data Source

4. **Analytics**
   - Executive Overview (Dashboard)
   - Customer Analysis
   - Brand Analysis
   - Category Analysis
   - Strategic Recommendations

5. **Filters**
   - Get Filter Options (Dynamic/Cascading)
   - Get Filter Options (Test)

6. **AI Chat**
   - AI Chat (Business Insights)
   - Customer Insights Chat
   - Customer Insights Chat (Test)
   - Insights Chat (View Insights)

7. **Customer Deep Intelligence**
   - Get Customer Insights
   - Get Customer Insights Filters

8. **Kanban & Goals**
   - Get Annual Goal
   - Get Recommendations
   - Generate Goals
   - Create/Update/Get Goals
   - Campaign Management

9. **Cockpit**
   - Get Action Items
   - Seed Action Items

10. **Root Cause Analysis**
    - Get Root Cause Issues
    - Generate Root Cause Issues
    - Test Root Cause Analysis

## Setup Instructions

### 1. Configure Base URL

The collection uses a variable `{{base_url}}` which defaults to:
```
http://localhost:8000/api
```

**To change it:**
1. Click on collection name
2. Go to **Variables** tab
3. Update `base_url` value
4. Click **Save**

**Common URLs:**
- Local: `http://localhost:8000/api`
- Development: `http://dev-server:8000/api`
- Production: `https://api.yourdomain.com/api`

### 2. Authentication Setup

**Automatic Token Management:**
- The **Login** endpoint automatically saves the token to `{{auth_token}}`
- All other endpoints use Bearer token authentication
- Token is stored in collection variable

**Manual Token Setup (if needed):**
1. Login first using the Login endpoint
2. Copy the token from response
3. Go to collection **Variables**
4. Paste token into `auth_token` variable

### 3. Default Credentials

**Default Admin User:**
- Email: `admin@thrivebrands.ai`
- Password: `Thrive@123`

## Usage Examples

### Example 1: Get Dashboard Data

1. **Login First:**
   - Go to **Authentication** → **Login**
   - Click **Send**
   - Token is automatically saved

2. **Get Dashboard Data:**
   - Go to **Analytics** → **Executive Overview (Dashboard)**
   - Modify query parameters if needed:
     - `years`: `2024` or `2023,2024`
     - `months`: `January` or `January,February`
   - Click **Send**

### Example 2: Use AI Chat

1. **Ensure you're logged in** (token is set)

2. **Send AI Chat Request:**
   - Go to **AI Chat** → **AI Chat (Business Insights)**
   - Modify the message in request body:
     ```json
     {
         "message": "What is the total revenue for 2024?"
     }
     ```
   - Click **Send**

### Example 3: Get Filtered Data

1. **Get Filter Options:**
   - Go to **Filters** → **Get Filter Options**
   - Add query parameters to filter options:
     - `years=2024` - Shows only options for 2024
     - `businesses=Brillo` - Shows only options for Brillo
   - Click **Send**

2. **Use Filters in Analytics:**
   - Go to **Analytics** → **Customer Analysis**
   - Add the same filters as query parameters
   - Click **Send**

## Query Parameters Guide

### Common Parameters:

**Years:**
- Single: `years=2024`
- Multiple: `years=2023,2024`

**Months:**
- Single: `months=January`
- Multiple: `months=January,February,March`

**Businesses:**
- Single: `businesses=Brillo`
- Multiple: `businesses=Brillo,Brillo & KMPL`
- **Note:** For businesses with commas, use the exact name as stored

**Brands:**
- Single: `brands=Brand1`
- Multiple: `brands=Brand1,Brand2`

**Channels:**
- Single: `channels=Online`
- Multiple: `channels=Online,Retail`

**Categories:**
- Single: `categories=Category1`
- Multiple: `categories=Category1,Category2`

## Request Body Examples

### Login Request:
```json
{
    "email": "admin@thrivebrands.ai",
    "password": "Thrive@123"
}
```

### AI Chat Request:
```json
{
    "message": "What is the total revenue for 2024?",
    "session_id": "session_123"
}
```

### Customer Insights Chat Request:
```json
{
    "message": "What is the total sales?",
    "chart_title": "Sales Channel Performance",
    "context": {
        "selectedYears": [2025],
        "selectedMonths": ["January"]
    },
    "session_id": "session_123",
    "conversation_history": []
}
```

### Create Goal Request:
```json
{
    "title": "Increase Q1 Sales",
    "description": "Increase sales by 20% in Q1",
    "department": "sales",
    "targetValue": 1000000,
    "currentValue": 800000,
    "deadline": "2024-03-31",
    "status": "in-progress"
}
```

## Environment Variables

The collection uses these variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000/api` | Base URL for all API requests |
| `auth_token` | (empty) | JWT token (auto-filled after login) |

## Authentication

**All endpoints (except Login) require authentication:**

- **Type:** Bearer Token
- **Header:** `Authorization: Bearer {{auth_token}}`
- **Auto-setup:** Login endpoint automatically saves token

## Error Handling

### Common Errors:

**401 Unauthorized:**
- Token expired or invalid
- Solution: Login again

**404 Not Found:**
- Endpoint doesn't exist
- Check URL path

**500 Internal Server Error:**
- Server error
- Check server logs

**400 Bad Request:**
- Invalid request parameters
- Check request body/query parameters

## Tips & Best Practices

1. **Always Login First:**
   - Run Login endpoint before testing other endpoints
   - Token is automatically saved

2. **Use Query Parameters:**
   - Most analytics endpoints support filtering
   - Use comma-separated values for multiple selections

3. **Test with Different Filters:**
   - Try different combinations of years, months, businesses, etc.
   - Test edge cases (empty filters, invalid values)

4. **Save Responses:**
   - Use Postman's "Save Response" feature
   - Compare responses for different filter combinations

5. **Use Environments:**
   - Create Postman environments for different servers (dev, staging, prod)
   - Switch between environments easily

## Collection Statistics

- **Total Endpoints:** 40+
- **Folders:** 10
- **Authentication:** Bearer Token (JWT)
- **Base URL:** Configurable via variable

## Support

For issues or questions:
1. Check server logs
2. Verify authentication token
3. Check endpoint documentation in code
4. Verify query parameters format

## Updates

To update the collection:
1. Export current collection from Postman
2. Compare with new endpoints
3. Add missing endpoints
4. Update examples if needed

---

**Last Updated:** December 2024
**Version:** 1.0

