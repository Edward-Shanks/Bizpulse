# Backend Refactoring Plan - FastAPI Industry Standard Architecture

## Current State
- **server.py**: ~7000 lines of monolithic code
- All routes, models, business logic, and database operations in one file
- No separation of concerns
- Difficult to maintain and test

## Target Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── core/                      # Core application setup
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration & settings
│   │   ├── database.py            # Database connection
│   │   └── dependencies.py        # Shared dependencies (auth, etc.)
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router aggregation
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── auth.py        # Authentication routes
│   │           ├── users.py       # User management routes
│   │           ├── analytics.py  # Analytics endpoints
│   │           ├── filters.py    # Filter options endpoints
│   │           ├── insights.py   # View insights chatbot
│   │           ├── customer_insights.py  # Customer Deep Intelligence
│   │           ├── data.py        # Data sync endpoints
│   │           ├── kanban.py      # Kanban/Goals endpoints
│   │           └── root_cause.py  # Root cause analysis
│   │
│   ├── models/                    # Pydantic models (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── analytics.py
│   │   ├── insights.py
│   │   ├── customer_insights.py
│   │   └── common.py
│   │
│   ├── schemas/                   # Database schemas (if needed)
│   │   └── __init__.py
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── analytics_service.py
│   │   ├── insights_service.py
│   │   ├── customer_insights_service.py
│   │   ├── filter_service.py
│   │   ├── data_service.py
│   │   └── llm_service.py
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── business_data_repository.py
│   │   └── shopify_data_repository.py
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── helpers.py            # safe_float, format_currency, etc.
│       ├── azure_storage.py      # Azure Blob Storage utilities
│       ├── query_builder.py      # MongoDB query building
│       └── llm_helpers.py        # LLM-related utilities
│
├── server.py                      # Legacy file (will be deprecated)
└── requirements.txt
```

## Migration Strategy

### Phase 1: Core Infrastructure ✅
- [x] Create directory structure
- [x] Create config.py (settings management)
- [x] Create database.py (MongoDB connection)
- [x] Create dependencies.py (auth dependency)
- [x] Create utils/helpers.py (common utilities)

### Phase 2: Models & Schemas
- [ ] Extract all Pydantic models to app/models/
- [ ] Organize by domain (user, analytics, insights, etc.)

### Phase 3: Repositories
- [ ] Create repository layer for database operations
- [ ] Move all MongoDB queries to repositories

### Phase 4: Services
- [ ] Extract business logic to services
- [ ] Services call repositories, not database directly

### Phase 5: Routes
- [ ] Split routes into separate files by domain
- [ ] Routes call services, not repositories directly

### Phase 6: Main Application
- [ ] Create app/main.py as entry point
- [ ] Update imports and dependencies
- [ ] Test all endpoints

### Phase 7: Cleanup
- [ ] Deprecate server.py
- [ ] Update documentation
- [ ] Update deployment scripts

## Benefits

1. **Maintainability**: Code organized by responsibility
2. **Testability**: Easy to unit test services and repositories
3. **Scalability**: Easy to add new features
4. **Team Collaboration**: Multiple developers can work on different modules
5. **Code Reusability**: Services and repositories can be reused
6. **Industry Standard**: Follows FastAPI best practices

## Key Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Dependency Injection**: Use FastAPI's Depends() for dependencies
3. **Repository Pattern**: Abstract database operations
4. **Service Layer**: Business logic separated from routes
5. **Single Responsibility**: Each file/class has one job



