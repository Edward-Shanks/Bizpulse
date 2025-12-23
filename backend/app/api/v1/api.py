"""
API v1 Router Aggregation
Combines all route modules into a single router
"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import and include route modules (import only what exists to avoid errors during migration)
try:
    from app.api.v1.routes import auth
    api_router.include_router(auth.router, tags=["Authentication"])
except ImportError:
    pass

try:
    from app.api.v1.routes import users
    api_router.include_router(users.router, tags=["Users"])
except ImportError:
    pass

try:
    from app.api.v1.routes import data
    api_router.include_router(data.router, tags=["Data"])
except ImportError:
    pass

try:
    from app.api.v1.routes import analytics
    api_router.include_router(analytics.router, tags=["Analytics"])
except ImportError:
    pass

try:
    from app.api.v1.routes import filters
    api_router.include_router(filters.router, tags=["Filters"])
except ImportError:
    pass

try:
    from app.api.v1.routes import action_items
    api_router.include_router(action_items.router, tags=["Action Items"])
except ImportError:
    pass

try:
    from app.api.v1.routes import root_cause
    api_router.include_router(root_cause.router, tags=["Root Cause Analysis"])
except ImportError:
    pass

try:
    from app.api.v1.routes import kanban
    api_router.include_router(kanban.router, tags=["Kanban"])
except ImportError:
    pass

try:
    from app.api.v1.routes import customer_insights
    api_router.include_router(customer_insights.router, tags=["Customer Insights"])
except ImportError:
    pass

try:
    from app.api.v1.routes import insights
    api_router.include_router(insights.router, tags=["Insights"])
except ImportError:
    pass

# Debug endpoints (for checking system status)
try:
    from app.api import debug
    api_router.include_router(debug.router, tags=["Debug"])
except ImportError:
    pass

