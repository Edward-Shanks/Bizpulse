"""
FastAPI Application Entry Point
Main application file that creates and configures the FastAPI app
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Application startup...")
    
    # Connect to MongoDB
    from app.core.database import database
    await connect_to_mongo()
    
    # Create default admin user if not exists
    from app.services.auth_service import create_default_admin_user
    await create_default_admin_user(database.db)
    
    # Verify data exists, sync from Azure if needed
    from app.services.data_service import verify_and_sync_data
    await verify_and_sync_data(database.db)
    
    # Log registered routes
    try:
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                method = list(route.methods)[0] if route.methods else 'GET'
                routes.append(f"{method} {route.path}")
        logger.info(f"Registered {len(routes)} routes")
    except Exception as e:
        logger.warning(f"Could not log routes: {str(e)}")
    
    yield
    
    # Shutdown
    await close_mongo_connection()
    logger.info("Application shutdown")

# Create FastAPI app
app = FastAPI(
    title="BizPulse API",
    description="Business Analytics and Insights API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
if settings.CORS_ORIGINS == ['*']:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BizPulse API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

