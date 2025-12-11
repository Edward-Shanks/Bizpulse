# Backend Refactoring - Migration Instructions

## Current Status

✅ **Phase 1 Complete**: Core infrastructure created
- Directory structure created
- Configuration module (`app/core/config.py`)
- Database connection (`app/core/database.py`)
- Dependencies (`app/core/dependencies.py`)
- Utility helpers (`app/utils/helpers.py`)
- Basic models extracted (`app/models/`)

## What's Been Created

### Core Infrastructure
- `app/core/config.py` - Centralized configuration
- `app/core/database.py` - MongoDB connection management
- `app/core/dependencies.py` - Authentication dependency
- `app/utils/helpers.py` - Common utility functions

### Models (Partial)
- `app/models/user.py` - User-related models
- `app/models/analytics.py` - Analytics models
- `app/models/insights.py` - Insights chatbot models
- `app/models/customer_insights.py` - Customer Deep Intelligence models

### Application Structure
- `app/main.py` - FastAPI app entry point (skeleton)
- `app/api/v1/api.py` - Router aggregation (skeleton)

## Next Steps to Complete Migration

### Phase 2: Extract Remaining Models
Extract all remaining Pydantic models from `server.py`:
- Kanban/Goals models
- Root Cause Analysis models
- Action Items models
- Any other response/request models

### Phase 3: Create Repositories
Create repository classes for database operations:
- `app/repositories/user_repository.py`
- `app/repositories/business_data_repository.py`
- `app/repositories/shopify_data_repository.py`

### Phase 4: Create Services
Extract business logic to services:
- `app/services/auth_service.py` - Authentication & JWT
- `app/services/analytics_service.py` - Analytics calculations
- `app/services/insights_service.py` - View insights chatbot
- `app/services/customer_insights_service.py` - Customer Deep Intelligence
- `app/services/filter_service.py` - Dynamic filters
- `app/services/data_service.py` - Data sync

### Phase 5: Create Routes
Split routes into separate files:
- `app/api/v1/routes/auth.py`
- `app/api/v1/routes/users.py`
- `app/api/v1/routes/analytics.py`
- `app/api/v1/routes/filters.py`
- `app/api/v1/routes/insights.py`
- `app/api/v1/routes/customer_insights.py`
- `app/api/v1/routes/data.py`
- `app/api/v1/routes/kanban.py`
- `app/api/v1/routes/root_cause.py`

### Phase 6: Testing
1. Update imports in `app/main.py`
2. Test all endpoints
3. Ensure backward compatibility
4. Update deployment scripts

## How to Use New Structure

### Running the New Structure (Once Complete)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Legacy Server (Current)
```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## Important Notes

1. **server.py is still functional** - The old file continues to work
2. **Gradual migration** - We can migrate endpoints one by one
3. **No breaking changes** - Existing functionality remains intact
4. **Testing required** - Each migrated endpoint should be tested

## File Size Comparison

- **Before**: `server.py` ~7000 lines
- **After**: Distributed across ~30+ focused files (avg ~200-300 lines each)

## Benefits Achieved

1. ✅ Clear separation of concerns
2. ✅ Easy to locate code
3. ✅ Better testability
4. ✅ Scalable architecture
5. ✅ Industry-standard structure



