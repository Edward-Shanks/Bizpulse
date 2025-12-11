# FastAPI Backend Architecture Guide

## Overview
This document describes the new industry-standard FastAPI architecture for the BizPulse backend project.

## Directory Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   │
│   ├── core/                     # Core application setup
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration & environment variables
│   │   ├── database.py          # MongoDB connection management
│   │   └── dependencies.py      # Shared dependencies (auth, etc.)
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   └── v1/                   # API version 1
│   │       ├── __init__.py
│   │       ├── api.py            # Router aggregation (includes all routes)
│   │       └── routes/           # Individual route modules
│   │           ├── __init__.py
│   │           ├── auth.py       # POST /auth/login, POST /auth/signup
│   │           ├── users.py      # GET /users, GET /users/me, etc.
│   │           ├── analytics.py  # GET /analytics/* endpoints
│   │           ├── filters.py    # GET /filters/options
│   │           ├── insights.py   # POST /insights/chat
│   │           ├── customer_insights.py  # POST /analytics/customer-insights/chat
│   │           ├── data.py       # GET /data/sync, GET /data/source
│   │           ├── kanban.py     # GET /kanban/*, POST /kanban/*
│   │           └── root_cause.py # GET /root-cause-analysis/*
│   │
│   ├── models/                   # Pydantic models (request/response schemas)
│   │   ├── __init__.py
│   │   ├── user.py              # User, LoginRequest, LoginResponse, etc.
│   │   ├── analytics.py         # BusinessDataRecord, SyncStatusResponse
│   │   ├── insights.py          # InsightsChatRequest, InsightsChatResponse
│   │   ├── customer_insights.py # CustomerInsightsChatRequest/Response
│   │   └── kanban.py            # Goal, Campaign, StrategicRecommendation models
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication & JWT token generation
│   │   ├── analytics_service.py # Analytics calculations & aggregations
│   │   ├── insights_service.py  # View insights chatbot logic
│   │   ├── customer_insights_service.py  # Customer Deep Intelligence logic
│   │   ├── filter_service.py    # Dynamic filter options logic
│   │   ├── data_service.py      # Data sync from Azure
│   │   └── llm_service.py       # LLM API calls (Perplexity, OpenAI)
│   │
│   ├── repositories/             # Data access layer (database operations)
│   │   ├── __init__.py
│   │   ├── user_repository.py   # User CRUD operations
│   │   ├── business_data_repository.py  # Business data queries
│   │   └── shopify_data_repository.py   # Shopify data queries
│   │
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── helpers.py           # safe_float, format_currency, parse_list
│       ├── azure_storage.py     # Azure Blob Storage operations
│       ├── query_builder.py    # MongoDB query building helpers
│       └── llm_helpers.py      # LLM-related utilities
│
├── server.py                     # Legacy file (deprecated, kept for reference)
└── requirements.txt
```

## Architecture Layers

### 1. Routes Layer (`app/api/v1/routes/`)
- **Responsibility**: Handle HTTP requests/responses
- **What it does**: 
  - Receives requests
  - Validates input using Pydantic models
  - Calls services
  - Returns responses
- **Example**:
  ```python
  @router.get("/analytics/executive-overview")
  async def get_executive_overview(
      years: str = None,
      email: str = Depends(get_current_user)
  ):
      return await analytics_service.get_executive_overview(years)
  ```

### 2. Services Layer (`app/services/`)
- **Responsibility**: Business logic
- **What it does**:
  - Implements business rules
  - Orchestrates multiple repository calls
  - Transforms data
  - Calls external APIs (LLM)
- **Example**:
  ```python
  async def get_executive_overview(years: str):
      query = build_query_from_filters(years)
      data = await business_data_repo.get_executive_data(query)
      return calculate_metrics(data)
  ```

### 3. Repositories Layer (`app/repositories/`)
- **Responsibility**: Database operations
- **What it does**:
  - Executes MongoDB queries
  - Handles data transformation
  - Abstracts database details
- **Example**:
  ```python
  async def get_executive_data(query: dict):
      pipeline = [
          {"$match": query},
          {"$group": {"_id": "$Year", "Revenue": {"$sum": "$Revenue"}}}
      ]
      return await db.business_data.aggregate(pipeline).to_list(100)
  ```

### 4. Models Layer (`app/models/`)
- **Responsibility**: Data validation
- **What it does**:
  - Defines request/response schemas
  - Validates input/output
  - Type safety

### 5. Utils Layer (`app/utils/`)
- **Responsibility**: Reusable helper functions
- **What it does**:
  - Common utilities (formatting, parsing)
  - External service helpers (Azure, LLM)

## Migration Strategy

### Step-by-Step Approach

1. **Keep server.py running** - Don't break existing functionality
2. **Create new structure** - Set up directories and core files
3. **Migrate incrementally** - Move one endpoint at a time
4. **Test each migration** - Ensure endpoints still work
5. **Update imports** - Gradually switch from server.py to new structure
6. **Deprecate server.py** - Once all endpoints are migrated

## Benefits

1. **Maintainability**: Easy to find and modify code
2. **Testability**: Each layer can be tested independently
3. **Scalability**: Easy to add new features
4. **Team Collaboration**: Multiple developers can work simultaneously
5. **Code Reusability**: Services and repositories can be reused
6. **Industry Standard**: Follows FastAPI best practices

## Next Steps

1. Complete model extraction
2. Create repository layer
3. Create service layer
4. Create route modules
5. Create main.py entry point
6. Test all endpoints
7. Update deployment scripts



