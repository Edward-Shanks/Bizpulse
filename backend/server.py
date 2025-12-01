from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pandas as pd
from io import StringIO
from azure.storage.blob import BlobServiceClient
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
# from emergentintegrations.llm.chat import LlmChat, UserMessage  # Package not available
import openai
import bcrypt
import jwt
import requests
import json
import asyncio

ROOT_DIR = Path(__file__).parent

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load nearest .env (backend/.env preferred). This works even if cwd differs.
_dotenv_path = find_dotenv(str(ROOT_DIR / '.env')) or find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)
    logger.info(f"Loaded environment from: {_dotenv_path}")
else:
    logger.warning("No .env file found. Relying on process env vars.")

# MongoDB connection
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')
if not mongo_url or not db_name:
    raise RuntimeError(
        "Missing required environment variables. Make sure backend/.env exists and has MONGO_URL and DB_NAME."
    )
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Azure Blob Storage setup
AZURE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_CONTAINER_NAME = os.getenv('AZURE_CONTAINER_NAME')
AZURE_BLOB_PATH = os.getenv('AZURE_BLOB_PATH')

# JWT Secret
JWT_SECRET = os.getenv('JWT_SECRET', 'thrive-brands-biz-pulse-secret-2024')
JWT_ALGORITHM = "HS256"

security = HTTPBearer()

# Scheduler for periodic sync
scheduler = BackgroundScheduler()

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    name: Optional[str] = None
    department: Optional[str] = None  # sales, operations, finance, hr, marketing, technology
    role: Optional[str] = None  # VP, Director, Manager, Team Member
    status: str = "active"  # active, inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    email: str

class BusinessDataRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    Year: int
    Month_Name: str
    Brand_Type_Name: Optional[str] = None
    PL_Brand: Optional[str] = None
    PL_Category: Optional[str] = None
    SubCat_Name: Optional[str] = None
    Attribute_Name: Optional[str] = None
    SKU_Channel_Name: Optional[str] = None
    PL_Cust_Grp: Optional[str] = None
    Units: Optional[float] = 0
    Revenue: Optional[float] = 0
    Price_Downs: Optional[float] = 0
    Perm_Disc: Optional[float] = 0
    Group_Cost: Optional[float] = 0
    LTA: Optional[float] = 0
    Gross_Profit: Optional[float] = 0
    Business: Optional[str] = None
    Channel: Optional[str] = None
    Customer: Optional[str] = None
    Brand: Optional[str] = None
    Category: Optional[str] = None
    Sub_Cat: Optional[str] = None
    Board_Category: Optional[str] = None

class AIConversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_message: str
    ai_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"

class AIChatResponse(BaseModel):
    response: str
    session_id: str

class CustomerInsightsChatRequest(BaseModel):
    """Request model for Customer Deep Intelligence chatbot"""
    message: str = Field(..., description="User's question or message", example="What is the total gross sales?")
    chart_title: Optional[str] = Field(None, description="Title of the chart being viewed", example="Sales Channel Performance")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Filter context including selectedYears, selectedMonths, selectedChannels, etc.",
        example={"selectedYears": [2025], "selectedMonths": ["January"]}
    )
    session_id: Optional[str] = Field(None, description="Session identifier for tracking conversations", example="session_123")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous conversation messages for context",
        example=[{"role": "user", "content": "What is the total sales?"}, {"role": "assistant", "content": "The total sales is..."}]
    )

class CustomerInsightsChatResponse(BaseModel):
    """Response model for Customer Deep Intelligence chatbot"""
    response: str = Field(..., description="AI-generated response to the user's question", example="Based on the Shopify customer data, the total gross sales is €299,132,414.31...")
    timestamp: Optional[str] = Field(None, description="Response timestamp", example="01:30 PM IST on November 29, 2025")
    context: Optional[str] = Field(None, description="Data context used for generating the response", example="Shopify Customer Data Analysis...")
    data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional data including pivot_table, filters, columns, etc.",
        example={
            "pivot_table": [{"Total sales": 299132414.31, "Orders": 15000}],
            "columns": ["Total sales"],
            "filters": {},
            "is_trend_query": False,
            "total_rows": 15972
        }
    )

class SyncStatusResponse(BaseModel):
    status: str
    message: str
    records_count: int

# Helper Functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def load_data_from_azure_blob() -> int:
    if not (AZURE_CONNECTION_STRING and AZURE_CONTAINER_NAME and AZURE_BLOB_PATH):
        logger.warning("Azure Blob config not set. Skipping Azure sync.")
        return 0
    try:
        logger.info(f"Downloading CSV from Azure: container={AZURE_CONTAINER_NAME}, path={AZURE_BLOB_PATH}")
        blob_service = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service.get_container_client(AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(AZURE_BLOB_PATH)
        stream = blob_client.download_blob()
        csv_bytes = stream.readall()
        csv_text = csv_bytes.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(csv_text))

        # Normalize column names to expected schema
        rename_map = {
            'Month': 'Month_Name',
            'MonthName': 'Month_Name',
            'month_name': 'Month_Name',
            'Sub_Category': 'Sub_Cat',
            'SubCat': 'Sub_Cat',
            'sub_cat': 'Sub_Cat',
            'Brand_Type': 'Brand_Type_Name',
            'PL Brand': 'PL_Brand',
            'PL Category': 'PL_Category',
            'SKU Channel Name': 'SKU_Channel_Name',
            'PL Cust Grp': 'PL_Cust_Grp',
            'gSales': 'Revenue',
            'fGP': 'Gross_Profit',  # Fixed: was 'GrossProfit'
            'Cases': 'Units',       # Fixed: added Cases -> Units mapping
        }
        df = df.rename(columns=rename_map)

        # Ensure required columns exist
        required = ['Year', 'Month_Name']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Required column missing in CSV: {col}")

        # Coerce numeric columns used downstream
        for col in ['Gross_Profit', 'Revenue', 'Units', 'Year']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Convert to list of dicts and insert
        records = df.to_dict(orient='records')
        if not records:
            logger.warning("Azure CSV contained no records.")
            return 0

        # Clean collection then insert
        await db.business_data.delete_many({})
        # Insert in batches to avoid large payloads
        batch_size = 5000
        total = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await db.business_data.insert_many(batch)
            total += len(batch)

        logger.info(f"Loaded {total} records from Azure CSV into MongoDB")
        return total
    except Exception as e:
        logger.error(f"Azure sync failed: {e}")
        return 0

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize default user only
    logger.info("Application startup...")
    
    # Log all registered routes for debugging
    try:
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                method = list(route.methods)[0] if route.methods else 'GET'
                routes.append(f"{method} {route.path}")
        logger.info(f"Registered {len(routes)} routes")
        customer_chat_route = [r for r in routes if 'customer-insights/chat' in r]
        if customer_chat_route:
            logger.info(f"✅ Customer insights chat route found: {customer_chat_route}")
        else:
            logger.warning("⚠️ Customer insights chat route NOT found in registered routes!")
            logger.warning(f"Available routes with 'customer': {[r for r in routes if 'customer' in r.lower()]}")
            logger.warning(f"All POST routes: {[r for r in routes if 'POST' in r]}")
            logger.warning(f"All analytics routes: {[r for r in routes if '/analytics' in r]}")
        # Log root cause analysis routes specifically
        rca_routes = [r for r in routes if 'root-cause-analysis' in r]
        if rca_routes:
            logger.info(f"✅ Root Cause Analysis routes found: {rca_routes}")
        else:
            logger.warning("⚠️ Root Cause Analysis routes NOT found in registered routes!")
            logger.warning(f"Available routes with 'root': {[r for r in routes if 'root' in r.lower()]}")
        # Also check the actual app.routes to see what's registered
        actual_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                actual_routes.append(f"{list(route.methods)} {route.path}")
        rca_actual = [r for r in actual_routes if 'root-cause-analysis' in r]
        logger.info(f"🔍🔍🔍 Actual app.routes with root-cause: {rca_actual}")
    except Exception as e:
        logger.warning(f"Could not log routes: {str(e)}")
        import traceback
        logger.warning(f"Traceback: {traceback.format_exc()}")
    
    # Create default user if not exists
    existing_user = await db.users.find_one({"email": "data.admin@thrivebrands.ai"})
    if not existing_user:
        default_password = os.getenv('DEFAULT_USER_PASSWORD', '123456User')
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(email="data.admin@thrivebrands.ai", password_hash=password_hash)
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        logger.info("Default user created")
    
    # Create admin user if not exists
    existing_admin = await db.users.find_one({"email": "admin@thrivebrands.ai"})
    if not existing_admin:
        admin_password = os.getenv('ADMIN_PASSWORD', 'Thrive@123')
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(email="admin@thrivebrands.ai", password_hash=password_hash)
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        logger.info("Admin user created")
    
    # Verify data exists in MongoDB; if empty try Azure sync
    count = await db.business_data.count_documents({})
    if count == 0:
        logger.info("No data in MongoDB. Attempting Azure CSV load...")
        loaded = await load_data_from_azure_blob()
        count = await db.business_data.count_documents({})
        if loaded > 0:
            logger.info(f"Data loaded from Azure. Records now available: {count}")
        else:
            logger.warning("⚠️ Azure load skipped/failed. You can run /api/data/sync after fixing config or use generate_dummy_data.py")
    else:
        logger.info(f"MongoDB already has data: {count} records")
    
    yield
    
    # Shutdown
    try:
        if scheduler.running:
            scheduler.shutdown()
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {str(e)}")
    try:
        client.close()
    except Exception as e:
        logger.warning(f"Error closing MongoDB client: {str(e)}")
    logger.info("Application shutdown")

# Create the main app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware BEFORE router (so error responses have CORS headers)
# Allow all origins for development, restrict in production
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
if cors_origins == ['*']:
    # Allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    # Specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# Add request logging middleware to debug routing issues
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Log ALL requests to customer-insights and root-cause-analysis endpoints
        if '/api/analytics/customer-insights' in path or '/api/auth' in path or '/api/root-cause-analysis' in path:
            logger.info(f"🔵🔵🔵 MIDDLEWARE: INCOMING REQUEST: {request.method} {path}")
            logger.info(f"🔵🔵🔵 MIDDLEWARE: Full URL: {request.url}")
            logger.info(f"🔵🔵🔵 MIDDLEWARE: Authorization header: {'present' if 'authorization' in request.headers else 'MISSING'}")
            if 'authorization' in request.headers:
                auth_header = request.headers.get('authorization', '')
                logger.info(f"🔵🔵🔵 MIDDLEWARE: Auth header value: {auth_header[:50]}...")
        try:
            response = await call_next(request)
            if '/api/analytics/customer-insights' in path or '/api/auth' in path or '/api/root-cause-analysis' in path:
                logger.info(f"🔵🔵🔵 MIDDLEWARE: RESPONSE: {response.status_code} for {request.method} {path}")
            return response
        except Exception as e:
            logger.error(f"🔵🔵🔵 MIDDLEWARE: ERROR: {str(e)}")
            import traceback
            logger.error(f"🔵🔵🔵 MIDDLEWARE: Traceback: {traceback.format_exc()}")
            raise

app.add_middleware(RequestLoggingMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Make email matching case-insensitive
    email_lower = request.email.lower().strip()
    user_doc = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Use the actual email from database for consistency
    actual_email = user_doc.get('email', request.email)
    
    if not bcrypt.checkpw(request.password.encode('utf-8'), user_doc['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = jwt.encode(
        {"email": actual_email, "exp": datetime.now(timezone.utc).timestamp() + 86400},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return LoginResponse(token=token, email=actual_email)

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    department: str  # sales, operations, finance, hr, marketing, technology
    role: str  # VP, Director, Manager, Team Member

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    status: str

@api_router.post("/auth/signup", response_model=UserResponse)
async def signup(request: SignupRequest, email: str = Depends(get_current_user)):
    """Development-only signup endpoint - requires authentication"""
    # Check if in development mode
    is_dev = os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    if not is_dev:
        raise HTTPException(status_code=403, detail="Signup is only available in development mode")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Validate department
    valid_departments = ['sales', 'operations', 'finance', 'hr', 'marketing', 'technology']
    if request.department.lower() not in valid_departments:
        raise HTTPException(status_code=400, detail=f"Invalid department. Must be one of: {', '.join(valid_departments)}")
    
    # Hash password
    password_hash = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = User(
        email=request.email,
        password_hash=password_hash,
        name=request.name,
        department=request.department.lower(),
        role=request.role,
        status="active"
    )
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        department=user.department,
        role=user.role,
        status=user.status
    )

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(email: str = Depends(get_current_user)):
    """Get all users/team members"""
    users = await db.users.find({"status": "active"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.get("/users/by-department/{department}", response_model=List[UserResponse])
async def get_users_by_department(department: str, email: str = Depends(get_current_user)):
    """Get users by department"""
    users = await db.users.find(
        {"department": department.lower(), "status": "active"},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(email: str = Depends(get_current_user)):
    """Get current logged-in user information"""
    user = await db.users.find_one({"email": email}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

@api_router.get("/data/sync", response_model=SyncStatusResponse)
async def trigger_sync(email: str = Depends(get_current_user)):
    try:
        loaded = await load_data_from_azure_blob()
        count = await db.business_data.count_documents({})
        message = "Loaded from Azure" if loaded > 0 else "Azure load skipped/failed; collection unchanged"
        return SyncStatusResponse(status="success", message=message, records_count=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/data/source")
async def get_data_source(email: str = Depends(get_current_user)):
    """Returns metadata about the current data source and sample records"""
    try:
        count = await db.business_data.count_documents({})
        if count == 0:
            return {
                "source": "none",
                "message": "No data in MongoDB",
                "records_count": 0,
                "sample_records": []
            }
        
        # Get a sample record to show data structure
        sample = await db.business_data.find_one({}, {"_id": 0})
        
        # Convert NaN/Inf values to None for JSON serialization
        if sample:
            import math
            sample = {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v) 
                     for k, v in sample.items()}
        
        # Check if this looks like dummy data or real data
        is_dummy = False
        if sample:
            # Check for dummy data indicators
            if 'dummy' in str(sample).lower() or 'test' in str(sample).lower():
                is_dummy = True
            # Check for realistic data patterns
            if 'Year' in sample and sample.get('Year', 0) > 2020:
                is_dummy = False
        
        return {
            "source": "dummy" if is_dummy else "azure",
            "message": "Using dummy data" if is_dummy else "Using Azure CSV data",
            "records_count": count,
            "sample_records": [sample] if sample else [],
            "columns": list(sample.keys()) if sample else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/executive-overview")
async def get_executive_overview(
    years: str = None,
    months: str = None,
    businesses: str = None,
    channels: str = None,
    email: str = Depends(get_current_user)
):
    """Executive Overview - YoY comparison, KPIs with multi-select filters"""
    logger.info("🔍 GET /api/analytics/executive-overview called")
    try:
        # Build query based on multi-select filters
        query = {}
        
        if years:
            year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
            if year_list:
                query['Year'] = {'$in': year_list}
        
        if months:
            month_list = [m.strip() for m in months.split(',') if m.strip()]
            if month_list:
                query['Month_Name'] = {'$in': month_list}
        
        if businesses:
            business_list = [b.strip() for b in businesses.split(',') if b.strip()]
            if business_list:
                query['Business'] = {'$in': business_list}
        
        if channels:
            channel_list = [c.strip() for c in channels.split(',') if c.strip()]
            if channel_list:
                query['Channel'] = {'$in': channel_list}
            
        # Helper to handle NaN values in float conversions
        import math
        def safe_float(val):
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return 0.0
            return float(val)
        
        logger.info(f"Query being executed: {query}")
        logger.info(f"🚀 Using MongoDB aggregation pipeline for performance")
        
        # Yearly performance aggregation
        pipeline_yearly = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {
                "_id": "$Year",
                "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "Units": {"$sum": {"$toDouble": "$Units"}}
            }}
        ]
        yearly_results = await db.business_data.aggregate(pipeline_yearly).to_list(100)
        logger.info(f"✅ Yearly aggregation: {len(yearly_results)} records")
        
        yearly_list = []
        for item in yearly_results:
            yearly_list.append({
                "Year": int(item['_id']) if item['_id'] else 0,
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Units": safe_float(item.get('Units', 0))
            })
        
        # Business performance aggregation
        pipeline_business = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {
                "_id": "$Business",
                "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "Units": {"$sum": {"$toDouble": "$Units"}}
            }}
        ]
        business_results = await db.business_data.aggregate(pipeline_business).to_list(100)
        logger.info(f"✅ Business aggregation: {len(business_results)} records")
        
        business_list = []
        for item in business_results:
            business_list.append({
                "Business": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Units": safe_float(item.get('Units', 0))
            })
        
        # Get current year for monthly trend
        pipeline_max_year = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {"_id": None, "maxYear": {"$max": {"$toDouble": "$Year"}}}}
        ]
        max_year_result = await db.business_data.aggregate(pipeline_max_year).to_list(1)
        current_year = int(max_year_result[0]['maxYear']) if max_year_result and max_year_result[0].get('maxYear') else 2024
        
        # Monthly trend for current year
        monthly_query = {**query, "Year": current_year}
        pipeline_monthly = [
            {"$match": monthly_query},
            {"$group": {
                "_id": "$Month_Name",
                "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "Units": {"$sum": {"$toDouble": "$Units"}}
            }}
        ]
        monthly_results = await db.business_data.aggregate(pipeline_monthly).to_list(50)
        logger.info(f"✅ Monthly aggregation: {len(monthly_results)} records")
        
        monthly_list = []
        for item in monthly_results:
            monthly_list.append({
                "Month_Name": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Units": safe_float(item.get('Units', 0))
            })
        
        # Channel performance aggregation
        pipeline_channel = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {
                "_id": "$Channel",
                "Revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "Gross_Profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "Units": {"$sum": {"$toDouble": "$Units"}}
            }}
        ]
        channel_results = await db.business_data.aggregate(pipeline_channel).to_list(100)
        logger.info(f"✅ Channel aggregation: {len(channel_results)} records")
        
        channel_list = []
        for item in channel_results:
            channel_list.append({
                "Channel": str(item['_id']) if item['_id'] else "Unknown",
                "Revenue": safe_float(item.get('Revenue', 0)),
                "Gross_Profit": safe_float(item.get('Gross_Profit', 0)),
                "Units": safe_float(item.get('Units', 0))
            })
        
        # Get totals
        pipeline_totals = [
            {"$match": query} if query else {"$match": {}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$toDouble": "$Revenue"}},
                "total_profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
                "total_units": {"$sum": {"$toDouble": "$Units"}}
            }}
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}
        
        logger.info(f"✅ Totals calculated: Revenue={totals.get('total_revenue', 0)}, Profit={totals.get('total_profit', 0)}")
        
        return {
            "yearly_performance": yearly_list,
            "business_performance": business_list,
            "monthly_trend": monthly_list,
            "channel_performance": channel_list,
            "total_profit": safe_float(totals.get('total_profit', 0)),
            "total_revenue": safe_float(totals.get('total_revenue', 0)),
            "total_units": safe_float(totals.get('total_units', 0))
        }
    except Exception as e:
        logger.error(f"Executive overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/customer-analysis")
async def get_customer_analysis(
    years: str = None,
    months: str = None,
    businesses: str = None,
    channels: str = None,
    customers: str = None,
    brands: str = None,
    email: str = Depends(get_current_user),
):
    """Customer Analysis - Channel and customer drilldowns with optional filters"""
    try:
        def parse_list(value: Optional[str], cast=None):
            if not value:
                return []
            items = []
            for part in value.split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    items.append(cast(part) if cast else part)
                except Exception:
                    continue
            return items

        query: Dict[str, Any] = {}

        year_list = parse_list(years, int)
        if year_list:
            query['Year'] = {'$in': year_list}

        month_list = parse_list(months)
        if month_list:
            query['Month_Name'] = {'$in': month_list}

        business_list = parse_list(businesses)
        if business_list:
            query['Business'] = {'$in': business_list}

        channel_list = parse_list(channels)
        if channel_list:
            query['Channel'] = {'$in': channel_list}

        customer_list = parse_list(customers)
        if customer_list:
            query['Customer'] = {'$in': customer_list}

        brand_list = parse_list(brands)
        if brand_list:
            query['Brand'] = {'$in': brand_list}

        def match_stage():
            return {"$match": query} if query else {"$match": {}}

        def safe_float(value: Any) -> float:
            try:
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    if pd.isna(value) or pd.isnull(value):
                        return 0.0
                    return float(value)
                return float(value)
            except Exception:
                return 0.0

        # Channel performance aggregation
        pipeline_channel = [
            match_stage(),
            {
                "$group": {
                    "_id": "$Channel",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        channel_results = await db.business_data.aggregate(pipeline_channel).to_list(200)
        channel_performance = []
        for item in channel_results:
            channel_performance.append({
                "Channel": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })

        # Customer performance aggregation
        pipeline_customer = [
            match_stage(),
            {
                "$group": {
                    "_id": "$Customer",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        customer_results = await db.business_data.aggregate(pipeline_customer).to_list(1000)
        customer_performance = []
        for item in customer_results:
            customer_performance.append({
                "Customer": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })

        top_customers = customer_performance[:50]

        # Channel profit margin
        for item in channel_performance:
            revenue = item.get("Revenue", 0)
            profit = item.get("Gross_Profit", 0)
            margin = (profit / revenue) * 100 if revenue else 0
            item["Profit_Margin"] = margin

        # Totals
        pipeline_totals = [
            match_stage(),
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}

        active_channels = sum(
            1 for item in channel_performance
            if item["Channel"] != "Unknown" and item["Revenue"] > 0
        )

        return {
            "channel_performance": channel_performance,
            "customer_performance": customer_performance,
            "top_customers": top_customers,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_channels": active_channels,
        }
    except Exception as e:
        logger.error(f"Customer analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/brand-analysis")
async def get_brand_analysis(
    years: str = None,
    months: str = None,
    businesses: str = None,
    channels: str = None,
    categories: str = None,
    brands: str = None,
    email: str = Depends(get_current_user),
):
    """Brand Analysis - Brand performance by category and channel with optional filters"""
    try:
        def parse_list(value: Optional[str], cast=None):
            if not value:
                return []
            items = []
            for part in value.split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    items.append(cast(part) if cast else part)
                except Exception:
                    continue
            return items

        query: Dict[str, Any] = {}

        year_list = parse_list(years, int)
        if year_list:
            query['Year'] = {'$in': year_list}

        month_list = parse_list(months)
        if month_list:
            query['Month_Name'] = {'$in': month_list}

        business_list = parse_list(businesses)
        if business_list:
            query['Business'] = {'$in': business_list}

        channel_list = parse_list(channels)
        if channel_list:
            query['Channel'] = {'$in': channel_list}

        category_list = parse_list(categories)
        if category_list:
            query['Category'] = {'$in': category_list}

        brand_list = parse_list(brands)
        if brand_list:
            query['Brand'] = {'$in': brand_list}

        def match_stage():
            return {"$match": query} if query else {"$match": {}}

        def safe_float(value: Any) -> float:
            try:
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    if pd.isna(value) or pd.isnull(value):
                        return 0.0
                    return float(value)
                return float(value)
            except Exception:
                return 0.0

        # Brand performance aggregation
        pipeline_brand = [
            match_stage(),
            {
                "$group": {
                    "_id": "$Brand",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        brand_results = await db.business_data.aggregate(pipeline_brand).to_list(200)
        brand_performance = []
        for item in brand_results:
            brand_performance.append({
                "Brand": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })

        # Brand by business aggregation
        pipeline_brand_business = [
            match_stage(),
            {
                "$group": {
                    "_id": {
                        "Brand": "$Brand",
                        "Business": "$Business",
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        brand_business_results = await db.business_data.aggregate(pipeline_brand_business).to_list(500)
        brand_by_business = []
        for item in brand_business_results:
            key = item.get("_id", {})
            brand_by_business.append({
                "Brand": str(key.get("Brand")) if key.get("Brand") else "Unknown",
                "Business": str(key.get("Business")) if key.get("Business") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
            })

        # Brand Year-over-Year aggregation
        pipeline_brand_yoy = [
            match_stage(),
            {
                "$group": {
                    "_id": {
                        "Brand": "$Brand",
                        "Year": "$Year",
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                }
            },
            {"$sort": {"_id.Brand": 1, "_id.Year": 1}},
        ]
        brand_yoy_results = await db.business_data.aggregate(pipeline_brand_yoy).to_list(1000)
        brand_yoy_growth = []
        for item in brand_yoy_results:
            key = item.get("_id", {})
            brand_yoy_growth.append({
                "Brand": str(key.get("Brand")) if key.get("Brand") else "Unknown",
                "Year": int(key.get("Year")) if key.get("Year") else 0,
                "Revenue": safe_float(item.get("Revenue")),
            })

        # Totals and active brands
        pipeline_totals = [
            match_stage(),
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}

        active_brands = sum(
            1 for item in brand_performance
            if item["Brand"] != "Unknown" and item["Revenue"] > 0
        )

        return {
            "brand_performance": brand_performance,
            "brand_by_business": brand_by_business,
            "brand_yoy_growth": brand_yoy_growth,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_brands": active_brands,
        }
    except Exception as e:
        logger.error(f"Brand analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/category-analysis")
async def get_category_analysis(
    years: str = None,
    months: str = None,
    businesses: str = None,
    channels: str = None,
    categories: str = None,
    sub_categories: str = None,
    email: str = Depends(get_current_user),
):
    """Category Analysis - Category and sub-category deep dives with optional filters"""
    try:
        def parse_list(value: Optional[str], cast=None):
            if not value:
                return []
            items = []
            for part in value.split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    items.append(cast(part) if cast else part)
                except Exception:
                    continue
            return items

        query: Dict[str, Any] = {}

        year_list = parse_list(years, int)
        if year_list:
            query['Year'] = {'$in': year_list}

        month_list = parse_list(months)
        if month_list:
            query['Month_Name'] = {'$in': month_list}

        business_list = parse_list(businesses)
        if business_list:
            query['Business'] = {'$in': business_list}

        channel_list = parse_list(channels)
        if channel_list:
            query['Channel'] = {'$in': channel_list}

        category_list = parse_list(categories)
        if category_list:
            query['Category'] = {'$in': category_list}

        subcategory_list = parse_list(sub_categories)
        if subcategory_list:
            # Handle both Sub_Cat (normalized) and Sub_Category (legacy)
            query['$or'] = [
                {'Sub_Cat': {'$in': subcategory_list}},
                {'Sub_Category': {'$in': subcategory_list}},
            ]

        def match_stage():
            return {"$match": query} if query else {"$match": {}}

        def safe_float(value: Any) -> float:
            try:
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    if pd.isna(value) or pd.isnull(value):
                        return 0.0
                    return float(value)
                return float(value)
            except Exception:
                return 0.0

        # Category performance aggregation
        pipeline_category = [
            match_stage(),
            {
                "$group": {
                    "_id": "$Category",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        category_results = await db.business_data.aggregate(pipeline_category).to_list(200)
        category_performance = []
        for item in category_results:
            category_performance.append({
                "Category": str(item.get("_id")) if item.get("_id") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })

        # Sub-category performance aggregation (use Sub_Cat when available)
        pipeline_subcategory = [
            match_stage(),
            {
                "$group": {
                    "_id": {
                        "Sub_Cat": {"$ifNull": ["$Sub_Cat", "$Sub_Category"]},
                        "Category": "$Category",
                    },
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {"$sort": {"Revenue": -1}},
        ]
        subcategory_results = await db.business_data.aggregate(pipeline_subcategory).to_list(500)
        subcategory_performance = []
        for item in subcategory_results:
            key = item.get("_id", {})
            subcategory_performance.append({
                "Sub_Category": str(key.get("Sub_Cat")) if key.get("Sub_Cat") else "Unknown",
                "Category": str(key.get("Category")) if key.get("Category") else "Unknown",
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
                "Units": safe_float(item.get("Units")),
            })

        # Board category performance when available
        pipeline_board = [
            match_stage(),
            {
                "$group": {
                    "_id": "$Board_Category",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                }
            },
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"Revenue": -1}},
        ]
        board_results = await db.business_data.aggregate(pipeline_board).to_list(200)
        board_category_performance = []
        for item in board_results:
            board_category_performance.append({
                "Board_Category": str(item.get("_id")),
                "Revenue": safe_float(item.get("Revenue")),
                "Gross_Profit": safe_float(item.get("Gross_Profit")),
            })

        # Totals
        pipeline_totals = [
            match_stage(),
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "total_profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "total_units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
        ]
        totals_result = await db.business_data.aggregate(pipeline_totals).to_list(1)
        totals = totals_result[0] if totals_result else {}

        active_categories = sum(
            1 for item in category_performance
            if item["Category"] != "Unknown" and item["Revenue"] > 0
        )

        return {
            "category_performance": category_performance,
            "subcategory_performance": subcategory_performance,
            "board_category_performance": board_category_performance,
            "total_revenue": safe_float(totals.get("total_revenue", 0)),
            "total_profit": safe_float(totals.get("total_profit", 0)),
            "total_units": safe_float(totals.get("total_units", 0)),
            "active_categories": active_categories,
        }
    except Exception as e:
        logger.error(f"Category analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/filters/options")
async def get_filter_options(email: str = Depends(get_current_user)):
    """Get all unique filter options"""
    logger.info("🔍 GET /api/filters/options called")
    try:
        logger.info("📊 Fetching unique values from MongoDB...")
        
        # Use distinct to get unique values - MUCH FASTER than loading all records
        years = await db.business_data.distinct('Year')
        months = await db.business_data.distinct('Month_Name')
        businesses = await db.business_data.distinct('Business')
        channels = await db.business_data.distinct('Channel')
        customers = await db.business_data.distinct('Customer')
        brands = await db.business_data.distinct('Brand')
        categories = await db.business_data.distinct('Category')
        sub_categories = await db.business_data.distinct('Sub_Cat')
        
        logger.info(f"✅ Fetched unique values")
        
        # Filter out None values and convert years to int
        years = sorted([int(y) for y in years if y is not None])
        months = [m for m in months if m is not None]
        businesses = [b for b in businesses if b is not None]
        channels = [c for c in channels if c is not None]
        customers = [c for c in customers if c is not None]
        brands = [b for b in brands if b is not None]
        categories = [c for c in categories if c is not None]
        sub_categories = [s for s in sub_categories if s is not None]
        
        # Sort months chronologically (handle both full names and abbreviations)
        month_order_full = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        month_order_abbr = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        
        def get_month_index(month):
            """Get month index for sorting"""
            if month in month_order_full:
                return month_order_full.index(month)
            elif month in month_order_abbr:
                return month_order_abbr.index(month)
            else:
                return 999
        
        months = sorted(months, key=get_month_index)
        
        result = {
            "years": years,
            "months": months,
            "businesses": businesses,
            "channels": channels,
            "customers": customers,
            "brands": brands,
            "categories": categories,
            "sub_categories": sub_categories
        }
        
        logger.info(f"Filter options generated: {[(k, len(v)) for k, v in result.items()]}")
        return result
    except Exception as e:
        logger.error(f"Error generating filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/filters/options-test")
async def get_filter_options_test():
    """Get all unique filter options - TEST ENDPOINT WITHOUT AUTH"""
    try:
        data = await db.business_data.find({}, {"_id": 0}).to_list(100000)
        logger.info(f"TEST: Retrieved {len(data)} records for filter options")
        
        if not data:
            logger.warning("TEST: No data found for filter options")
            return {}
        
        df = pd.DataFrame(data)
        logger.info(f"TEST: DataFrame shape: {df.shape}")
        logger.info(f"TEST: DataFrame columns: {list(df.columns)}")
        
        if df.empty:
            logger.warning("TEST: DataFrame is empty")
            return {}
        
        result = {
            "years": sorted(df['Year'].dropna().unique().tolist()) if 'Year' in df.columns else [],
            "months": df['Month_Name'].dropna().unique().tolist() if 'Month_Name' in df.columns else [],
            "businesses": df['Business'].dropna().unique().tolist() if 'Business' in df.columns else [],
            "channels": df['Channel'].dropna().unique().tolist() if 'Channel' in df.columns else [],
            "customers": df['Customer'].dropna().unique().tolist() if 'Customer' in df.columns else [],
            "brands": df['Brand'].dropna().unique().tolist() if 'Brand' in df.columns else [],
            "categories": df['Category'].dropna().unique().tolist() if 'Category' in df.columns else [],
            "sub_categories": df['Sub_Cat'].dropna().unique().tolist() if 'Sub_Cat' in df.columns else []
        }
        
        logger.info(f"TEST: Filter options generated: {[(k, len(v)) for k, v in result.items()]}")
        return result
    except Exception as e:
        logger.error(f"TEST: Error generating filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Perplexity API helper function
async def query_perplexity(prompt: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """Query Perplexity API for AI responses"""
    
    PPLX_API_KEY = os.getenv("PPLX_API_KEY1")
    if not PPLX_API_KEY:
        logger.error("PPLX_API_KEY1 environment variable is not set")
        raise ValueError("PPLX_API_KEY1 environment variable is required")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [{
        "role": "system",
        "content": (
            "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
            "Analyze the provided business data and generate strategic marketing and business recommendations. "
            "All monetary values are in Euros (€). Be specific, data-driven, and actionable. "
            "Focus on growth opportunities, customer acquisition, retention strategies, and revenue optimization. "
            "Provide recommendations with clear reasoning, expected impact, and implementation channels."
        )
    }]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": "sonar-pro",
        "messages": messages,
        "max_tokens": 2000
    }
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 1  # Start with 1 second
    
    for attempt in range(max_retries):
        try:
            # Use asyncio.to_thread to run synchronous requests in a thread pool
            def make_request():
                response = requests.post(url, headers=headers, json=payload, timeout=60)  # Increased timeout to 60s
                response.raise_for_status()
                result = response.json()
                if 'choices' not in result or len(result['choices']) == 0:
                    raise ValueError("Invalid response format from Perplexity API")
                return result['choices'][0]['message']['content']
            
            # Run the synchronous request in a thread pool
            result = await asyncio.to_thread(make_request)
            logger.info(f"Perplexity API call successful on attempt {attempt + 1}")
            return result
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Perplexity API timeout on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                logger.error(f"Perplexity API timeout after {max_retries} attempts")
                raise HTTPException(status_code=500, detail="AI service timeout. Please try again.")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Perplexity API request error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                # Check if it's a rate limit or server error (5xx) - retry these
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if status_code >= 500 or status_code == 429:  # Server error or rate limit
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                # For other errors, don't retry
                logger.error(f"Perplexity API non-retryable error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
            else:
                logger.error(f"Perplexity API request failed after {max_retries} attempts: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI service error after retries: {str(e)}")
                
        except (KeyError, ValueError) as e:
            logger.error(f"Perplexity API response parsing error: {str(e)}")
            # Don't retry parsing errors
            raise HTTPException(status_code=500, detail=f"AI service response format error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected Perplexity API error on attempt {attempt + 1}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    
    # Should never reach here, but just in case
    raise HTTPException(status_code=500, detail="AI service error: Max retries exceeded")

@api_router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest, email: str = Depends(get_current_user)):
    """AI Chat Assistant for business insights"""
    try:
        # Get business data context
        data = await db.business_data.find({}, {"_id": 0}).to_list(1000)
        df = pd.DataFrame(data)
        
        # Create data summary for AI context
        context = f"""
You are VectorDeep AI, a business intelligence assistant for ThriveBrands. You have access to business data with the following structure:

Data Overview:
- Total Records: {len(df)} 
- Years: {df['Year'].unique().tolist() if not df.empty else []}
- Businesses: {df['Business'].unique().tolist() if not df.empty else []}
- Brands: {df['Brand'].unique().tolist()[:10] if not df.empty else []} (showing first 10)
- Total Revenue: ${df['Revenue'].sum():,.2f} if not df.empty else 0
- Total Gross Profit: ${df['Gross_Profit'].sum():,.2f} if not df.empty else 0

You can answer questions about:
- Sales performance and trends
- Brand analysis
- Customer and channel performance
- Category insights
- Year-over-year comparisons

Provide insights with specific numbers when possible. Highlight good performance in your response and provide actionable recommendations.
"""
        
        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Send message to OpenAI
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": request.message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            response_text = f"Sorry, I'm having trouble connecting to the AI service. Error: {str(e)}"
        
        # Save conversation
        conversation = AIConversation(
            session_id=request.session_id,
            user_message=request.message,
            ai_response=response_text
        )
        conv_dict = conversation.model_dump()
        conv_dict['timestamp'] = conv_dict['timestamp'].isoformat()
        await db.ai_conversations.insert_one(conv_dict)
        
        return AIChatResponse(response=response_text, session_id=request.session_id)
    except Exception as e:
        logger.error(f"AI Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Strategic Recommendations Model
class StrategicRecommendation(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    type: str = "system"
    category: str
    startDate: str
    endDate: Optional[str] = None
    budget: float
    impact: Dict[str, Any]
    reasoning: str
    channels: List[str]
    aiScore: int
    acceptedAt: Optional[str] = None  # When it was accepted to live
    status: Optional[str] = "recommended"  # recommended, live, past

class StrategicRecommendationsResponse(BaseModel):
    recommended: List[StrategicRecommendation]
    live: List[StrategicRecommendation]
    past: List[StrategicRecommendation] = []

class AcceptCampaignRequest(BaseModel):
    campaignId: int
    fromCollection: str  # "recommended"

# Root Cause Analysis Models
class RootCauseIssue(BaseModel):
    id: int
    title: str
    severity: str  # high, medium, low
    rootCause: str
    impact: str
    recommendation: str
    status: str  # investigating, resolved, monitoring
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class RootCauseAnalysisResponse(BaseModel):
    issues: List[RootCauseIssue]
    summary: Dict[str, int]  # critical, investigating, resolved counts

# Helper function to move expired campaigns from live to past
async def move_expired_campaigns():
    """Move campaigns from live to past if their endDate has passed"""
    try:
        kanban_doc = await db.kanban.find_one({})
        if not kanban_doc:
            return
        
        live_campaigns = kanban_doc.get('live', [])
        past_campaigns = kanban_doc.get('past', [])
        
        current_date = datetime.now(timezone.utc).date()
        expired_campaigns = []
        remaining_live = []
        
        for campaign in live_campaigns:
            if campaign.get('endDate'):
                try:
                    end_date = datetime.fromisoformat(campaign['endDate'].replace('Z', '+00:00')).date()
                    if end_date < current_date:
                        # Campaign has expired, move to past
                        campaign['status'] = 'past'
                        campaign['expiredAt'] = datetime.now(timezone.utc).isoformat()
                        expired_campaigns.append(campaign)
                    else:
                        remaining_live.append(campaign)
                except Exception as e:
                    logger.warning(f"Error parsing endDate for campaign {campaign.get('title')}: {e}")
                    remaining_live.append(campaign)
            else:
                # No end date, keep in live
                remaining_live.append(campaign)
        
        if expired_campaigns:
            # Update MongoDB
            past_campaigns.extend(expired_campaigns)
            await db.kanban.update_one(
                {},
                {"$set": {
                    "live": remaining_live,
                    "past": past_campaigns,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Moved {len(expired_campaigns)} expired campaigns to past")
    except Exception as e:
        logger.error(f"Error moving expired campaigns: {str(e)}")

@api_router.get("/kanban/annual-goal")
async def get_annual_goal(email: str = Depends(get_current_user)):
    """Get real annual goal metrics based on customer activation data"""
    try:
        # Get all business data
        data = await db.business_data.find({}, {"_id": 0}).to_list(10000)
        if not data:
            return {
                "current": 0,
                "target": 100,
                "metric": "% Activated Customers",
                "progress": 0
            }
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return {
                "current": 0,
                "target": 100,
                "metric": "% Activated Customers",
                "progress": 0
            }
        
        # Calculate unique customers
        unique_customers = df['Customer'].nunique() if 'Customer' in df.columns else 0
        
        # Calculate active customers (customers with transactions in current year)
        current_year = datetime.now(timezone.utc).year
        current_year_data = df[df['Year'] == current_year] if 'Year' in df.columns else df
        active_customers = current_year_data['Customer'].nunique() if not current_year_data.empty and 'Customer' in current_year_data.columns else 0
        
        # Calculate activation percentage
        # Activated customers = customers who made purchases in current year
        # Target could be based on historical data or a growth target
        if unique_customers > 0:
            activation_percentage = (active_customers / unique_customers) * 100
        else:
            activation_percentage = 0
        
        # Set target (could be based on historical average or growth target)
        # For now, use a reasonable target based on data
        historical_years = df['Year'].unique() if 'Year' in df.columns else []
        if len(historical_years) > 1:
            # Calculate average activation across years
            yearly_activation = []
            for year in historical_years:
                year_data = df[df['Year'] == year]
                year_customers = year_data['Customer'].nunique() if 'Customer' in year_data.columns else 0
                if unique_customers > 0:
                    yearly_activation.append((year_customers / unique_customers) * 100)
            
            if yearly_activation:
                avg_activation = sum(yearly_activation) / len(yearly_activation)
                target = min(100, max(activation_percentage + 5, avg_activation + 10))  # Target is 10% above average or current + 5%
            else:
                target = min(100, activation_percentage + 10)  # Default: 10% above current
        else:
            target = min(100, activation_percentage + 10)  # Default: 10% above current
        
        return {
            "current": round(activation_percentage, 1),
            "target": round(target, 1),
            "metric": "% Activated Customers",
            "progress": round((activation_percentage / target * 100) if target > 0 else 0, 1),
            "active_customers": active_customers,
            "total_customers": unique_customers
        }
    except Exception as e:
        logger.error(f"Error calculating annual goal: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return default values on error
        return {
            "current": 0,
            "target": 100,
            "metric": "% Activated Customers",
            "progress": 0
        }

@api_router.get("/kanban/recommendations", response_model=StrategicRecommendationsResponse)
async def get_kanban_recommendations(email: str = Depends(get_current_user)):
    """Load kanban recommendations from MongoDB (does not generate new ones)"""
    try:
        # Move expired campaigns first
        await move_expired_campaigns()
        
        # Load from MongoDB
        kanban_doc = await db.kanban.find_one({})
        
        if not kanban_doc:
            # Initialize empty kanban document
            initial_doc = {
                "recommended": [],
                "live": [],
                "past": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.kanban.insert_one(initial_doc)
            return StrategicRecommendationsResponse(
                recommended=[],
                live=[],
                past=[]
            )
        
        # Convert to response model
        recommended = [StrategicRecommendation(**rec) for rec in kanban_doc.get('recommended', [])]
        live = [StrategicRecommendation(**camp) for camp in kanban_doc.get('live', [])]
        past = [StrategicRecommendation(**camp) for camp in kanban_doc.get('past', [])]
        
        return StrategicRecommendationsResponse(
            recommended=recommended,
            live=live,
            past=past
        )
    except Exception as e:
        logger.error(f"Error loading kanban recommendations: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error loading recommendations: {str(e)}")

class GoalRequest(BaseModel):
    campaignId: str
    title: str
    description: str
    department: str
    owners: List[str]  # List of user IDs
    teamMembers: Optional[List[str]] = []
    dependencies: Optional[List[str]] = []
    metrics: Optional[List[str]] = []
    keyResults: Optional[List[Dict]] = []
    status: str = "on-track"
    progress: int = 0

class GenerateGoalsRequest(BaseModel):
    campaignId: str
    autoAssign: bool = False  # If True, AI assigns departments and owners

class GoalResponse(BaseModel):
    id: str
    campaignId: str
    title: str
    description: str
    department: str
    owners: List[str]
    teamMembers: List[str]
    dependencies: List[str]
    metrics: List[str]
    keyResults: List[Dict]
    status: str
    progress: int
    createdAt: str
    tasks: Optional[List[Dict]] = []
    lastUpdated: Optional[str] = None
    lastUpdatedBy: Optional[str] = None

@api_router.post("/kanban/generate-goals", response_model=List[GoalResponse])
async def generate_goals_from_campaign(request: GenerateGoalsRequest, email: str = Depends(get_current_user)):
    """Generate AI-powered goals from a campaign"""
    try:
        import traceback
        logger.info(f"Generating goals for campaign ID: {request.campaignId}")
        
        # Get campaign from MongoDB
        kanban_doc = await db.kanban.find_one({})
        if not kanban_doc:
            logger.error("Kanban data not found in MongoDB")
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        # Find campaign in live or recommended
        campaign = None
        live_campaigns = kanban_doc.get('live', [])
        recommended_campaigns = kanban_doc.get('recommended', [])
        logger.info(f"Searching in {len(live_campaigns)} live and {len(recommended_campaigns)} recommended campaigns")
        
        for camp in live_campaigns + recommended_campaigns:
            camp_id = camp.get('id')
            if camp_id == request.campaignId or str(camp_id) == str(request.campaignId):
                campaign = camp
                logger.info(f"Found campaign: {campaign.get('title', 'Unknown')}")
                break
        
        if not campaign:
            logger.error(f"Campaign with ID {request.campaignId} not found")
            raise HTTPException(status_code=404, detail=f"Campaign not found: {request.campaignId}")
        
        # Get all team members for department assignment
        try:
            all_users = await db.users.find({"status": "active"}, {"_id": 0, "password_hash": 0}).to_list(1000)
            logger.info(f"Found {len(all_users)} active users")
        except Exception as user_error:
            logger.error(f"Error fetching users: {str(user_error)}")
            all_users = []
        
        users_by_dept = {}
        for user in all_users:
            dept = user.get('department')
            if dept:
                if dept not in users_by_dept:
                    users_by_dept[dept] = []
                users_by_dept[dept].append(user)
        
        logger.info(f"Users by department: {list(users_by_dept.keys())}")
        
        # Build AI prompt
        budget = campaign.get('budget', 0)
        if isinstance(budget, dict):
            budget = budget.get('value', 0) if isinstance(budget.get('value'), (int, float)) else 0
        elif not isinstance(budget, (int, float)):
            budget = 0
        
        impact_value = 0
        impact_percentage = 0
        impact = campaign.get('impact', {})
        if isinstance(impact, dict):
            impact_value = impact.get('value', 0) if isinstance(impact.get('value'), (int, float)) else 0
            impact_percentage = impact.get('percentage', 0) if isinstance(impact.get('percentage'), (int, float)) else 0
        
        channels = campaign.get('channels', [])
        if not isinstance(channels, list):
            channels = []
        
        campaign_context = f"""
Campaign Title: {campaign.get('title', 'Unknown')}
Campaign Description: {campaign.get('description', 'No description')}
Category: {campaign.get('category', 'N/A')}
Budget: €{budget:,.2f}
Expected Impact: €{impact_value:,.2f} ({impact_percentage}% uplift)
Channels: {', '.join(str(c) for c in channels)}
Start Date: {campaign.get('startDate', 'N/A')}
End Date: {campaign.get('endDate', 'N/A')}
"""
        
        ai_prompt = f"""
Based on the following campaign, generate 3-6 strategic goals that will help achieve this campaign's objectives.
Each goal should be:
1. Specific and actionable
2. Assigned to appropriate departments (sales, operations, finance, hr, marketing, technology)
3. Have clear owners (can be multiple)
4. Include dependencies
5. Have measurable metrics
6. Include 2-3 key results with current/target values

CAMPAIGN DETAILS:
{campaign_context}

AVAILABLE DEPARTMENTS AND TEAM MEMBERS:
{json.dumps({dept: [{'name': u.get('name'), 'email': u.get('email'), 'role': u.get('role')} for u in users] for dept, users in users_by_dept.items()}, indent=2)}

OUTPUT FORMAT (JSON array ONLY - no markdown, no code blocks, no explanations):
You MUST return ONLY a valid JSON array. Do not include any markdown code blocks, explanations, or text outside the JSON array.
The JSON must be valid with ALL property names enclosed in double quotes. Do NOT use single quotes or unquoted property names.

CRITICAL JSON RULES:
1. All property names MUST be in double quotes: "title" not title or 'title'
2. All string values MUST be in double quotes: "value" not 'value' or value
3. No trailing commas before closing braces or brackets
4. No comments or explanations outside the JSON
5. No markdown code blocks (no ```json or ```)

Example format (copy this structure exactly):
[
  {{
    "title": "Goal title",
    "description": "Detailed goal description",
    "department": "sales",
    "owners": ["user@example.com"],
    "teamMembers": ["member@example.com"],
    "dependencies": ["Dependency 1", "Dependency 2"],
    "metrics": ["Metric 1", "Metric 2"],
    "keyResults": [
      {{"description": "KR 1", "current": 0, "target": 100}},
      {{"description": "KR 2", "current": 0, "target": 50}}
    ],
    "status": "on-track",
    "progress": 0
  }}
]

CRITICAL: Return ONLY the JSON array. No markdown, no code blocks, no explanations. All property names and string values MUST be in double quotes.
Generate 3-6 goals that are realistic, measurable, and aligned with the campaign objectives.
"""
        
        # Call Perplexity AI with retry logic
        logger.info("Calling Perplexity AI to generate goals...")
        ai_response = None
        max_ai_retries = 2
        for ai_attempt in range(max_ai_retries):
            try:
                ai_response = await query_perplexity(ai_prompt)
                if not ai_response or len(ai_response.strip()) == 0:
                    if ai_attempt < max_ai_retries - 1:
                        logger.warning(f"Perplexity API returned empty response, retrying... (attempt {ai_attempt + 1}/{max_ai_retries})")
                        await asyncio.sleep(1)  # Wait 1 second before retry
                        continue
                    logger.error("Perplexity API returned empty response after retries")
                    raise HTTPException(status_code=500, detail="AI service returned empty response. Please try again.")
                logger.info(f"AI response received, length: {len(ai_response)}")
                break  # Success, exit retry loop
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as ai_error:
                if ai_attempt < max_ai_retries - 1:
                    logger.warning(f"Perplexity API error on attempt {ai_attempt + 1}/{max_ai_retries}: {str(ai_error)}, retrying...")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                logger.error(f"Perplexity API error after {max_ai_retries} attempts: {str(ai_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"AI service error: {str(ai_error)}. Please try again.")
        
        if not ai_response:
            raise HTTPException(status_code=500, detail="Failed to get AI response after retries. Please try again.")
        
        # Parse AI response (extract JSON)
        # Note: json is already imported at module level
        import re
        
        # Try to find JSON array in the response with multiple strategies
        json_str = None
        json_match = None
        
        # Strategy 1: Simple array pattern
        json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        
        # Strategy 2: More flexible pattern with capture group
        if not json_str:
            json_match = re.search(r'(\[[\s\S]*\])', ai_response)
            if json_match:
                json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
        
        # Strategy 3: Find array boundaries manually
        if not json_str:
            start_idx = ai_response.find('[')
            end_idx = ai_response.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx + 1]
        
        if not json_str:
            logger.error(f"AI response does not contain valid JSON array. Response length: {len(ai_response)}, First 1000 chars: {ai_response[:1000]}")
            raise HTTPException(
                status_code=500, 
                detail="AI response format invalid - no JSON array found. The AI service may have returned an unexpected format. Please try again."
            )
        
        # Try to clean up common JSON issues
        # Remove markdown code blocks if present (more aggressive)
        json_str = re.sub(r'```json\s*', '', json_str, flags=re.IGNORECASE)
        json_str = re.sub(r'```\s*', '', json_str)
        # Remove any leading/trailing whitespace and newlines
        json_str = json_str.strip()
        
        # Additional cleanup: Remove any text before the first [ and after the last ]
        if json_str:
            first_bracket = json_str.find('[')
            last_bracket = json_str.rfind(']')
            if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                json_str = json_str[first_bracket:last_bracket + 1]
                logger.info(f"Cleaned JSON: extracted array from position {first_bracket} to {last_bracket}")
        
        logger.info(f"JSON string length after cleanup: {len(json_str)}, first 200 chars: {json_str[:200]}")
        
        # Try to fix common JSON issues
        try:
            ai_goals = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"First JSON parse attempt failed: {str(e)}")
            logger.warning(f"JSON string (first 500 chars): {json_str[:500]}")
            
            # Try to fix common issues
            try:
                # Strategy: Fix unquoted property names
                # This regex finds property names that aren't quoted and quotes them
                # Pattern: word characters followed by colon (not already quoted)
                # Handle both inline and multiline cases
                fixed_json = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str, flags=re.MULTILINE)
                
                # Fix single quotes to double quotes (but be careful with apostrophes in strings)
                # First, protect strings with single quotes by temporarily replacing them
                # This is a simplified approach - replace single quotes around keys and values
                fixed_json = re.sub(r"'([^']*)':", r'"\1":', fixed_json)  # Keys with single quotes
                fixed_json = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_json)  # String values with single quotes
                
                # Try parsing again
                ai_goals = json.loads(fixed_json)
                logger.info("Successfully parsed JSON after fixing quotes and property names")
            except json.JSONDecodeError as e2:
                logger.warning(f"Second JSON parse attempt failed: {str(e2)}")
                try:
                    # Strategy: More aggressive fixing
                    # Remove any markdown code blocks completely
                    fixed_json = re.sub(r'```[a-z]*\s*', '', json_str)
                    fixed_json = re.sub(r'```\s*', '', fixed_json)
                    fixed_json = fixed_json.strip()
                    
                    # Find array boundaries
                    start_idx = fixed_json.find('[')
                    end_idx = fixed_json.rfind(']')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        fixed_json = fixed_json[start_idx:end_idx + 1]
                    
                    # Fix unquoted property names more aggressively
                    # Match: word at start of line or after comma/brace, followed by colon
                    # But avoid matching already quoted keys
                    fixed_json = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json)
                    
                    # Also fix keys that might be at the start of the JSON (not after { or ,)
                    # This handles cases like: {title: "value"} where title is the first key
                    fixed_json = re.sub(r'{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'{"\1":', fixed_json)
                    
                    # Fix trailing commas
                    fixed_json = re.sub(r',\s*}', '}', fixed_json)
                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                    
                    ai_goals = json.loads(fixed_json)
                    logger.info("Successfully parsed JSON after aggressive fixing")
                except json.JSONDecodeError as e3:
                    logger.error(f"Third JSON parse attempt failed: {str(e3)}")
                    error_pos = e3.pos if hasattr(e3, 'pos') else 0
                    logger.error(f"Error at position: {error_pos}")
                    if error_pos > 0:
                        start_pos = max(0, error_pos - 200)
                        end_pos = min(len(json_str), error_pos + 200)
                        logger.error(f"JSON string around error (chars {start_pos} to {end_pos}):")
                        logger.error(f"Context: ...{json_str[start_pos:end_pos]}...")
                        # Also log the problematic line
                        lines = json_str[:error_pos].split('\n')
                        if lines:
                            logger.error(f"Error on line {len(lines)}: {lines[-1][-150:]}")
                    logger.error(f"Full AI response (first 3000 chars): {ai_response[:3000]}")
                    logger.error(f"Extracted JSON string (first 2000 chars): {json_str[:2000]}")
                    if len(json_str) > 2000:
                        logger.error(f"Extracted JSON string (last 500 chars): ...{json_str[-500:]}")
                    
                    # Last resort: Try to extract just the array and use a more lenient parser
                    try:
                        import json5  # More lenient JSON parser
                        ai_goals = json5.loads(json_str)
                        logger.info("Successfully parsed JSON using json5")
                    except ImportError:
                        logger.warning("json5 not available, trying manual extraction")
                        # Last resort: Try to manually fix the most common issues
                        try:
                            # More aggressive regex to fix unquoted keys
                            # This handles cases like: {title: "value"} -> {"title": "value"}
                            fixed_json = json_str
                            
                            # Step 1: Fix unquoted property names (most common issue)
                            # Match unquoted identifiers before colon (after { or , or whitespace at start of line)
                            # This handles: {title: "value"} and also cases where there's whitespace
                            fixed_json = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json, flags=re.MULTILINE)
                            
                            # Step 2: Fix single quotes in keys
                            fixed_json = re.sub(r"'([^']+)':", r'"\1":', fixed_json)
                            
                            # Step 3: Fix single quotes in string values (but be careful)
                            # Only replace if it's a simple string value (not containing escaped quotes)
                            fixed_json = re.sub(r":\s*'([^']*)'([,\]}])", r': "\1"\2', fixed_json)
                            
                            # Step 4: Remove trailing commas
                            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                            
                            # Step 5: Ensure array boundaries are correct
                            start_idx = fixed_json.find('[')
                            end_idx = fixed_json.rfind(']')
                            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                                fixed_json = fixed_json[start_idx:end_idx + 1]
                            
                            ai_goals = json.loads(fixed_json)
                            logger.info("Successfully parsed JSON after manual aggressive fixing")
                        except Exception as e5:
                            logger.error(f"Manual extraction also failed: {str(e5)}")
                            # Last resort: Try to extract goals manually using regex
                            try:
                                logger.warning("Attempting manual goal extraction using regex patterns")
                                # Try multiple patterns to extract goal information
                                ai_goals = []
                                
                                # Pattern 1: Extract titles (with or without quotes, case-insensitive)
                                title_patterns = [
                                    r'"title"\s*:\s*"([^"]+)"',  # Quoted title
                                    r"'title'\s*:\s*'([^']+)'",  # Single-quoted title
                                    r'title\s*:\s*"([^"]+)"',    # Unquoted key, quoted value
                                    r'title\s*:\s*\'([^\']+)\'', # Unquoted key, single-quoted value
                                ]
                                
                                titles = []
                                for pattern in title_patterns:
                                    found = re.findall(pattern, json_str, re.IGNORECASE)
                                    if found:
                                        titles.extend(found)
                                        break
                                
                                # Pattern 2: Extract descriptions
                                desc_patterns = [
                                    r'"description"\s*:\s*"([^"]+)"',
                                    r"'description'\s*:\s*'([^']+)'",
                                    r'description\s*:\s*"([^"]+)"',
                                ]
                                
                                descriptions = []
                                for pattern in desc_patterns:
                                    found = re.findall(pattern, json_str, re.IGNORECASE)
                                    if found:
                                        descriptions.extend(found)
                                        break
                                
                                # Pattern 3: Extract departments
                                dept_patterns = [
                                    r'"department"\s*:\s*"([^"]+)"',
                                    r"'department'\s*:\s*'([^']+)'",
                                    r'department\s*:\s*"([^"]+)"',
                                ]
                                
                                departments = []
                                for pattern in dept_patterns:
                                    found = re.findall(pattern, json_str, re.IGNORECASE)
                                    if found:
                                        departments.extend(found)
                                        break
                                
                                if titles:
                                    logger.info(f"Found {len(titles)} goal titles via regex, creating minimal goals")
                                    # Create minimal goal structures
                                    for i, title in enumerate(titles[:6]):  # Max 6 goals
                                        desc = descriptions[i] if i < len(descriptions) else f"Goal for {title}"
                                        dept = departments[i] if i < len(departments) else "sales"
                                        ai_goals.append({
                                            "title": title,
                                            "description": desc,
                                            "department": dept,
                                            "owners": [],
                                            "teamMembers": [],
                                            "dependencies": [],
                                            "metrics": [],
                                            "keyResults": [
                                                {"description": "Key Result 1", "current": 0, "target": 100}
                                            ],
                                            "status": "on-track",
                                            "progress": 0
                                        })
                                    logger.info(f"Created {len(ai_goals)} minimal goals from regex extraction")
                                else:
                                    raise HTTPException(
                                        status_code=500, 
                                        detail=f"AI response JSON parsing failed. Could not extract any goals. Please try again."
                                    )
                            except Exception as e6:
                                logger.error(f"Regex extraction also failed: {str(e6)}")
                                logger.error(f"Full AI response (first 3000 chars): {ai_response[:3000]}")
                                logger.error(f"Extracted JSON string (first 1500 chars): {json_str[:1500]}")
                                raise HTTPException(
                                    status_code=500, 
                                    detail=f"AI response JSON parsing failed at position {e3.pos if hasattr(e3, 'pos') else 'unknown'}: {str(e3)}. The AI may have returned malformed JSON. Please try again."
                                )
                    except Exception as e4:
                        logger.error(f"All JSON parsing attempts failed. Last error: {str(e4)}")
                        raise HTTPException(
                            status_code=500, 
                            detail=f"AI response JSON parsing failed: {str(e4)}. The AI may have returned malformed JSON. Please try again or check the AI response format."
                        )
        
        if not isinstance(ai_goals, list):
            logger.error(f"AI response is not a list. Type: {type(ai_goals)}")
            raise HTTPException(status_code=500, detail="AI response is not a list")
        
        if len(ai_goals) == 0:
            logger.warning("AI generated empty goals list")
            raise HTTPException(status_code=500, detail="AI generated no goals")
        
        # Convert to GoalResponse format
        generated_goals = []
        for idx, ai_goal in enumerate(ai_goals):
            try:
                # Ensure ai_goal is a dict
                if not isinstance(ai_goal, dict):
                    logger.warning(f"Goal {idx} is not a dictionary, skipping")
                    continue
                
                # Map owner emails to user IDs
                owner_ids = []
                owners = ai_goal.get('owners', [])
                if not isinstance(owners, list):
                    owners = []
                for owner_email in owners:
                    if isinstance(owner_email, str):
                        user = next((u for u in all_users if u.get('email') == owner_email), None)
                        if user and user.get('id'):
                            owner_ids.append(user.get('id'))
                
                team_member_ids = []
                team_members = ai_goal.get('teamMembers', [])
                if not isinstance(team_members, list):
                    team_members = []
                for member_email in team_members:
                    if isinstance(member_email, str):
                        user = next((u for u in all_users if u.get('email') == member_email), None)
                        if user and user.get('id'):
                            team_member_ids.append(user.get('id'))
                
                # Validate department
                department = ai_goal.get('department', 'sales')
                valid_departments = ['sales', 'operations', 'finance', 'hr', 'marketing', 'technology']
                if department not in valid_departments:
                    department = 'sales'  # Default fallback
                
                # Validate status
                status = ai_goal.get('status', 'on-track')
                valid_statuses = ['on-track', 'at-risk', 'not-started']
                if status not in valid_statuses:
                    status = 'on-track'
                
                # Validate progress
                progress = ai_goal.get('progress', 0)
                if not isinstance(progress, (int, float)):
                    progress = 0
                progress = max(0, min(100, int(progress)))
                
                # Ensure keyResults is properly formatted
                key_results = ai_goal.get('keyResults', [])
                if not isinstance(key_results, list):
                    key_results = []
                # Validate each key result has required fields
                validated_key_results = []
                for kr in key_results:
                    if isinstance(kr, dict):
                        validated_key_results.append({
                            "description": str(kr.get('description', '')),
                            "current": int(kr.get('current', 0)) if isinstance(kr.get('current'), (int, float)) else 0,
                            "target": int(kr.get('target', 0)) if isinstance(kr.get('target'), (int, float)) else 0
                        })
                
                goal = {
                    "id": str(uuid.uuid4()),
                    "campaignId": str(request.campaignId),
                    "title": str(ai_goal.get('title', f'Untitled Goal {idx + 1}')),
                    "description": str(ai_goal.get('description', '')),
                    "department": department,
                    "owners": owner_ids if owner_ids else [],  # Ensure it's a list
                    "teamMembers": team_member_ids if team_member_ids else [],  # Ensure it's a list
                    "dependencies": ai_goal.get('dependencies', []) if isinstance(ai_goal.get('dependencies'), list) else [],
                    "metrics": ai_goal.get('metrics', []) if isinstance(ai_goal.get('metrics'), list) else [],
                    "keyResults": validated_key_results,
                    "status": status,
                    "progress": progress,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "tasks": []  # Initialize tasks array
                }
                generated_goals.append(goal)
            except Exception as goal_error:
                logger.error(f"Error processing goal {idx}: {str(goal_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue  # Skip invalid goals
        
        if len(generated_goals) == 0:
            raise HTTPException(status_code=500, detail="No valid goals could be generated from AI response")
        
        # Validate and convert to GoalResponse
        validated_goals = []
        for goal in generated_goals:
            try:
                # Ensure all required fields are present and properly formatted
                goal_dict = {
                    "id": goal.get("id", str(uuid.uuid4())),
                    "campaignId": goal.get("campaignId", str(request.campaignId)),
                    "title": str(goal.get("title", "Untitled Goal")),
                    "description": str(goal.get("description", "")),
                    "department": str(goal.get("department", "sales")),
                    "owners": goal.get("owners", []) if isinstance(goal.get("owners"), list) else [],
                    "teamMembers": goal.get("teamMembers", []) if isinstance(goal.get("teamMembers"), list) else [],
                    "dependencies": goal.get("dependencies", []) if isinstance(goal.get("dependencies"), list) else [],
                    "metrics": goal.get("metrics", []) if isinstance(goal.get("metrics"), list) else [],
                    "keyResults": goal.get("keyResults", []) if isinstance(goal.get("keyResults"), list) else [],
                    "status": str(goal.get("status", "on-track")),
                    "progress": int(goal.get("progress", 0)),
                    "createdAt": goal.get("createdAt", datetime.now(timezone.utc).isoformat()),
                    "tasks": goal.get("tasks", []) if isinstance(goal.get("tasks"), list) else []
                }
                validated_goal = GoalResponse(**goal_dict)
                validated_goals.append(validated_goal)
            except Exception as validation_error:
                logger.error(f"Goal validation error: {str(validation_error)}")
                logger.error(f"Goal data: {goal}")
                import traceback
                logger.error(f"Validation traceback: {traceback.format_exc()}")
                continue
        
        if len(validated_goals) == 0:
            raise HTTPException(status_code=500, detail="No valid goals could be validated")
        
        logger.info(f"Successfully generated {len(validated_goals)} goals")
        return validated_goals
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_goals_from_campaign: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate goals: {str(e)}. Please check server logs for details."
        )

@api_router.post("/kanban/goals", response_model=GoalResponse)
async def create_goal(request: GoalRequest, email: str = Depends(get_current_user)):
    """Create a new goal linked to a campaign"""
    try:
        goal = {
            "id": str(uuid.uuid4()),
            "campaignId": request.campaignId,
            "title": request.title,
            "description": request.description,
            "department": request.department,
            "owners": request.owners,
            "teamMembers": request.teamMembers or [],
            "dependencies": request.dependencies or [],
            "metrics": request.metrics or [],
            "keyResults": request.keyResults or [],
            "status": request.status,
            "progress": request.progress,
            "tasks": [],  # Initialize empty tasks array
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in goals collection
        await db.goals.insert_one(goal)
        
        # Update campaign to include goal ID
        kanban_doc = await db.kanban.find_one({})
        if kanban_doc:
            for camp in kanban_doc.get('live', []):
                if camp.get('id') == request.campaignId:
                    if 'goals' not in camp:
                        camp['goals'] = []
                    camp['goals'].append(goal['id'])
                    await db.kanban.update_one(
                        {"live.id": request.campaignId},
                        {"$set": {"live.$[elem].goals": camp['goals']}},
                        array_filters=[{"elem.id": request.campaignId}]
                    )
                    break
        
        return GoalResponse(**goal)
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")

@api_router.get("/kanban/campaigns/{campaignId}/goals", response_model=List[GoalResponse])
async def get_campaign_goals(campaignId: str, email: str = Depends(get_current_user)):
    """Get all goals for a specific campaign"""
    try:
        goals = await db.goals.find({"campaignId": campaignId}, {"_id": 0}).to_list(1000)
        return [GoalResponse(**goal) for goal in goals]
    except Exception as e:
        logger.error(f"Error fetching campaign goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

@api_router.get("/goals/by-department/{department}", response_model=List[GoalResponse])
async def get_goals_by_department(department: str, email: str = Depends(get_current_user)):
    """Get all goals for a specific department"""
    try:
        goals = await db.goals.find({"department": department.lower()}, {"_id": 0}).to_list(1000)
        return [GoalResponse(**goal) for goal in goals]
    except Exception as e:
        logger.error(f"Error fetching department goals: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

class UpdateGoalRequest(BaseModel):
    progress: Optional[int] = None
    status: Optional[str] = None
    keyResults: Optional[List[Dict]] = None
    tasks: Optional[List[Dict]] = None  # New field for user tasks

@api_router.get("/goals/{goalId}", response_model=GoalResponse)
async def get_goal(goalId: str, email: str = Depends(get_current_user)):
    """Get a specific goal by ID"""
    try:
        goal = await db.goals.find_one({"id": goalId}, {"_id": 0})
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return GoalResponse(**goal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching goal: {str(e)}")

@api_router.put("/goals/{goalId}", response_model=GoalResponse)
async def update_goal(goalId: str, request: UpdateGoalRequest, email: str = Depends(get_current_user)):
    """Update a goal - owners, team members, and admins can update"""
    try:
        # Get the goal
        goal = await db.goals.find_one({"id": goalId}, {"_id": 0})
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Get current user info
        user_doc = await db.users.find_one({"email": email}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_doc.get('id')
        
        # Check if user is owner, team member, or admin
        owners = goal.get('owners', [])
        team_members = goal.get('teamMembers', [])
        user_role = user_doc.get('role', '').lower()
        user_department = user_doc.get('department', '').lower()
        is_admin = user_role == 'admin' or user_department == 'admin'
        
        if user_id not in owners and user_id not in team_members and not is_admin:
            raise HTTPException(status_code=403, detail="You don't have permission to update this goal")
        
        # Update only provided fields
        update_data = {}
        if request.progress is not None:
            update_data['progress'] = max(0, min(100, request.progress))
        if request.status is not None:
            valid_statuses = ['on-track', 'at-risk', 'not-started', 'completed']
            if request.status in valid_statuses:
                update_data['status'] = request.status
        if request.keyResults is not None:
            update_data['keyResults'] = request.keyResults
        if request.tasks is not None:
            update_data['tasks'] = request.tasks
            update_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
            update_data['lastUpdatedBy'] = user_id
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update the goal
        await db.goals.update_one(
            {"id": goalId},
            {"$set": update_data}
        )
        
        # Get updated goal
        updated_goal = await db.goals.find_one({"id": goalId}, {"_id": 0})
        return GoalResponse(**updated_goal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating goal: {str(e)}")

@api_router.post("/kanban/accept")
async def accept_campaign(request: AcceptCampaignRequest, email: str = Depends(get_current_user)):
    """Move a campaign from recommended to live"""
    try:
        kanban_doc = await db.kanban.find_one({})
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        recommended = kanban_doc.get('recommended', [])
        live = kanban_doc.get('live', [])
        
        # Find the campaign in recommended
        campaign_to_move = None
        updated_recommended = []
        
        for campaign in recommended:
            if campaign.get('id') == request.campaignId:
                campaign_to_move = campaign
            else:
                updated_recommended.append(campaign)
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail="Campaign not found in recommended")
        
        # Add to live with acceptance timestamp
        campaign_to_move['status'] = 'live'
        campaign_to_move['acceptedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('startDate'):
            campaign_to_move['startDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        live.append(campaign_to_move)
        
        # Update MongoDB
        await db.kanban.update_one(
            {},
            {"$set": {
                "recommended": updated_recommended,
                "live": live,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved to live")
        
        return {"success": True, "message": "Campaign moved to live"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting campaign: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error accepting campaign: {str(e)}")

@api_router.post("/kanban/archive")
async def archive_campaign(request: AcceptCampaignRequest, email: str = Depends(get_current_user)):
    """Move a campaign from recommended or live to past (archived)"""
    try:
        kanban_doc = await db.kanban.find_one({})
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        recommended = kanban_doc.get('recommended', [])
        live = kanban_doc.get('live', [])
        past = kanban_doc.get('past', [])
        
        # Find the campaign in the source collection
        campaign_to_move = None
        source_collection = request.fromCollection
        
        if source_collection == 'recommended':
            updated_source = []
            for campaign in recommended:
                if campaign.get('id') == request.campaignId:
                    campaign_to_move = campaign
                else:
                    updated_source.append(campaign)
            if campaign_to_move:
                recommended = updated_source
        elif source_collection == 'live':
            updated_source = []
            for campaign in live:
                if campaign.get('id') == request.campaignId:
                    campaign_to_move = campaign
                else:
                    updated_source.append(campaign)
            if campaign_to_move:
                live = updated_source
        else:
            raise HTTPException(status_code=400, detail=f"Invalid fromCollection: {source_collection}")
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail=f"Campaign not found in {source_collection}")
        
        # Add to past with archive timestamp
        campaign_to_move['status'] = 'past'
        campaign_to_move['archivedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('endDate'):
            campaign_to_move['endDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        past.append(campaign_to_move)
        
        # Update MongoDB
        await db.kanban.update_one(
            {},
            {"$set": {
                "recommended": recommended,
                "live": live,
                "past": past,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved to past")
        
        return {"success": True, "message": "Campaign archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving campaign: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error archiving campaign: {str(e)}")

@api_router.post("/kanban/move-to-live")
async def move_to_live(request: AcceptCampaignRequest, email: str = Depends(get_current_user)):
    """Move a campaign from past (archived) to live (active)"""
    try:
        kanban_doc = await db.kanban.find_one({})
        if not kanban_doc:
            raise HTTPException(status_code=404, detail="Kanban data not found")
        
        past = kanban_doc.get('past', [])
        live = kanban_doc.get('live', [])
        
        # Find the campaign in past
        campaign_to_move = None
        updated_past = []
        
        for campaign in past:
            if campaign.get('id') == request.campaignId:
                campaign_to_move = campaign
            else:
                updated_past.append(campaign)
        
        if not campaign_to_move:
            raise HTTPException(status_code=404, detail="Campaign not found in archived")
        
        # Add to live with reactivation timestamp
        campaign_to_move['status'] = 'live'
        campaign_to_move['reactivatedAt'] = datetime.now(timezone.utc).isoformat()
        if not campaign_to_move.get('startDate'):
            campaign_to_move['startDate'] = datetime.now(timezone.utc).isoformat().split('T')[0]
        live.append(campaign_to_move)
        
        # Update MongoDB
        await db.kanban.update_one(
            {},
            {"$set": {
                "past": updated_past,
                "live": live,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Campaign '{campaign_to_move.get('title')}' moved from archived to live")
        
        return {"success": True, "message": "Campaign reactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving campaign to live: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error moving campaign to live: {str(e)}")

@api_router.get("/analytics/strategic-recommendations", response_model=StrategicRecommendationsResponse)
async def generate_strategic_recommendations(email: str = Depends(get_current_user)):
    """Generate NEW AI-powered strategic recommendations based on real Azure data and save to MongoDB"""
    import sys
    print("=" * 80, file=sys.stderr)
    print("🚀 STARTING strategic recommendations generation", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    logger.info("=" * 80)
    logger.info("🚀 STARTING strategic recommendations generation")
    logger.info(f"🚀 Called by user: {email}")
    logger.info("=" * 80)
    try:
        logger.info("🔍 Generating NEW strategic recommendations from Azure data")
        
        # Get comprehensive business data
        data = await db.business_data.find({}, {"_id": 0}).to_list(10000)
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        df = pd.DataFrame(data)
        
        # Check if DataFrame is empty or missing required columns
        if df.empty:
            logger.warning("DataFrame is empty")
            raise HTTPException(status_code=404, detail="No data available in database")
        
        # Check for required columns
        required_columns = ['Revenue', 'Gross_Profit', 'Units', 'Year', 'Business', 'Channel', 'Customer', 'Brand']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            logger.error(f"Available columns: {df.columns.tolist()}")
            raise HTTPException(status_code=500, detail=f"Missing required columns: {missing_columns}")
        
        # Calculate key metrics for context
        total_revenue = float(df['Revenue'].sum()) if not df.empty else 0
        total_profit = float(df['Gross_Profit'].sum()) if not df.empty else 0
        total_units = float(df['Units'].sum()) if not df.empty else 0
        
        # Year-over-year analysis
        yearly_data = df.groupby('Year').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum',
            'Units': 'sum'
        }).reset_index()
        
        # Top performing businesses
        business_perf = df.groupby('Business').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Top channels
        channel_perf = df.groupby('Channel').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Top customers
        customer_perf = df.groupby('Customer').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Get past campaigns for AI analysis
        kanban_doc = await db.kanban.find_one({})
        past_campaigns = kanban_doc.get('past', []) if kanban_doc else []
        
        # Build past campaigns context for AI
        past_context = ""
        if past_campaigns:
            past_context = "\n\nPAST CAMPAIGNS PERFORMANCE (for learning):\n"
            for idx, past_camp in enumerate(past_campaigns[:10], 1):  # Limit to 10 most recent
                past_context += f"{idx}. {past_camp.get('title', 'Unknown')}\n"
                past_context += f"   Category: {past_camp.get('category', 'N/A')}\n"
                past_context += f"   Budget: €{past_camp.get('budget', 0):,.2f}\n"
                past_context += f"   Expected Impact: €{past_camp.get('impact', {}).get('value', 0):,.2f} ({past_camp.get('impact', {}).get('percentage', 0)}% uplift)\n"
                past_context += f"   Period: {past_camp.get('startDate', 'N/A')} to {past_camp.get('endDate', 'N/A')}\n"
                past_context += f"   Channels: {', '.join(past_camp.get('channels', []))}\n\n"
        
        # Build data context for AI
        data_context = f"""
Business Performance Data Analysis:

OVERALL METRICS:
- Total Revenue: €{total_revenue:,.2f}
- Total Gross Profit: €{total_profit:,.2f}
- Total Units Sold: {total_units:,.0f}
- Profit Margin: {(total_profit/total_revenue*100) if total_revenue > 0 else 0:.2f}%

YEAR-OVER-YEAR PERFORMANCE:
{yearly_data.to_string(index=False) if not yearly_data.empty else 'No yearly data'}

TOP 5 BUSINESSES BY REVENUE:
{business_perf.to_string(index=False) if not business_perf.empty else 'No business data'}

TOP 5 CHANNELS BY REVENUE:
{channel_perf.to_string(index=False) if not channel_perf.empty else 'No channel data'}

TOP 5 CUSTOMERS BY REVENUE:
{customer_perf.to_string(index=False) if not customer_perf.empty else 'No customer data'}

AVAILABLE DATA PERIODS:
- Years: {sorted(df['Year'].unique().tolist()) if not df.empty else []}
- Total Records: {len(df)}
- Unique Businesses: {df['Business'].nunique() if not df.empty else 0}
- Unique Channels: {df['Channel'].nunique() if not df.empty else 0}
- Unique Brands: {df['Brand'].nunique() if not df.empty else 0}
- Unique Customers: {df['Customer'].nunique() if not df.empty else 0}
{past_context}
"""
        
        # Generate AI recommendations
        ai_prompt = f"""
Based on the following business data, generate 4-6 strategic marketing and business recommendations.

DATA CONTEXT:
{data_context}

REQUIREMENTS:
1. Each recommendation must be specific, actionable, and data-driven
2. Include realistic budget estimates (in Euros) based on the revenue scale
3. Calculate expected impact (revenue increase in Euros and percentage uplift)
4. Provide detailed reasoning based on the actual data patterns AND past campaign performance (if available)
5. Suggest appropriate marketing channels (e.g., Meta Ads, Google Ads, Email, Social Media, etc.)
6. Assign an AI confidence score (0-100) based on data strength
7. Categorize as 'acquisition', 'retention', or 'engagement'
8. Include realistic start and end dates (3-6 month campaigns)
9. If past campaigns are provided, learn from them - avoid repeating unsuccessful strategies and build on what worked

OUTPUT FORMAT (JSON array):
[
  {{
    "title": "Specific recommendation title",
    "description": "Detailed description of the recommendation",
    "category": "acquisition|retention|engagement",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD",
    "budget": 50000,
    "impact": {{"value": 250000, "percentage": 15.5}},
    "reasoning": "Detailed reasoning based on data patterns, specific numbers, and why this will work",
    "channels": ["Channel1", "Channel2"],
    "aiScore": 85
  }}
]

Return ONLY valid JSON array, no additional text.
"""
        
        try:
            logger.info("🤖 Calling Perplexity AI to generate recommendations...")
            logger.info(f"🤖 Prompt length: {len(ai_prompt)} characters")
            try:
                ai_response = await query_perplexity(ai_prompt)
            except Exception as ai_error:
                logger.error(f"❌ Perplexity API call failed: {str(ai_error)}")
                import traceback
                logger.error(f"❌ AI Error Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"AI service call failed: {str(ai_error)}")
            
            logger.info(f"🤖 AI Response received (length: {len(ai_response) if ai_response else 0})")
            
            if not ai_response:
                logger.error("❌ AI response is empty or None")
                raise HTTPException(status_code=500, detail="AI service returned empty response")
            
            if len(ai_response.strip()) < 10:
                logger.error(f"❌ AI response is too short: '{ai_response}'")
                raise HTTPException(status_code=500, detail="AI service returned invalid response (too short)")
            
            # Parse JSON from AI response (might have markdown code blocks)
            ai_response_clean = ai_response.strip()
            logger.info(f"🤖 AI Response (first 500 chars): {ai_response_clean[:500]}")
            
            if ai_response_clean.startswith('```json'):
                ai_response_clean = ai_response_clean[7:]
            if ai_response_clean.startswith('```'):
                ai_response_clean = ai_response_clean[3:]
            if ai_response_clean.endswith('```'):
                ai_response_clean = ai_response_clean[:-3]
            ai_response_clean = ai_response_clean.strip()
            
            logger.info(f"🤖 Parsing JSON from cleaned response...")
            recommendations_data = json.loads(ai_response_clean)
            logger.info(f"🤖 Successfully parsed {len(recommendations_data)} recommendations from AI")
            
            # Check if we got any recommendations
            if not recommendations_data or len(recommendations_data) == 0:
                logger.error("❌ AI returned empty recommendations array")
                raise HTTPException(status_code=500, detail="AI service returned empty recommendations. Please try again.")
            
            logger.info(f"✅ Processing {len(recommendations_data)} recommendations from AI")
            
            # Format recommendations
            recommendations = []
            for idx, rec in enumerate(recommendations_data[:6], 1):  # Limit to 6
                recommendations.append(StrategicRecommendation(
                    id=idx,
                    title=rec.get('title', f'Recommendation {idx}'),
                    description=rec.get('description', ''),
                    type='system',
                    category=rec.get('category', 'acquisition'),
                    startDate=rec.get('startDate', '2025-01-20'),
                    endDate=rec.get('endDate'),
                    budget=float(rec.get('budget', 50000)),
                    impact=rec.get('impact', {'value': 100000, 'percentage': 10}),
                    reasoning=rec.get('reasoning', ''),
                    channels=rec.get('channels', ['Email']),
                    aiScore=int(rec.get('aiScore', 75)),
                    status='recommended'
                ))
            
            # Save to MongoDB (replace existing recommended, keep live and past)
            kanban_doc = await db.kanban.find_one({})
            if not kanban_doc:
                # Create new document
                kanban_doc = {
                    "recommended": [rec.model_dump() for rec in recommendations],
                    "live": [],
                    "past": [],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await db.kanban.insert_one(kanban_doc)
            else:
                # Update only recommended field
                await db.kanban.update_one(
                    {},
                    {"$set": {
                        "recommended": [rec.model_dump() for rec in recommendations],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            # Move expired campaigns before returning
            await move_expired_campaigns()
            
            # Load current state from MongoDB
            updated_doc = await db.kanban.find_one({})
            live_campaigns = [StrategicRecommendation(**camp) for camp in updated_doc.get('live', [])] if updated_doc else []
            past_campaigns = [StrategicRecommendation(**camp) for camp in updated_doc.get('past', [])] if updated_doc else []
            
            logger.info(f"Generated {len(recommendations)} new recommendations and saved to MongoDB")
            
            return StrategicRecommendationsResponse(
                recommended=recommendations,
                live=live_campaigns,
                past=past_campaigns
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            logger.error(f"❌ AI Response (first 1000 chars): {ai_response[:1000] if 'ai_response' in locals() else 'No response'}")
            logger.error(f"❌ AI Response (last 500 chars): {ai_response[-500:] if 'ai_response' in locals() and len(ai_response) > 500 else 'N/A'}")
            # Try to extract JSON from the response if it's embedded in text
            recommendations_data = None
            if 'ai_response' in locals() and ai_response:
                import re
                # Try to find JSON array in the response (more robust pattern)
                json_match = re.search(r'\[[\s\S]*\]', ai_response)
                if json_match:
                    try:
                        recommendations_data = json.loads(json_match.group(0))
                        logger.info(f"✅ Extracted JSON from text: {len(recommendations_data)} recommendations")
                    except Exception as extract_error:
                        logger.error(f"❌ Failed to parse extracted JSON: {extract_error}")
                        recommendations_data = None
                
                # If still no JSON, try to find it between code blocks
                if not recommendations_data:
                    json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', ai_response)
                    if json_match:
                        try:
                            recommendations_data = json.loads(json_match.group(1))
                            logger.info(f"✅ Extracted JSON from code block: {len(recommendations_data)} recommendations")
                        except Exception as extract_error:
                            logger.error(f"❌ Failed to parse JSON from code block: {extract_error}")
            
            if not recommendations_data:
                raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON. The AI may have returned invalid JSON format. Error: {str(e)}")
            
            # Continue processing with extracted recommendations_data (fall through to the code below)
            logger.info(f"🤖 Processing {len(recommendations_data)} extracted recommendations...")
            
            # Format recommendations
            recommendations = []
            for idx, rec in enumerate(recommendations_data[:6], 1):  # Limit to 6
                recommendations.append(StrategicRecommendation(
                    id=idx,
                    title=rec.get('title', f'Recommendation {idx}'),
                    description=rec.get('description', ''),
                    type='system',
                    category=rec.get('category', 'acquisition'),
                    startDate=rec.get('startDate', '2025-01-20'),
                    endDate=rec.get('endDate'),
                    budget=float(rec.get('budget', 50000)),
                    impact=rec.get('impact', {'value': 100000, 'percentage': 10}),
                    reasoning=rec.get('reasoning', ''),
                    channels=rec.get('channels', ['Email']),
                    aiScore=int(rec.get('aiScore', 75)),
                    status='recommended'
                ))
            
            # Save to MongoDB (replace existing recommended, keep live and past)
            kanban_doc = await db.kanban.find_one({})
            if not kanban_doc:
                # Create new document
                kanban_doc = {
                    "recommended": [rec.model_dump() for rec in recommendations],
                    "live": [],
                    "past": [],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await db.kanban.insert_one(kanban_doc)
            else:
                # Update only recommended field
                await db.kanban.update_one(
                    {},
                    {"$set": {
                        "recommended": [rec.model_dump() for rec in recommendations],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            # Move expired campaigns before returning
            await move_expired_campaigns()
            
            # Load current state from MongoDB
            updated_doc = await db.kanban.find_one({})
            live_campaigns = [StrategicRecommendation(**camp) for camp in updated_doc.get('live', [])] if updated_doc else []
            past_campaigns = [StrategicRecommendation(**camp) for camp in updated_doc.get('past', [])] if updated_doc else []
            
            logger.info(f"✅ Generated {len(recommendations)} new recommendations and saved to MongoDB")
            
            # Final safety check - never return empty recommendations
            if not recommendations or len(recommendations) == 0:
                logger.error("❌ CRITICAL: Generated recommendations list is empty after processing!")
                raise HTTPException(status_code=500, detail="Failed to generate recommendations. AI returned empty results. Please try again.")
            
            logger.info(f"✅ Returning {len(recommendations)} recommendations to client")
            
            return StrategicRecommendationsResponse(
                recommended=recommendations,
                live=live_campaigns,
                past=past_campaigns
            )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Don't return empty arrays - raise an error so the user knows something went wrong
            raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}. Please check backend logs for details.")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Strategic recommendations error: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Strategic recommendations error: {str(e)}. Please check backend logs for details.")

@api_router.get("/analytics/customer-insights/chat/test")
async def test_customer_insights_chat(email: str = Depends(get_current_user)):
    """Test endpoint to verify customer insights chat route is accessible"""
    return {
        "status": "ok", 
        "message": "Customer insights chat endpoint is accessible", 
        "endpoint": "/api/analytics/customer-insights/chat",
        "method": "POST"
    }

class ActionItem(BaseModel):
    id: int
    title: str
    dueDate: str
    priority: str  # high, medium, low
    category: str  # critical, impact
    description: Optional[str] = None
    impact: Optional[str] = None  # high, medium, low

class ActionItemsResponse(BaseModel):
    critical: List[ActionItem]
    impact: List[ActionItem]

@api_router.get("/cockpit/action-items", response_model=ActionItemsResponse)
async def get_action_items(email: str = Depends(get_current_user)):
    """Get action items directly from MongoDB"""
    try:
        logger.info("🔍 Fetching action items from MongoDB")
        
        # Get action items directly from MongoDB
        cached_doc = await db.cockpit_action_items.find_one({})
        if cached_doc:
            logger.info("✅ Found action items document in MongoDB")
            logger.info(f"   Document keys: {list(cached_doc.keys())}")
            logger.info(f"   Critical items count: {len(cached_doc.get('critical', []))}")
            logger.info(f"   Impact items count: {len(cached_doc.get('impact', []))}")
            
            critical_items = []
            impact_items = []
            
            # Parse critical items with error handling
            for idx, item in enumerate(cached_doc.get('critical', [])):
                try:
                    # Log item structure for debugging
                    if idx == 0:
                        logger.info(f"   Sample critical item keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    critical_items.append(ActionItem(**item))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping invalid critical item {idx}: {e}")
                    logger.warning(f"   Item data: {item}")
                    continue
            
            # Parse impact items with error handling
            for idx, item in enumerate(cached_doc.get('impact', [])):
                try:
                    # Log item structure for debugging
                    if idx == 0:
                        logger.info(f"   Sample impact item keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                    impact_items.append(ActionItem(**item))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping invalid impact item {idx}: {e}")
                    logger.warning(f"   Item data: {item}")
                    continue
            
            logger.info(f"✅ Successfully loaded {len(critical_items)} critical and {len(impact_items)} impact items")
            
            # Return items (empty arrays if none found)
            return ActionItemsResponse(
                critical=critical_items,
                impact=impact_items
            )
        else:
            logger.warning("⚠️ No action items document found in MongoDB")
            logger.info("ℹ️ Auto-seeding action items...")
            
            # Auto-seed action items if collection is empty
            action_items_data = {
                "critical": [
                    {
                        "id": 1,
                        "title": "Reverse 45% YoY Revenue Decline: Emergency Recovery Plan",
                        "dueDate": "2025-12-15",
                        "priority": "high",
                        "impact": "high",
                        "category": "critical",
                        "description": "Urgent action required to address significant year-over-year revenue decline"
                    },
                    {
                        "id": 2,
                        "title": "Reduce Grocery Channel Concentration from 73.4%",
                        "dueDate": "2025-01-20",
                        "priority": "high",
                        "impact": "high",
                        "category": "critical",
                        "description": "Diversify channel mix to reduce dependency on grocery channel"
                    },
                    {
                        "id": 3,
                        "title": "Stabilize Top 5 Customer Relationships",
                        "dueDate": "2025-01-15",
                        "priority": "medium",
                        "impact": "high",
                        "category": "critical",
                        "description": "Focus on maintaining and strengthening relationships with top customers"
                    },
                    {
                        "id": 4,
                        "title": "Audit Food Business Unit Margin Compression",
                        "dueDate": "2025-02-01",
                        "priority": "medium",
                        "impact": "medium",
                        "category": "critical",
                        "description": "Investigate and address margin compression in food business unit"
                    },
                    {
                        "id": 5,
                        "title": "Launch Online Channel Growth Initiative",
                        "dueDate": "2025-02-28",
                        "priority": "low",
                        "impact": "medium",
                        "category": "critical",
                        "description": "Develop and execute strategy to grow online channel presence"
                    }
                ],
                "impact": [
                    {
                        "id": 6,
                        "title": "Scale Food Business to €22M+ via Category Expansion",
                        "dueDate": "2025-03-15",
                        "priority": "high",
                        "impact": "high",
                        "category": "impact",
                        "description": "Expand food business categories to achieve revenue target of €22M+"
                    },
                    {
                        "id": 7,
                        "title": "Develop Wholesale Channel Acceleration Program",
                        "dueDate": "2025-02-28",
                        "priority": "high",
                        "impact": "high",
                        "category": "impact",
                        "description": "Create program to accelerate growth in wholesale channel"
                    },
                    {
                        "id": 8,
                        "title": "Optimize Household & Beauty Segment Efficiency",
                        "dueDate": "2025-03-20",
                        "priority": "medium",
                        "impact": "medium",
                        "category": "impact",
                        "description": "Improve operational efficiency in household and beauty segments"
                    },
                    {
                        "id": 9,
                        "title": "Build International Channel to 5% of Revenue Mix",
                        "dueDate": "2025-03-31",
                        "priority": "low",
                        "impact": "medium",
                        "category": "impact",
                        "description": "Develop international channel to reach 5% of total revenue"
                    }
                ],
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # Save to MongoDB
            await db.cockpit_action_items.update_one(
                {},
                {"$set": action_items_data},
                upsert=True
            )
            
            logger.info(f"✅ Auto-seeded {len(action_items_data['critical'])} critical and {len(action_items_data['impact'])} impact items")
            
            # Parse and return the seeded items
            critical_items = [ActionItem(**item) for item in action_items_data['critical']]
            impact_items = [ActionItem(**item) for item in action_items_data['impact']]
            
            return ActionItemsResponse(
                critical=critical_items,
                impact=impact_items
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Action items error: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Action items error: {str(e)}")

@api_router.post("/cockpit/action-items/seed")
async def seed_action_items_endpoint(email: str = Depends(get_current_user)):
    """Seed action items in MongoDB if collection is empty"""
    try:
        # Check if data already exists
        existing = await db.cockpit_action_items.find_one({})
        if existing and (existing.get('critical') or existing.get('impact')):
            critical_count = len(existing.get('critical', []))
            impact_count = len(existing.get('impact', []))
            logger.info(f"Action items already exist: {critical_count} critical, {impact_count} impact")
            return {
                "message": "Action items already exist",
                "critical_count": critical_count,
                "impact_count": impact_count
            }
        
        # Action items data based on screenshot/requirements
        action_items_data = {
            "critical": [
                {
                    "id": 1,
                    "title": "Reverse 45% YoY Revenue Decline: Emergency Recovery Plan",
                    "dueDate": "2025-12-15",
                    "priority": "high",
                    "impact": "high",
                    "category": "critical",
                    "description": "Urgent action required to address significant year-over-year revenue decline"
                },
                {
                    "id": 2,
                    "title": "Reduce Grocery Channel Concentration from 73.4%",
                    "dueDate": "2025-01-20",
                    "priority": "high",
                    "impact": "high",
                    "category": "critical",
                    "description": "Diversify channel mix to reduce dependency on grocery channel"
                },
                {
                    "id": 3,
                    "title": "Stabilize Top 5 Customer Relationships",
                    "dueDate": "2025-01-15",
                    "priority": "medium",
                    "impact": "high",
                    "category": "critical",
                    "description": "Focus on maintaining and strengthening relationships with top customers"
                },
                {
                    "id": 4,
                    "title": "Audit Food Business Unit Margin Compression",
                    "dueDate": "2025-02-01",
                    "priority": "medium",
                    "impact": "medium",
                    "category": "critical",
                    "description": "Investigate and address margin compression in food business unit"
                },
                {
                    "id": 5,
                    "title": "Launch Online Channel Growth Initiative",
                    "dueDate": "2025-02-28",
                    "priority": "low",
                    "impact": "medium",
                    "category": "critical",
                    "description": "Develop and execute strategy to grow online channel presence"
                }
            ],
            "impact": [
                {
                    "id": 6,
                    "title": "Scale Food Business to €22M+ via Category Expansion",
                    "dueDate": "2025-03-15",
                    "priority": "high",
                    "impact": "high",
                    "category": "impact",
                    "description": "Expand food business categories to achieve revenue target of €22M+"
                },
                {
                    "id": 7,
                    "title": "Develop Wholesale Channel Acceleration Program",
                    "dueDate": "2025-02-28",
                    "priority": "high",
                    "impact": "high",
                    "category": "impact",
                    "description": "Create program to accelerate growth in wholesale channel"
                },
                {
                    "id": 8,
                    "title": "Optimize Household & Beauty Segment Efficiency",
                    "dueDate": "2025-03-20",
                    "priority": "medium",
                    "impact": "medium",
                    "category": "impact",
                    "description": "Improve operational efficiency in household and beauty segments"
                },
                {
                    "id": 9,
                    "title": "Build International Channel to 5% of Revenue Mix",
                    "dueDate": "2025-03-31",
                    "priority": "low",
                    "impact": "medium",
                    "category": "impact",
                    "description": "Develop international channel to reach 5% of total revenue"
                }
            ],
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into MongoDB
        result = await db.cockpit_action_items.update_one(
            {},
            {"$set": action_items_data},
            upsert=True
        )
        
        logger.info(f"✅ Seeded action items: {len(action_items_data['critical'])} critical, {len(action_items_data['impact'])} impact")
        
        return {
            "message": "Action items seeded successfully",
            "critical_count": len(action_items_data['critical']),
            "impact_count": len(action_items_data['impact'])
        }
        
    except Exception as e:
        logger.error(f"❌ Error seeding action items: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error seeding action items: {str(e)}")

# Root Cause Analysis Endpoints
        
        df = pd.DataFrame(data)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available in database")
        
        # Check for required columns
        required_columns = ['Revenue', 'Gross_Profit', 'Units', 'Year', 'Business', 'Channel', 'Customer', 'Brand']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise HTTPException(status_code=500, detail=f"Missing required columns: {missing_columns}")
        
        # Calculate key metrics for context
        total_revenue = float(df['Revenue'].sum()) if not df.empty else 0
        total_profit = float(df['Gross_Profit'].sum()) if not df.empty else 0
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Year-over-year analysis
        yearly_data = df.groupby('Year').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum',
            'Units': 'sum'
        }).reset_index()
        
        # Top performing businesses
        business_perf = df.groupby('Business').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Top channels
        channel_perf = df.groupby('Channel').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Top customers
        customer_perf = df.groupby('Customer').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False).head(5)
        
        # Identify issues and opportunities
        issues = []
        opportunities = []
        
        # Check for declining revenue
        if len(yearly_data) > 1:
            latest_year = yearly_data.iloc[-1]['Revenue']
            prev_year = yearly_data.iloc[-2]['Revenue'] if len(yearly_data) > 1 else latest_year
            if latest_year < prev_year:
                decline_pct = ((prev_year - latest_year) / prev_year * 100) if prev_year > 0 else 0
                issues.append(f"Revenue declined by {decline_pct:.1f}% year-over-year")
        
        # Check profit margin
        if profit_margin < 20:
            issues.append(f"Profit margin is low at {profit_margin:.1f}%, below industry standard")
        
        # Check channel concentration
        top_channel_revenue = channel_perf.iloc[0]['Revenue'] if not channel_perf.empty else 0
        channel_concentration = (top_channel_revenue / total_revenue * 100) if total_revenue > 0 else 0
        if channel_concentration > 70:
            issues.append(f"High channel concentration: {channel_concentration:.1f}% of revenue from single channel")
        
        # Opportunities
        if not business_perf.empty:
            top_business = business_perf.iloc[0]
            opportunities.append(f"Expand {top_business['Business']} business segment (€{top_business['Revenue']:,.0f} revenue)")
        
        if len(channel_perf) > 1:
            underperforming_channels = channel_perf[channel_perf['Revenue'] < channel_perf.iloc[0]['Revenue'] * 0.3]
            if not underperforming_channels.empty:
                opportunities.append(f"Optimize {underperforming_channels.iloc[0]['Channel']} channel performance")
        
        # Build data context for AI
        data_context = f"""
Business Performance Analysis:

OVERALL METRICS:
- Total Revenue: €{total_revenue:,.2f}
- Total Gross Profit: €{total_profit:,.2f}
- Profit Margin: {profit_margin:.2f}%

YEAR-OVER-YEAR PERFORMANCE:
{yearly_data.to_string(index=False) if not yearly_data.empty else 'No yearly data'}

TOP 5 BUSINESSES BY REVENUE:
{business_perf.to_string(index=False) if not business_perf.empty else 'No business data'}

TOP 5 CHANNELS BY REVENUE:
{channel_perf.to_string(index=False) if not channel_perf.empty else 'No channel data'}

TOP 5 CUSTOMERS BY REVENUE:
{customer_perf.to_string(index=False) if not customer_perf.empty else 'No customer data'}

IDENTIFIED ISSUES:
{chr(10).join(f"- {issue}" for issue in issues) if issues else "- No critical issues identified"}

OPPORTUNITIES:
{chr(10).join(f"- {opp}" for opp in opportunities) if opportunities else "- No specific opportunities identified"}
"""
        
        # Generate AI action items
        ai_prompt = f"""
Based on the following business data analysis, generate 6-9 strategic action items.
Split them into two categories:
1. CRITICAL: Urgent issues that need immediate attention (revenue decline, profit margin issues, operational problems)
2. IMPACT: High-impact opportunities for growth (expansion, optimization, new initiatives)

DATA CONTEXT:
{data_context}

REQUIREMENTS:
1. Generate 3-5 CRITICAL action items (urgent, time-sensitive issues)
2. Generate 3-4 IMPACT action items (growth opportunities, optimizations)
3. Each action item must have:
   - A specific, actionable title (max 60 characters)
   - A due date within the next 30-90 days (format: YYYY-MM-DD)
   - A priority level: "high", "medium", or "low"
   - An impact level: "high", "medium", or "low" (expected business impact)
   - A brief description (1-2 sentences)
4. CRITICAL REQUIREMENT: Each category (critical AND impact) MUST have at least one item with EACH priority level (high, medium, low)
   - Critical category: must have at least 1 high, 1 medium, and 1 low priority item
   - Impact category: must have at least 1 high, 1 medium, and 1 low priority item
5. Base recommendations on actual data patterns and metrics shown above
6. Make titles specific and data-driven (mention actual numbers, channels, businesses when relevant)

OUTPUT FORMAT (JSON array):
{{
  "critical": [
    {{
      "title": "Specific critical action title",
      "dueDate": "2025-01-30",
      "priority": "high|medium|low",
      "impact": "high|medium|low",
      "description": "Brief description of why this is critical"
    }}
  ],
  "impact": [
    {{
      "title": "Specific impact action title",
      "dueDate": "2025-02-15",
      "priority": "high|medium|low",
      "impact": "high|medium|low",
      "description": "Brief description of expected impact"
    }}
  ]
}}

Return ONLY valid JSON object, no markdown, no code blocks, no additional text.
"""
        
        try:
            logger.info("🤖 Calling Perplexity AI to generate action items...")
            ai_response = await query_perplexity(ai_prompt)
            
            if not ai_response:
                raise HTTPException(status_code=500, detail="AI service returned empty response")
            
            # Parse JSON response
            ai_response_clean = ai_response.strip()
            if ai_response_clean.startswith('```json'):
                ai_response_clean = ai_response_clean[7:]
            if ai_response_clean.startswith('```'):
                ai_response_clean = ai_response_clean[3:]
            if ai_response_clean.endswith('```'):
                ai_response_clean = ai_response_clean[:-3]
            ai_response_clean = ai_response_clean.strip()
            
            try:
                action_items_data = json.loads(ai_response_clean)
            except json.JSONDecodeError as e:
                # Try to extract JSON using regex as fallback
                import re
                try:
                    # Try to find JSON object in the response
                    json_match = re.search(r'\{[\s\S]*"critical"[\s\S]*"impact"[\s\S]*\}', ai_response_clean)
                    if json_match:
                        action_items_data = json.loads(json_match.group(0))
                    else:
                        raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
                except:
                    logger.error(f"Failed to parse action items JSON: {e}")
                    raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
            
            # Validate and structure response
            critical_items = []
            impact_items = []
            
            # Process critical items
            for idx, item in enumerate(action_items_data.get('critical', [])[:5], 1):
                try:
                    critical_items.append(ActionItem(
                        id=idx,
                        title=item.get('title', f'Critical Action {idx}')[:60],
                        dueDate=item.get('dueDate', '2025-02-15'),
                        priority=item.get('priority', 'high') if item.get('priority') in ['high', 'medium', 'low'] else 'high',
                        impact=item.get('impact', item.get('priority', 'high')) if item.get('impact', item.get('priority', 'high')) in ['high', 'medium', 'low'] else item.get('priority', 'high'),
                        category='critical',
                        description=item.get('description', '')
                    ))
                except Exception as e:
                    logger.warning(f"Error processing critical item {idx}: {e}")
                    continue
            
            # Process impact items
            for idx, item in enumerate(action_items_data.get('impact', [])[:5], 1):
                try:
                    impact_items.append(ActionItem(
                        id=len(critical_items) + idx,
                        title=item.get('title', f'Impact Action {idx}')[:60],
                        dueDate=item.get('dueDate', '2025-02-20'),
                        priority=item.get('priority', 'medium') if item.get('priority') in ['high', 'medium', 'low'] else 'medium',
                        impact=item.get('impact', item.get('priority', 'medium')) if item.get('impact', item.get('priority', 'medium')) in ['high', 'medium', 'low'] else item.get('priority', 'medium'),
                        category='impact',
                        description=item.get('description', '')
                    ))
                except Exception as e:
                    logger.warning(f"Error processing impact item {idx}: {e}")
                    continue
            
            # Ensure EACH category has items with ALL priority levels (high, medium, low)
            # Check Critical category
            critical_priorities = [item.priority for item in critical_items]
            if critical_items:
                # Ensure Critical has high priority
                if 'high' not in critical_priorities:
                    # Find first item and set to high
                    if len(critical_items) > 0:
                        critical_items[0].priority = 'high'
                        critical_priorities[0] = 'high'
                
                # Ensure Critical has medium priority
                if 'medium' not in critical_priorities:
                    # Find second item or last item and set to medium
                    if len(critical_items) > 1:
                        critical_items[1].priority = 'medium'
                        critical_priorities[1] = 'medium'
                    elif len(critical_items) == 1:
                        # If only one item, we need to add another or change this one
                        # Change to medium and add a high priority item
                        critical_items[0].priority = 'high'
                        # Add a medium priority item
                        from datetime import datetime, timedelta
                        due_date = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
                        critical_items.append(ActionItem(
                            id=len(critical_items) + 1,
                            title="Address Critical Business Issue",
                            dueDate=due_date,
                            priority='medium',
                            impact='medium',
                            category='critical',
                            description="Address identified critical business issue based on data analysis"
                        ))
                        critical_priorities.append('medium')
                
                # Ensure Critical has low priority
                if 'low' not in critical_priorities:
                    # Find last item and set to low, or add new item
                    if len(critical_items) > 2:
                        critical_items[-1].priority = 'low'
                        critical_priorities[-1] = 'low'
                    else:
                        # Add a low priority item
                        from datetime import datetime, timedelta
                        due_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
                        critical_items.append(ActionItem(
                            id=len(critical_items) + 1,
                            title="Review and Optimize Operations",
                            dueDate=due_date,
                            priority='low',
                            impact='low',
                            category='critical',
                            description="Review operational processes for optimization opportunities"
                        ))
                        critical_priorities.append('low')
            
            # Check Impact category
            impact_priorities = [item.priority for item in impact_items]
            if impact_items:
                # Ensure Impact has high priority
                if 'high' not in impact_priorities:
                    # Find first item and set to high
                    if len(impact_items) > 0:
                        impact_items[0].priority = 'high'
                        impact_priorities[0] = 'high'
                
                # Ensure Impact has medium priority
                if 'medium' not in impact_priorities:
                    # Find second item or add new item
                    if len(impact_items) > 1:
                        impact_items[1].priority = 'medium'
                        impact_priorities[1] = 'medium'
                    elif len(impact_items) == 1:
                        # Change to high and add medium
                        impact_items[0].priority = 'high'
                        from datetime import datetime, timedelta
                        due_date = (datetime.now() + timedelta(days=50)).strftime('%Y-%m-%d')
                        impact_items.append(ActionItem(
                            id=len(critical_items) + len(impact_items) + 1,
                            title="Optimize Growth Opportunities",
                            dueDate=due_date,
                            priority='medium',
                            impact='high',
                            category='impact',
                            description="Optimize identified growth opportunities for maximum impact"
                        ))
                        impact_priorities.append('medium')
                
                # Ensure Impact has low priority
                if 'low' not in impact_priorities:
                    # Find last item and set to low, or add new item
                    if len(impact_items) > 2:
                        impact_items[-1].priority = 'low'
                        impact_priorities[-1] = 'low'
                    else:
                        # Add a low priority item
                        from datetime import datetime, timedelta
                        due_date = (datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d')
                        impact_items.append(ActionItem(
                            id=len(critical_items) + len(impact_items) + 1,
                            title="Explore Long-term Strategic Initiatives",
                            dueDate=due_date,
                            priority='low',
                            impact='medium',
                            category='impact',
                            description="Explore long-term strategic initiatives for sustainable growth"
                        ))
                        impact_priorities.append('low')
            
            # Final validation: Ensure minimum items in each category
            # Critical should have at least 3 items (one of each priority)
            while len(critical_items) < 3:
                from datetime import datetime, timedelta
                priorities_needed = ['high', 'medium', 'low']
                existing_priorities = [item.priority for item in critical_items]
                missing_priority = [p for p in priorities_needed if p not in existing_priorities]
                if missing_priority:
                    due_date = (datetime.now() + timedelta(days=30 + len(critical_items) * 15)).strftime('%Y-%m-%d')
                    critical_items.append(ActionItem(
                        id=len(critical_items) + 1,
                        title=f"Critical Action Item {len(critical_items) + 1}",
                        dueDate=due_date,
                        priority=missing_priority[0],
                        impact=missing_priority[0],
                        category='critical',
                        description="Critical action item based on business data analysis"
                    ))
                else:
                    break
            
            # Impact should have at least 3 items (one of each priority)
            while len(impact_items) < 3:
                from datetime import datetime, timedelta
                priorities_needed = ['high', 'medium', 'low']
                existing_priorities = [item.priority for item in impact_items]
                missing_priority = [p for p in priorities_needed if p not in existing_priorities]
                if missing_priority:
                    due_date = (datetime.now() + timedelta(days=40 + len(impact_items) * 15)).strftime('%Y-%m-%d')
                    impact_items.append(ActionItem(
                        id=len(critical_items) + len(impact_items) + 1,
                        title=f"Impact Action Item {len(impact_items) + 1}",
                        dueDate=due_date,
                        priority=missing_priority[0],
                        impact=missing_priority[0],
                        category='impact',
                        description="High-impact action item based on business data analysis"
                    ))
                else:
                    break
            
            # Ensure we have at least some items with all priorities
            if not critical_items and not impact_items:
                # Fallback to default items with all priority levels
                from datetime import datetime, timedelta
                critical_items = [
                    ActionItem(id=1, title="Review Revenue Trends", dueDate=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), priority="high", impact="high", category="critical", description="Analyze revenue trends and identify growth opportunities"),
                    ActionItem(id=2, title="Optimize Channel Performance", dueDate=(datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'), priority="medium", impact="medium", category="critical", description="Review and optimize underperforming channels"),
                    ActionItem(id=3, title="Address Operational Issues", dueDate=(datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'), priority="low", impact="low", category="critical", description="Review and address operational inefficiencies"),
                ]
                impact_items = [
                    ActionItem(id=4, title="Expand Top Business Segment", dueDate=(datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d'), priority="high", impact="high", category="impact", description="Leverage top-performing business segment for expansion"),
                    ActionItem(id=5, title="Improve Profit Margins", dueDate=(datetime.now() + timedelta(days=50)).strftime('%Y-%m-%d'), priority="medium", impact="high", category="impact", description="Identify cost optimization opportunities"),
                    ActionItem(id=6, title="Explore New Market Opportunities", dueDate=(datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d'), priority="low", impact="medium", category="impact", description="Research and explore new market segments for growth"),
                ]
            
            logger.info(f"✅ Generated {len(critical_items)} critical and {len(impact_items)} impact action items")
            
            # Save to MongoDB cache
            cache_doc = {
                "critical": [item.model_dump() for item in critical_items],
                "impact": [item.model_dump() for item in impact_items],
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # Update or insert cache document
            await db.cockpit_action_items.update_one(
                {},
                {"$set": cache_doc},
                upsert=True
            )
            
            logger.info("✅ Action items saved to MongoDB cache")
            
            return ActionItemsResponse(
                critical=critical_items,
                impact=impact_items
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error generating action items: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error generating action items: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Action items error: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Action items error: {str(e)}")

# Root Cause Analysis Endpoints
@api_router.get("/root-cause-analysis/test", name="test_root_cause")
async def test_root_cause_route():
    """Test endpoint to verify root cause analysis route is accessible"""
    logger.info("🔍🔍🔍 TEST ENDPOINT CALLED!")
    return {
        "status": "ok",
        "message": "Root cause analysis endpoint is accessible",
        "endpoint": "/api/root-cause-analysis/issues"
    }

@api_router.get("/root-cause-analysis/issues", response_model=RootCauseAnalysisResponse, name="get_root_cause_issues")
async def get_root_cause_issues(email: str = Depends(get_current_user)):
    """Load root cause analysis issues from MongoDB"""
    logger.info(f"🔍🔍🔍 GET /root-cause-analysis/issues called by {email}")
    try:
        rca_doc = await db.root_cause_analysis.find_one({})
        
        if not rca_doc:
            # Initialize empty document
            initial_doc = {
                "issues": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await db.root_cause_analysis.insert_one(initial_doc)
            return RootCauseAnalysisResponse(
                issues=[],
                summary={"critical": 0, "investigating": 0, "resolved": 0}
            )
        
        # Convert MongoDB issues to RootCauseIssue objects
        issues = []
        for issue_data in rca_doc.get('issues', []):
            try:
                # Ensure id is an int
                if 'id' not in issue_data or not isinstance(issue_data.get('id'), int):
                    issue_data['id'] = len(issues) + 1
                issues.append(RootCauseIssue(**issue_data))
            except Exception as e:
                logger.warning(f"Error parsing issue: {e}, skipping issue: {issue_data}")
                continue
        
        # Calculate summary
        critical_count = len([i for i in issues if i.severity == 'high'])
        investigating_count = len([i for i in issues if i.status == 'investigating'])
        resolved_count = len([i for i in issues if i.status == 'resolved'])
        
        return RootCauseAnalysisResponse(
            issues=issues,
            summary={
                "critical": critical_count,
                "investigating": investigating_count,
                "resolved": resolved_count
            }
        )
    except Exception as e:
        logger.error(f"Error loading root cause issues: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error loading root cause issues: {str(e)}")

@api_router.post("/root-cause-analysis/generate", response_model=RootCauseAnalysisResponse, name="generate_root_cause_issues")
async def generate_root_cause_issues(email: str = Depends(get_current_user)):
    """Generate NEW AI-powered root cause analysis issues based on real business data"""
    logger.info(f"🔍🔍🔍 POST /root-cause-analysis/generate called by {email}")
    try:
        logger.info("🔍 Generating NEW root cause analysis issues from business data")
        
        # Get comprehensive business data
        data = await db.business_data.find({}, {"_id": 0}).to_list(10000)
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        df = pd.DataFrame(data)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available in database")
        
        required_columns = ['Revenue', 'Gross_Profit', 'Units', 'Year', 'Business', 'Channel', 'Customer', 'Brand']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise HTTPException(status_code=500, detail=f"Missing required columns: {missing_columns}")
        
        # Calculate key metrics for context
        total_revenue = float(df['Revenue'].sum()) if not df.empty else 0
        total_profit = float(df['Gross_Profit'].sum()) if not df.empty else 0
        total_units = float(df['Units'].sum()) if not df.empty else 0
        profit_margin = (total_profit/total_revenue*100) if total_revenue > 0 else 0
        
        # Year-over-year analysis
        yearly_data = df.groupby('Year').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum',
            'Units': 'sum'
        }).reset_index().sort_values('Year')
        
        # Identify declining trends
        if len(yearly_data) > 1:
            latest_year = yearly_data.iloc[-1]
            previous_year = yearly_data.iloc[-2] if len(yearly_data) > 1 else None
            revenue_decline = previous_year and latest_year['Revenue'] < previous_year['Revenue']
            profit_decline = previous_year and latest_year['Gross_Profit'] < previous_year['Gross_Profit']
        else:
            revenue_decline = False
            profit_decline = False
        
        # Business performance by segment
        business_perf = df.groupby('Business').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Channel performance
        channel_perf = df.groupby('Channel').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Customer performance
        customer_perf = df.groupby('Customer').agg({
            'Revenue': 'sum',
            'Gross_Profit': 'sum'
        }).reset_index().sort_values('Revenue', ascending=False)
        
        # Build data context for AI
        data_context = f"""
Business Performance Data Analysis for Root Cause Analysis:

OVERALL METRICS:
- Total Revenue: €{total_revenue:,.2f}
- Total Gross Profit: €{total_profit:,.2f}
- Total Units Sold: {total_units:,.0f}
- Profit Margin: {profit_margin:.2f}%

YEAR-OVER-YEAR PERFORMANCE:
{yearly_data.to_string(index=False) if not yearly_data.empty else 'No yearly data'}

TREND ANALYSIS:
- Revenue Trend: {'Declining' if revenue_decline else 'Stable/Increasing'}
- Profit Trend: {'Declining' if profit_decline else 'Stable/Increasing'}

TOP 5 BUSINESSES BY REVENUE:
{business_perf.head(5).to_string(index=False) if not business_perf.empty else 'No business data'}

TOP 5 CHANNELS BY REVENUE:
{channel_perf.head(5).to_string(index=False) if not channel_perf.empty else 'No channel data'}

TOP 5 CUSTOMERS BY REVENUE:
{customer_perf.head(5).to_string(index=False) if not customer_perf.empty else 'No customer data'}

AVAILABLE DATA PERIODS:
- Years: {sorted(df['Year'].unique().tolist()) if not df.empty else []}
- Total Records: {len(df)}
- Unique Businesses: {df['Business'].nunique() if not df.empty else 0}
- Unique Channels: {df['Channel'].nunique() if not df.empty else 0}
- Unique Brands: {df['Brand'].nunique() if not df.empty else 0}
- Unique Customers: {df['Customer'].nunique() if not df.empty else 0}
"""
        
        # Generate AI root cause analysis issues
        ai_prompt = f"""
Based on the following business performance data, identify 3-5 critical business issues that need root cause analysis.

DATA CONTEXT:
{data_context}

REQUIREMENTS:
1. Identify real issues based on data patterns (declining revenue, profit margins, customer churn, etc.)
2. For each issue, provide:
   - A clear, specific title (e.g., "Sales Decline in Q4", "Customer Churn Rate Increase")
   - Severity level: "high", "medium", or "low" based on impact
   - Root cause: A specific, data-driven explanation of why this issue is occurring
   - Impact: Quantified impact (e.g., "€250K revenue loss", "15% increase in churn")
   - AI Recommendation: Specific, actionable recommendation to address the root cause
   - Status: "investigating", "resolved", or "monitoring"
3. Base recommendations on actual data patterns and trends
4. Prioritize issues with highest business impact
5. Provide realistic impact estimates based on the data scale

OUTPUT FORMAT (JSON array):
[
  {{
    "title": "Specific issue title",
    "severity": "high|medium|low",
    "rootCause": "Detailed explanation of the root cause based on data",
    "impact": "Quantified impact description (e.g., €250K revenue loss)",
    "recommendation": "Specific, actionable AI recommendation",
    "status": "investigating|resolved|monitoring"
  }}
]

Return ONLY valid JSON array, no additional text.
"""
        
        try:
            ai_response = await query_perplexity(ai_prompt)
            
            # Parse JSON from AI response
            ai_response_clean = ai_response.strip()
            if ai_response_clean.startswith('```json'):
                ai_response_clean = ai_response_clean[7:]
            if ai_response_clean.startswith('```'):
                ai_response_clean = ai_response_clean[3:]
            if ai_response_clean.endswith('```'):
                ai_response_clean = ai_response_clean[:-3]
            ai_response_clean = ai_response_clean.strip()
            
            issues_data = json.loads(ai_response_clean)
            
            # Format issues
            issues = []
            for idx, issue_data in enumerate(issues_data[:5], 1):  # Limit to 5
                issues.append(RootCauseIssue(
                    id=idx,
                    title=issue_data.get('title', f'Issue {idx}'),
                    severity=issue_data.get('severity', 'medium'),
                    rootCause=issue_data.get('rootCause', ''),
                    impact=issue_data.get('impact', ''),
                    recommendation=issue_data.get('recommendation', ''),
                    status=issue_data.get('status', 'investigating'),
                    createdAt=datetime.now(timezone.utc).isoformat(),
                    updatedAt=datetime.now(timezone.utc).isoformat()
                ))
            
            # Save to MongoDB
            rca_doc = await db.root_cause_analysis.find_one({})
            if not rca_doc:
                rca_doc = {
                    "issues": [issue.model_dump() for issue in issues],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await db.root_cause_analysis.insert_one(rca_doc)
            else:
                await db.root_cause_analysis.update_one(
                    {},
                    {"$set": {
                        "issues": [issue.model_dump() for issue in issues],
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            # Calculate summary
            critical_count = len([i for i in issues if i.severity == 'high'])
            investigating_count = len([i for i in issues if i.status == 'investigating'])
            resolved_count = len([i for i in issues if i.status == 'resolved'])
            
            logger.info(f"Generated {len(issues)} new root cause issues and saved to MongoDB")
            
            return RootCauseAnalysisResponse(
                issues=issues,
                summary={
                    "critical": critical_count,
                    "investigating": investigating_count,
                    "resolved": resolved_count
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response (first 500 chars): {ai_response[:500] if 'ai_response' in locals() else 'No response'}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating root cause issues: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error generating root cause issues: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Root cause analysis error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Root cause analysis error: {str(e)}")

@api_router.get(
    "/analytics/customer-insights/filters",
    summary="Get Customer Insights Filter Options",
    description="Returns available years and months from the Shopify customer data for filtering."
)
async def get_customer_insights_filters(email: str = Depends(get_current_user)):
    """
    Get filter options for customer insights based on actual Shopify data.
    
    Returns only years and months that exist in the Shopify data, ensuring filters are accurate.
    """
    try:
        # Load Shopify_customer_df.csv
        csv_path = ROOT_DIR / 'Shopify_customer_df.csv'
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Shopify_customer_df.csv file not found")
        
        df = pd.read_csv(csv_path)
        if df.empty:
            return {
                "years": [],
                "months": []
            }
        
        # Convert date columns
        if 'Day' in df.columns:
            try:
                df['Day'] = pd.to_datetime(df['Day'], errors='coerce')
                df['Year'] = df['Day'].dt.year
                df['Month'] = df['Day'].dt.month
                df['MonthName'] = df['Day'].dt.strftime('%B')
                
                # Get unique years and months from actual data
                years = sorted([int(y) for y in df['Year'].dropna().unique() if pd.notna(y)])
                months = sorted(df['MonthName'].dropna().unique().tolist(), key=lambda x: {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }.get(x, 999))
                
                logger.info(f"✅ Customer insights filters - Years: {years}, Months: {len(months)}")
                
                return {
                    "years": years,
                    "months": months
                }
            except Exception as e:
                logger.error(f"Error processing date columns for filters: {str(e)}")
                return {
                    "years": [],
                    "months": []
                }
        else:
            logger.warning("⚠️ 'Day' column not found in Shopify data.")
            return {
                "years": [],
                "months": []
            }
    except Exception as e:
        logger.error(f"Error getting customer insights filters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")

@api_router.get(
    "/analytics/customer-insights",
    summary="Get Customer Insights Data",
    description="Returns comprehensive customer insights data with optional year and month filters."
)
async def get_customer_insights(
    years: str = None,
    months: str = None,
    email: str = Depends(get_current_user)
):
    """
    Customer Insights from Shopify data - Multiple visualizations.
    
    Returns aggregated customer data including:
    - New vs Returning customers
    - Channel performance
    - Geographic distribution
    - Traffic sources
    - Customer lifetime value
    - Monthly trends
    - And more...
    """
    try:
        # Load Shopify_customer_df.csv
        csv_path = ROOT_DIR / 'Shopify_customer_df.csv'
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Shopify_customer_df.csv file not found")
        
        df = pd.read_csv(csv_path)
        if df.empty:
            raise HTTPException(status_code=500, detail="Customer Shopify data is empty")
        
        # Convert date columns
        if 'Day' in df.columns:
            try:
                df['Day'] = pd.to_datetime(df['Day'], errors='coerce')
                df['Year'] = df['Day'].dt.year
                df['Month'] = df['Day'].dt.month
                df['MonthName'] = df['Day'].dt.strftime('%B')
                logger.info(f"✅ Date columns processed. Valid dates: {df['Day'].notna().sum()}/{len(df)}")
            except Exception as e:
                logger.warning(f"Error processing date columns: {str(e)}")
                df['Year'] = None
                df['Month'] = None
                df['MonthName'] = None
        else:
            logger.warning("⚠️ 'Day' column not found in Shopify data. Cannot apply date filters.")
            df['Year'] = None
            df['Month'] = None
            df['MonthName'] = None
        
        # Apply filters
        logger.info(f"🔍 Applying filters - years: {years}, months: {months}")
        logger.info(f"📊 Data shape before filtering: {df.shape}")
        logger.info(f"📅 Available years in data: {sorted(df['Year'].dropna().unique().tolist()) if 'Year' in df.columns else 'N/A'}")
        logger.info(f"📅 Available months in data: {sorted(df['Month'].dropna().unique().tolist()) if 'Month' in df.columns else 'N/A'}")
        
        if years:
            try:
                year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
                if year_list:
                    logger.info(f"🔍 Filtering by years: {year_list}")
                    # Filter out NaN values and apply year filter
                    df = df[df['Year'].notna() & df['Year'].isin(year_list)]
                    logger.info(f"📊 Data shape after year filter: {df.shape}")
            except Exception as e:
                logger.error(f"❌ Error filtering by years: {str(e)}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        if months:
            try:
                month_list = [m.strip() for m in months.split(',') if m.strip()]
                if month_list:
                    logger.info(f"🔍 Received month filter values: {month_list}")
                    
                    # Comprehensive month name mapping (handles various formats)
                    month_map = {
                        # Full names
                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                        'September': 9, 'October': 10, 'November': 11, 'December': 12,
                        # Abbreviations
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                        'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9,
                        'Oct': 10, 'Nov': 11, 'Dec': 12,
                        # Case variations
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12,
                    }
                    
                    # Try to map month names to numbers
                    month_numbers = []
                    for m in month_list:
                        # Try exact match first
                        if m in month_map:
                            month_numbers.append(month_map[m])
                        else:
                            # Try case-insensitive match
                            m_lower = m.lower()
                            for key, value in month_map.items():
                                if key.lower() == m_lower:
                                    month_numbers.append(value)
                                    break
                    
                    # Also try matching against MonthName column if it exists (for Shopify data)
                    if 'MonthName' in df.columns:
                        # Get unique month names in the data
                        available_months = df['MonthName'].dropna().unique().tolist()
                        logger.info(f"📅 Available month names in data: {available_months}")
                        
                        # Try to match selected months with available month names
                        for m in month_list:
                            m_lower = m.lower().strip()
                            for avail_month in available_months:
                                if avail_month and str(avail_month).lower().strip() == m_lower:
                                    # Get month number from the matched month name
                                    matching_rows = df[df['MonthName'] == avail_month]
                                    if len(matching_rows) > 0:
                                        month_num = matching_rows['Month'].iloc[0]
                                        if pd.notna(month_num) and int(month_num) not in month_numbers:
                                            month_numbers.append(int(month_num))
                                            logger.info(f"✅ Matched '{m}' to month number {int(month_num)} via MonthName column")
                    
                    # Remove duplicates and None values
                    month_numbers = sorted(list(set([m for m in month_numbers if m is not None])))
                    
                    if month_numbers:
                        logger.info(f"🔍 Filtering by month numbers: {month_numbers}")
                        # Filter out NaN values and apply month filter
                        df_filtered = df[df['Month'].notna() & df['Month'].isin(month_numbers)]
                        if len(df_filtered) > 0:
                            df = df_filtered
                            logger.info(f"📊 Data shape after month filter: {df.shape}")
                        else:
                            # Fallback: try filtering by MonthName directly
                            logger.warning("⚠️ Month number filter returned no results, trying MonthName filter")
                            if 'MonthName' in df.columns:
                                # Create a list of month names that match the selected months
                                matching_month_names = []
                                for m in month_list:
                                    m_lower = m.lower().strip()
                                    for avail_month in df['MonthName'].dropna().unique():
                                        if str(avail_month).lower().strip() == m_lower:
                                            matching_month_names.append(avail_month)
                                
                                if matching_month_names:
                                    df = df[df['MonthName'].isin(matching_month_names)]
                                    logger.info(f"✅ Filtered by MonthName: {matching_month_names}, shape: {df.shape}")
                                else:
                                    logger.warning(f"⚠️ Could not match any month names. Selected: {month_list}")
                    else:
                        logger.warning(f"⚠️ Could not map any month names to numbers. Month list: {month_list}")
                        # Last resort: try direct MonthName matching
                        if 'MonthName' in df.columns:
                            matching_month_names = []
                            for m in month_list:
                                m_lower = m.lower().strip()
                                for avail_month in df['MonthName'].dropna().unique():
                                    if str(avail_month).lower().strip() == m_lower:
                                        matching_month_names.append(avail_month)
                            
                            if matching_month_names:
                                df = df[df['MonthName'].isin(matching_month_names)]
                                logger.info(f"✅ Filtered by MonthName (fallback): {matching_month_names}, shape: {df.shape}")
            except Exception as e:
                logger.error(f"❌ Error filtering by months: {str(e)}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        logger.info(f"📊 Final data shape after all filters: {df.shape}")
        
        if df.empty:
            logger.warning("⚠️ Data is empty after filtering. Returning empty results.")
            return {
                "newVsReturning": [],
                "channelPerformance": [],
                "regionPerformance": [],
                "trafficSource": [],
                "customerLifetimeValue": [],
                "monthlyTrend": [],
                "subscriptionStatus": [],
                "topCustomers": [],
                "platformAnalysis": [],
                "trafficType": [],
                "hourlyPatterns": [],
                "countryDistribution": [],
                "smsSubscription": [],
                "orderReturnAnalysis": [],
                "mediumAnalysis": [],
                "topProducts": [],
                "dayOfWeekAnalysis": [],
                "returnTrend": [],
                "summary": {
                    "totalCustomers": 0,
                    "totalOrders": 0,
                    "totalSales": 0,
                    "avgOrderValue": 0,
                    "newCustomers": 0,
                    "returningCustomers": 0
                }
            }
        
        # Ensure numeric columns
        numeric_cols = ['Net sales', 'Gross sales', 'Total sales', 'Orders', 'Orders (first-time)', 
                       'Orders (returning)', 'Quantity ordered', 'Customer number of orders']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 1. Customer Acquisition vs Retention (New vs Returning)
        new_vs_returning = df.groupby('New or returning customer').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        new_vs_returning.columns = ['type', 'orders', 'sales', 'unique_customers']
        
        # 2. Sales Channel Performance (use Order or return to show order vs return as channels)
        # Since there's no Sales channel column, we'll use Order or return as a proxy
        channel_perf = df.groupby('Order or return').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        channel_perf.columns = ['channel', 'sales', 'orders', 'customers']
        channel_perf = channel_perf.sort_values('sales', ascending=False)
        
        # 3. Geographic Distribution (Top Regions)
        region_perf = df.groupby('Shipping region').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        region_perf.columns = ['region', 'sales', 'orders', 'customers']
        region_perf = region_perf.sort_values('sales', ascending=False).head(10)
        
        # 4. Traffic Source Analysis
        traffic_source = df.groupby('Referring channel').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        traffic_source.columns = ['source', 'sales', 'orders', 'customers']
        traffic_source = traffic_source[traffic_source['source'].notna()].sort_values('sales', ascending=False).head(10)
        
        # 5. Customer Lifetime Value (by number of orders)
        clv_buckets = pd.cut(df['Customer number of orders'], 
                            bins=[0, 1, 3, 5, 10, 20, float('inf')],
                            labels=['1', '2-3', '4-5', '6-10', '11-20', '20+'])
        clv_analysis = df.groupby(clv_buckets).agg({
            'Total sales': 'sum',
            'Customer email': 'nunique',
            'Orders': 'sum'
        }).reset_index()
        clv_analysis.columns = ['order_bucket', 'total_sales', 'unique_customers', 'total_orders']
        clv_analysis['avg_sales_per_customer'] = clv_analysis['total_sales'] / clv_analysis['unique_customers']
        
        # 6. Monthly/Daily Trend - Group by day to show trends within the month
        # Also include previous month data if available
        if 'Day' in df.columns and df['Day'].notna().any():
            # Daily trends within the current month
            try:
                daily_trend = df.groupby('Day').agg({
                    'Total sales': 'sum',
                    'Orders': 'sum',
                    'Customer email': 'nunique',
                    'Orders (first-time)': 'sum',
                    'Orders (returning)': 'sum'
                }).reset_index()
                daily_trend = daily_trend.sort_values('Day')
                daily_trend['Year'] = daily_trend['Day'].dt.year
                daily_trend['Month'] = daily_trend['Day'].dt.month
                daily_trend['MonthName'] = daily_trend['Day'].dt.strftime('%B')
                daily_trend['day_label'] = daily_trend['Day'].dt.strftime('%b %d, %Y')
                daily_trend['month_label'] = daily_trend['MonthName'] + ' ' + daily_trend['Year'].astype(str)
                
                # Monthly aggregation (for months with data)
                # Filter out rows where Year or Month is null
                df_valid_dates = df[(df['Year'].notna()) & (df['Month'].notna())]
                if not df_valid_dates.empty:
                    monthly_trend = df_valid_dates.groupby(['Year', 'Month']).agg({
                        'Total sales': 'sum',
                        'Orders': 'sum',
                        'Customer email': 'nunique',
                        'Orders (first-time)': 'sum',
                        'Orders (returning)': 'sum'
                    }).reset_index()
                else:
                    monthly_trend = pd.DataFrame(columns=['Year', 'Month', 'Total sales', 'Orders', 'Customer email', 'Orders (first-time)', 'Orders (returning)'])
                
                # Add month names
                monthly_trend['MonthName'] = pd.to_datetime(monthly_trend[['Year', 'Month']].assign(Day=1)).dt.strftime('%B')
                monthly_trend = monthly_trend.sort_values(['Year', 'Month'])
                monthly_trend['month_label'] = monthly_trend['MonthName'] + ' ' + monthly_trend['Year'].astype(str)
                
                # If we have previous month data columns, aggregate them for comparison
                if 'Total sales (previous_month)' in df.columns and not df_valid_dates.empty:
                    try:
                        prev_month_data = df_valid_dates.groupby(['Year', 'Month']).agg({
                            'Total sales (previous_month)': 'sum',
                            'Orders (previous_month)': 'sum',
                            'Orders first time (previous_month)': 'sum',
                            'Orders returning (previous_month)': 'sum'
                        }).reset_index()
                        
                        # Calculate previous month year/month
                        prev_month_data['PrevYear'] = prev_month_data['Year']
                        prev_month_data['PrevMonth'] = prev_month_data['Month'] - 1
                        prev_month_data.loc[prev_month_data['PrevMonth'] == 0, 'PrevMonth'] = 12
                        prev_month_data.loc[prev_month_data['PrevMonth'] == 12, 'PrevYear'] = prev_month_data['PrevYear'] - 1
                        prev_month_data['PrevMonthName'] = pd.to_datetime(prev_month_data[['PrevYear', 'PrevMonth']].assign(Day=1)).dt.strftime('%B')
                        prev_month_data['prev_month_label'] = prev_month_data['PrevMonthName'] + ' ' + prev_month_data['PrevYear'].astype(str)
                        
                        # Add previous month data to monthly trend
                        prev_month_rows = []
                        for idx, row in prev_month_data.iterrows():
                            prev_sales = row.get('Total sales (previous_month)', 0)
                            if pd.notna(prev_sales) and prev_sales > 0:
                                prev_month_rows.append({
                                    'Year': int(row['PrevYear']),
                                    'Month': int(row['PrevMonth']),
                                    'MonthName': str(row['PrevMonthName']),
                                    'month_label': str(row['prev_month_label']),
                                    'Total sales': float(prev_sales),
                                    'Orders': float(row.get('Orders (previous_month)', 0) or 0),
                                    'Customer email': 0,  # Not available in prev month data
                                    'Orders (first-time)': float(row.get('Orders first time (previous_month)', 0) or 0),
                                    'Orders (returning)': float(row.get('Orders returning (previous_month)', 0) or 0)
                                })
                        
                        if prev_month_rows:
                            prev_df = pd.DataFrame(prev_month_rows)
                            monthly_trend = pd.concat([monthly_trend, prev_df], ignore_index=True)
                    except Exception as e:
                        logger.warning(f"Error processing previous month data: {str(e)}")
                        # Continue without previous month data
                
                # Sort again after adding previous month data
                monthly_trend = monthly_trend.sort_values(['Year', 'Month']).reset_index(drop=True)
                
                # Use daily trend for more granular view if only one month, otherwise use monthly
                # Check if we have multiple months - if so, use monthly aggregation
                unique_months = monthly_trend[['Year', 'Month']].drop_duplicates()
                if len(unique_months) <= 1:  # If we have only 1 month, show daily trends
                    monthly_trend = daily_trend.copy()
                    monthly_trend['month_label'] = monthly_trend['day_label']  # Use day labels for daily view
                # Otherwise, keep monthly aggregation (which we already have)
            except Exception as e:
                logger.error(f"Error processing daily/monthly trends: {str(e)}")
                # Fallback to simple monthly grouping
                df_valid_dates = df[(df['Year'].notna()) & (df['Month'].notna())]
                if not df_valid_dates.empty:
                    monthly_trend = df_valid_dates.groupby(['Year', 'Month']).agg({
                        'Total sales': 'sum',
                        'Orders': 'sum',
                        'Customer email': 'nunique',
                        'Orders (first-time)': 'sum',
                        'Orders (returning)': 'sum'
                    }).reset_index()
                    monthly_trend['MonthName'] = pd.to_datetime(monthly_trend[['Year', 'Month']].assign(Day=1)).dt.strftime('%B')
                    monthly_trend = monthly_trend.sort_values(['Year', 'Month'])
                    monthly_trend['month_label'] = monthly_trend['MonthName'] + ' ' + monthly_trend['Year'].astype(str)
                else:
                    monthly_trend = pd.DataFrame(columns=['Year', 'Month', 'MonthName', 'month_label', 'Total sales', 'Orders', 'Customer email', 'Orders (first-time)', 'Orders (returning)'])
        else:
            # Fallback to monthly grouping if Day column not available
            df_valid_dates = df[(df['Year'].notna()) & (df['Month'].notna())]
            if not df_valid_dates.empty:
                monthly_trend = df_valid_dates.groupby(['Year', 'Month']).agg({
                    'Total sales': 'sum',
                    'Orders': 'sum',
                    'Customer email': 'nunique',
                    'Orders (first-time)': 'sum',
                    'Orders (returning)': 'sum'
                }).reset_index()
                monthly_trend['MonthName'] = pd.to_datetime(monthly_trend[['Year', 'Month']].assign(Day=1)).dt.strftime('%B')
                monthly_trend = monthly_trend.sort_values(['Year', 'Month'])
                monthly_trend['month_label'] = monthly_trend['MonthName'] + ' ' + monthly_trend['Year'].astype(str)
            else:
                monthly_trend = pd.DataFrame(columns=['Year', 'Month', 'MonthName', 'month_label', 'Total sales', 'Orders', 'Customer email', 'Orders (first-time)', 'Orders (returning)'])
        
        # Rename columns to ensure consistent keys in JSON response
        if not monthly_trend.empty and 'Total sales' in monthly_trend.columns:
            monthly_trend = monthly_trend.rename(columns={
                'Total sales': 'Total_sales',
                'Orders (first-time)': 'Orders_first_time',
                'Orders (returning)': 'Orders_returning',
                'Customer email': 'Customer_email'
            })
        
        # 7. Email Subscription Status
        subscription_status = df.groupby('Customer email subscription status').agg({
            'Customer email': 'nunique',
            'Total sales': 'sum',
            'Orders': 'sum'
        }).reset_index()
        subscription_status.columns = ['status', 'unique_customers', 'sales', 'orders']
        
        # 8. Top Customers by Sales
        top_customers = df.groupby(['Customer email', 'Customer name']).agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer number of orders': 'max'
        }).reset_index()
        top_customers.columns = ['email', 'name', 'total_sales', 'total_orders', 'lifetime_orders']
        top_customers = top_customers.sort_values('total_sales', ascending=False).head(20)
        
        # 9. Platform/Medium Analysis
        platform_analysis = df.groupby('Referring platform').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        platform_analysis.columns = ['platform', 'sales', 'orders', 'customers']
        platform_analysis = platform_analysis[platform_analysis['platform'].notna()].sort_values('sales', ascending=False).head(10)
        
        # 10. Traffic Type Performance
        traffic_type = df.groupby('Traffic type').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        traffic_type.columns = ['type', 'sales', 'orders', 'customers']
        traffic_type = traffic_type[traffic_type['type'].notna()].sort_values('sales', ascending=False)
        
        # 11. Hour of Day Shopping Patterns
        try:
            hourly_patterns = df[df['Hour of day'].notna()].groupby('Hour of day').agg({
                'Total sales': 'sum',
                'Orders': 'sum',
                'Customer email': 'nunique'
            }).reset_index()
            hourly_patterns.columns = ['hour', 'sales', 'orders', 'customers']
            hourly_patterns = hourly_patterns.sort_values('hour')
            hourly_patterns['hour'] = hourly_patterns['hour'].astype(int)
        except Exception as e:
            logger.warning(f"Error processing hourly patterns: {str(e)}")
            hourly_patterns = pd.DataFrame(columns=['hour', 'sales', 'orders', 'customers'])
        
        # 12. Country Distribution
        country_dist = df.groupby('Shipping country').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        country_dist.columns = ['country', 'sales', 'orders', 'customers']
        country_dist = country_dist.sort_values('sales', ascending=False)
        
        # 13. SMS Subscription Status
        sms_subscription = df[df['Customer SMS subscription status'].notna()].groupby('Customer SMS subscription status').agg({
            'Customer email': 'nunique',
            'Total sales': 'sum',
            'Orders': 'sum'
        }).reset_index()
        sms_subscription.columns = ['status', 'unique_customers', 'sales', 'orders']
        
        # 14. Order vs Return Analysis
        order_return_analysis = df.groupby('Order or return').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Net returns': 'sum',
            'Total returns': 'sum'
        }).reset_index()
        order_return_analysis.columns = ['type', 'total_sales', 'orders', 'net_returns', 'total_returns']
        
        # 15. Referring Medium Analysis
        medium_analysis = df[df['Referring medium'].notna()].groupby('Referring medium').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customer email': 'nunique'
        }).reset_index()
        medium_analysis.columns = ['medium', 'sales', 'orders', 'customers']
        medium_analysis = medium_analysis.sort_values('sales', ascending=False)
        
        # 16. Top Products by Sales
        top_products = df[df['Product variant SKU'].notna()].groupby('Product variant SKU').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Quantity ordered': 'sum'
        }).reset_index()
        top_products.columns = ['sku', 'sales', 'orders', 'quantity']
        top_products = top_products.sort_values('sales', ascending=False).head(15)
        
        # 17. Day of Week Analysis
        if 'Day' in df.columns:
            try:
                df['DayOfWeek'] = pd.to_datetime(df['Day'], errors='coerce').dt.day_name()
                day_of_week = df[df['DayOfWeek'].notna()].groupby('DayOfWeek').agg({
                    'Total sales': 'sum',
                    'Orders': 'sum',
                    'Customer email': 'nunique'
                }).reset_index()
                day_of_week.columns = ['day', 'sales', 'orders', 'customers']
                # Order by day of week
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_of_week['day_order'] = day_of_week['day'].map({day: i for i, day in enumerate(day_order)})
                day_of_week = day_of_week[day_of_week['day_order'].notna()].sort_values('day_order').drop('day_order', axis=1)
            except Exception as e:
                logger.warning(f"Error processing day of week analysis: {str(e)}")
                day_of_week = pd.DataFrame(columns=['day', 'sales', 'orders', 'customers'])
        else:
            day_of_week = pd.DataFrame(columns=['day', 'sales', 'orders', 'customers'])
        
        # 18. Return Rate Trend (monthly)
        if 'Day' in df.columns:
            try:
                return_data = df[df['Order or return'] == 'return']
                if not return_data.empty:
                    return_trend = return_data.groupby(['Year', 'Month']).agg({
                        'Total returns': 'sum',
                        'Orders': 'sum'
                    }).reset_index()
                    monthly_sales = df.groupby(['Year', 'Month'])['Total sales'].sum().reset_index()
                    return_trend = return_trend.merge(monthly_sales, on=['Year', 'Month'], how='left', suffixes=('', '_total'))
                    return_trend['MonthName'] = pd.to_datetime(return_trend[['Year', 'Month']].assign(Day=1)).dt.strftime('%B')
                    return_trend = return_trend.sort_values(['Year', 'Month'])
                    return_trend['month_label'] = return_trend['MonthName'] + ' ' + return_trend['Year'].astype(str)
                    return_trend['return_rate'] = (return_trend['Total returns'].abs() / return_trend['Total sales_total'].replace(0, 1) * 100).fillna(0)
                    return_trend = return_trend.drop('Total sales_total', axis=1)
                else:
                    return_trend = pd.DataFrame(columns=['Year', 'Month', 'MonthName', 'month_label', 'Total returns', 'Orders', 'return_rate'])
            except Exception as e:
                logger.warning(f"Error processing return trend: {str(e)}")
                return_trend = pd.DataFrame(columns=['Year', 'Month', 'MonthName', 'month_label', 'Total returns', 'Orders', 'return_rate'])
        else:
            return_trend = pd.DataFrame(columns=['Year', 'Month', 'MonthName', 'month_label', 'Total returns', 'Orders', 'return_rate'])
        
        # Ensure all dataframes are not empty - convert to dict with empty list fallback
        def safe_to_dict(df, default=[]):
            if df is None or df.empty:
                return default
            return df.to_dict('records')
        
        return {
            "newVsReturning": safe_to_dict(new_vs_returning),
            "channelPerformance": safe_to_dict(channel_perf),
            "regionPerformance": safe_to_dict(region_perf),
            "trafficSource": safe_to_dict(traffic_source),
            "customerLifetimeValue": safe_to_dict(clv_analysis),
            "monthlyTrend": safe_to_dict(monthly_trend),
            "subscriptionStatus": safe_to_dict(subscription_status),
            "topCustomers": safe_to_dict(top_customers),
            "platformAnalysis": safe_to_dict(platform_analysis),
            "trafficType": safe_to_dict(traffic_type),
            "hourlyPatterns": safe_to_dict(hourly_patterns),
            "countryDistribution": safe_to_dict(country_dist),
            "smsSubscription": safe_to_dict(sms_subscription),
            "orderReturnAnalysis": safe_to_dict(order_return_analysis),
            "mediumAnalysis": safe_to_dict(medium_analysis),
            "topProducts": safe_to_dict(top_products),
            "dayOfWeekAnalysis": safe_to_dict(day_of_week),
            "returnTrend": safe_to_dict(return_trend),
            "summary": {
                "totalCustomers": int(df['Customer email'].nunique()),
                "totalOrders": int(df['Orders'].sum()),
                "totalSales": float(df['Total sales'].sum()),
                "avgOrderValue": float(df['Total sales'].sum() / df['Orders'].sum() if df['Orders'].sum() > 0 else 0),
                "newCustomers": int((df['New or returning customer'] == 'New').sum()),
                "returningCustomers": int((df['New or returning customer'] == 'Returning').sum())
            }
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="customer_shopify.csv file not found")
    except Exception as e:
        logger.error(f"Error processing customer insights: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing customer insights: {str(e)}")

# Test endpoint to verify route registration (no auth required for testing)
@api_router.get("/analytics/customer-insights/chat/health")
async def customer_insights_chat_health():
    """Health check for customer insights chat endpoint"""
    return {"status": "ok", "message": "Customer insights chat route is registered", "path": "/api/analytics/customer-insights/chat"}

# Simple test POST endpoint (no auth, no dependencies) to verify POST routes work
@api_router.post("/analytics/customer-insights/chat/test-simple")
async def customer_insights_chat_test_simple(request: CustomerInsightsChatRequest):
    """Simple test endpoint without auth to verify POST route registration"""
    logger.info("🔵 TEST-SIMPLE endpoint called!")
    return {"status": "ok", "message": "POST route is working", "received": request.message[:50]}

# Customer Insights Chat endpoint - Uses FastAPI module
@api_router.post("/analytics/customer-insights/chat", response_model=CustomerInsightsChatResponse, name="customer_insights_chat")
async def customer_insights_chat(request: CustomerInsightsChatRequest):
    """AI Chat Assistant for Customer Deep Intelligence insights using Shopify customer data"""
    logger.info(f"🔵🔵🔵 Customer insights chat endpoint CALLED")
    logger.info(f"🔵🔵🔵 Request received: {request.message[:100] if request.message else 'None'}")
    logger.info(f"🔵🔵🔵 Full request path: /api/analytics/customer-insights/chat")
    
    try:
        # Import the FastAPI functions
        from customer_insights_fastapi import process_customer_insights_chat
        
        # Process the chat request using the FastAPI functions
        result = process_customer_insights_chat(
            message=request.message or "",
            context=request.context or {},
            conversation_history=request.conversation_history or [],
            chart_title=request.chart_title
        )
        
        # Convert result to response model
        return CustomerInsightsChatResponse(
            response=result.get("response", "I apologize, but I couldn't process your request."),
            timestamp=result.get("timestamp", datetime.now().strftime("%I:%M %p IST on %B %d, %Y")),
            context=result.get("context", ""),
            data=result.get("data", {})
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="shopify_data.csv file not found")
    except ImportError as e:
        logger.error(f"Failed to import customer_insights_fastapi: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load customer insights FastAPI module: {str(e)}")
    except Exception as e:
        logger.error(f"Customer insights chat error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing customer insights chat: {str(e)}")

# ============================================================================
# Customer Deep Intelligence View Insights API
# Enhanced endpoint for view insights modal with advanced data processing
# ============================================================================

class ShopifyDataProcessor:
    """Data processor for Shopify customer data - for view insights"""
    def __init__(self, df):
        self.df = df.copy()
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess the Shopify data"""
        # Convert date column
        if 'Day' in self.df.columns:
            self.df['Day'] = pd.to_datetime(self.df['Day'], errors='coerce')
            
            # Extract date components
            self.df['Date'] = self.df['Day'].dt.date
            self.df['Month'] = self.df['Day'].dt.month_name()
            self.df['Month_Num'] = self.df['Day'].dt.month
            self.df['Year'] = self.df['Day'].dt.year
            self.df['YearMonth'] = self.df['Day'].dt.to_period('M')
            self.df['DayOfWeek'] = self.df['Day'].dt.day_name()
            self.df['Week'] = self.df['Day'].dt.isocalendar().week
        
        # Ensure numeric columns
        numeric_cols = ['Net sales', 'Gross sales', 'Total sales', 'Orders', 
                       'Orders (first-time)', 'Orders (returning)', 
                       'Quantity ordered', 'Customer number of orders', 'Customers']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Calculate additional metrics
        if 'Orders' in self.df.columns and 'Customers' in self.df.columns:
            self.df['Conversion_Rate'] = self.df['Orders'] / self.df['Customers']
            self.df['Conversion_Rate'] = self.df['Conversion_Rate'].fillna(0)
        
        if 'Total sales' in self.df.columns and 'Orders' in self.df.columns:
            self.df['Avg_Order_Value'] = self.df['Total sales'] / self.df['Orders']
            self.df['Avg_Order_Value'] = self.df['Avg_Order_Value'].fillna(0)
    
    def get_filtered_data(self, start_date=None, end_date=None, channel=None, 
                          customer_type=None, month=None, year=None, country=None):
        """Filter data based on user selections"""
        filtered_df = self.df.copy()
        
        # Date filter
        if start_date and end_date and 'Date' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) & 
                (filtered_df['Date'] <= end_date)
            ]
        
        # Month filter
        if month and month != 'All' and 'Month' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Month'] == month]
        
        # Year filter
        if year and year != 'All' and 'Year' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Year'] == int(year)]
        
        # Channel filter
        if channel and channel != 'All' and 'Referring channel' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Referring channel'] == channel]
        
        # Customer type filter
        if customer_type and customer_type != 'All' and 'New or returning customer' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['New or returning customer'] == customer_type]
        
        # Country filter
        if country and country != 'All' and 'Shipping country' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Shipping country'] == country]
        
        return filtered_df
    
    def get_summary_stats(self, filtered_df=None):
        """Get overall summary statistics"""
        if filtered_df is None:
            filtered_df = self.df
        
        total_orders = filtered_df['Orders'].sum() if 'Orders' in filtered_df.columns else 0
        total_sales = filtered_df['Total sales'].sum() if 'Total sales' in filtered_df.columns else 0
        total_customers = filtered_df['Customers'].sum() if 'Customers' in filtered_df.columns else 0
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        returning_rate = 0
        if 'Returning customer rate' in filtered_df.columns:
            returning_rate = filtered_df['Returning customer rate'].mean() * 100
        elif 'New or returning customer' in filtered_df.columns:
            returning_count = (filtered_df['New or returning customer'] == 'Returning').sum()
            total_cust_count = len(filtered_df)
            returning_rate = (returning_count / total_cust_count * 100) if total_cust_count > 0 else 0
        
        return {
            'total_orders': int(total_orders),
            'total_sales': round(total_sales, 2),
            'total_customers': int(total_customers),
            'avg_order_value': round(avg_order_value, 2),
            'returning_customer_rate': round(returning_rate, 2),
            'data_points': len(filtered_df)
        }
    
    def get_monthly_sales(self, filtered_df=None):
        """Get sales by month"""
        if filtered_df is None:
            filtered_df = self.df
        
        if 'Year' not in filtered_df.columns or 'Month' not in filtered_df.columns:
            return pd.DataFrame()
        
        monthly_sales = filtered_df.groupby(['Year', 'Month', 'Month_Num']).agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customers': 'sum',
        }).reset_index().sort_values(['Year', 'Month_Num'])
        
        return monthly_sales
    
    def get_advanced_metrics(self, filtered_df=None):
        """Calculate advanced business metrics"""
        if filtered_df is None:
            filtered_df = self.df
        
        # Customer Lifetime Value
        if 'Customer email' in filtered_df.columns and 'Total sales' in filtered_df.columns:
            customer_sales = filtered_df.groupby('Customer email')['Total sales'].sum()
            clv = customer_sales.mean() if len(customer_sales) > 0 else 0
        else:
            clv = 0
        
        # Customer Acquisition Cost (simulated)
        total_sales = filtered_df['Total sales'].sum() if 'Total sales' in filtered_df.columns else 0
        total_customers = filtered_df['Customers'].sum() if 'Customers' in filtered_df.columns else 0
        total_marketing_spend = total_sales * 0.2  # 20% of sales
        cac = total_marketing_spend / total_customers if total_customers > 0 else 0
        
        # Retention Rate
        if 'New or returning customer' in filtered_df.columns and 'Customers' in filtered_df.columns:
            returning_customers = filtered_df[filtered_df['New or returning customer'] == 'Returning']['Customers'].sum()
            retention_rate = (returning_customers / total_customers) * 100 if total_customers > 0 else 0
        else:
            retention_rate = 0
        
        # Churn Rate
        churn_rate = 100 - retention_rate
        
        # Repeat Purchase Rate
        if 'New or returning customer' in filtered_df.columns and 'Customer email' in filtered_df.columns:
            repeat_customers = filtered_df[filtered_df['New or returning customer'] == 'Returning']['Customer email'].nunique()
            total_unique_customers = filtered_df['Customer email'].nunique()
            repeat_rate = (repeat_customers / total_unique_customers) * 100 if total_unique_customers > 0 else 0
        else:
            repeat_rate = 0
        
        return {
            'customer_lifetime_value': round(clv, 2),
            'customer_acquisition_cost': round(cac, 2),
            'retention_rate': round(retention_rate, 2),
            'churn_rate': round(churn_rate, 2),
            'repeat_purchase_rate': round(repeat_rate, 2),
            'clv_to_cac_ratio': round(clv/cac, 2) if cac > 0 else 0
        }
    
    def get_channel_performance(self, filtered_df=None):
        """Get performance by referring channel"""
        if filtered_df is None:
            filtered_df = self.df
        
        if 'Referring channel' not in filtered_df.columns:
            return pd.DataFrame()
        
        channel_perf = filtered_df.groupby('Referring channel').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Customers': 'sum'
        }).reset_index()
        
        if 'Customers' in channel_perf.columns:
            channel_perf['Conversion_Rate'] = (channel_perf['Orders'] / channel_perf['Customers']).fillna(0)
        
        return channel_perf
    
    def get_geographic_insights(self, filtered_df=None):
        """Get insights by shipping country"""
        if filtered_df is None:
            filtered_df = self.df
        
        if 'Shipping country' not in filtered_df.columns:
            return pd.DataFrame()
        
        geo_insights = filtered_df.groupby('Shipping country').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Customers': 'sum'
        }).reset_index()
        
        return geo_insights

# Global cache for customer data processor
_customer_processor_cache = None

def get_customer_processor():
    """Get or create customer data processor with caching"""
    global _customer_processor_cache
    if _customer_processor_cache is not None:
        return _customer_processor_cache
    
    csv_path = ROOT_DIR / 'Shopify_customer_df.csv'
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Shopify_customer_df.csv file not found")
    
    df = pd.read_csv(csv_path)
    if df.empty:
        raise HTTPException(status_code=500, detail="Customer Shopify data is empty")
    
    processor = ShopifyDataProcessor(df)
    _customer_processor_cache = processor
    return processor

def generate_customer_data_context(processor, query, filters=None):
    """Generate data context for AI prompt"""
    # Apply filters if provided
    filtered_df = processor.df.copy()
    
    if filters:
        year = filters.get('year') or (filters.get('selectedYears', [None])[0] if filters.get('selectedYears') else None)
        month = filters.get('month') or (filters.get('selectedMonths', [None])[0] if filters.get('selectedMonths') else None)
        channel = filters.get('channel') or (filters.get('selectedChannels', [None])[0] if filters.get('selectedChannels') else None)
        customer_type = filters.get('customer_type') or (filters.get('selectedCustomerTypes', [None])[0] if filters.get('selectedCustomerTypes') else None)
        country = filters.get('country') or (filters.get('selectedCountries', [None])[0] if filters.get('selectedCountries') else None)
        
        filtered_df = processor.get_filtered_data(
            year=year,
            month=month,
            channel=channel,
            customer_type=customer_type,
            country=country
        )
    
    # Get summary statistics
    summary = processor.get_summary_stats(filtered_df)
    advanced = processor.get_advanced_metrics(filtered_df)
    monthly_data = processor.get_monthly_sales(filtered_df)
    channels = processor.get_channel_performance(filtered_df)
    geography = processor.get_geographic_insights(filtered_df)
    
    # Build context string
    context = f"""
CUSTOMER DATA OVERVIEW:
- Total Customers: {summary['total_customers']:,}
- Total Orders: {summary['total_orders']:,}
- Total Sales: ${summary['total_sales']:,.2f}
- Average Order Value: ${summary['avg_order_value']:,.2f}
- Returning Customer Rate: {summary['returning_customer_rate']:.1f}%

ADVANCED METRICS:
- Customer Lifetime Value: ${advanced['customer_lifetime_value']:,.2f}
- Customer Acquisition Cost: ${advanced['customer_acquisition_cost']:,.2f}
- Retention Rate: {advanced['retention_rate']:.1f}%
- Repeat Purchase Rate: {advanced['repeat_purchase_rate']:.1f}%
- CLV to CAC Ratio: {advanced['clv_to_cac_ratio']:.1f}

MONTHLY SALES DATA:
{monthly_data.to_string(index=False) if not monthly_data.empty else 'No monthly data available'}

CHANNEL PERFORMANCE:
{channels.to_string(index=False) if not channels.empty else 'No channel data available'}

GEOGRAPHIC DISTRIBUTION:
{geography.to_string(index=False) if not geography.empty else 'No geographic data available'}

You can answer questions about:
- Customer behavior and patterns
- Sales channel performance
- Geographic distribution
- Customer lifetime value
- New vs returning customer analysis
- Traffic sources and platforms
- Time-based shopping patterns (hourly, daily, monthly)
- Product performance
- Return rates and trends
"""
    
    return context, summary, advanced, monthly_data, channels, geography

# Customer Deep Intelligence View Insights endpoint
@api_router.post(
    "/analytics/customer-insights/view-insights/chat", 
    response_model=CustomerInsightsChatResponse,
    summary="Customer Deep Intelligence View Insights Chat",
    description="""
    AI-powered chatbot for Customer Deep Intelligence view insights modal.
    
    This endpoint processes natural language questions about Shopify customer data and returns AI-generated insights.
    
    **Features:**
    - Natural language query processing
    - Context-aware responses using conversation history
    - Filter support (year, month, channel, customer type, country)
    - Chart-specific context integration
    
    **Example Questions:**
    - "What is the total gross sales?"
    - "What are the top performing channels?"
    - "Show me sales trends by month"
    - "Which countries have the highest sales?"
    """
)
async def customer_view_insights_chat(request: CustomerInsightsChatRequest, email: str = Depends(get_current_user)):
    """
    Enhanced AI Chat Assistant for Customer Deep Intelligence view insights modal using FastAPI.
    
    Processes user questions about Shopify customer data and returns AI-generated insights with data context.
    """
    logger.info(f"Customer view insights chat endpoint called by {email}")
    logger.info(f"Request message: {request.message[:100] if request.message else 'None'}")
    
    try:
        # Import the FastAPI functions
        from customer_insights_fastapi import process_customer_insights_chat
        
        # Process the chat request using the FastAPI functions
        result = process_customer_insights_chat(
            message=request.message or "",
            context=request.context or {},
            conversation_history=request.conversation_history or [],
            chart_title=request.chart_title
        )
        
        # Convert result to response model - ensure all data is JSON serializable
        response_data = CustomerInsightsChatResponse(
            response=result.get("response", "I apologize, but I couldn't process your request."),
            timestamp=result.get("timestamp", datetime.now().strftime("%I:%M %p IST on %B %d, %Y")),
            context=result.get("context", ""),
            data=result.get("data", {})
        )
        
        return response_data
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail="shopify_data.csv file not found")
    except ImportError as e:
        logger.error(f"Failed to import customer_insights_fastapi: {str(e)}")
        import traceback
        logger.error(f"Import traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to load customer insights FastAPI module: {str(e)}")
    except Exception as e:
        logger.error(f"Customer view insights chat error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing customer view insights chat: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Add a catch-all exception handler to see what's happening
from starlette.requests import Request as StarletteRequest

@app.exception_handler(404)
async def not_found_handler(request: StarletteRequest, exc):
    logger.error(f"❌❌❌ 404 ERROR: {request.method} {request.url.path}")
    logger.error(f"❌❌❌ Query params: {dict(request.query_params)}")
    logger.error(f"❌❌❌ Full URL: {request.url}")
    logger.error(f"❌❌❌ Headers: {dict(request.headers)}")
    # Log available POST routes
    post_routes = [r.path for r in app.routes if hasattr(r, 'path') and hasattr(r, 'methods') and 'POST' in r.methods]
    logger.error(f"❌❌❌ Available POST routes: {post_routes}")
    # Log available GET routes
    get_routes = [r.path for r in app.routes if hasattr(r, 'path') and hasattr(r, 'methods') and 'GET' in r.methods]
    root_cause_routes = [r for r in get_routes + post_routes if 'root-cause' in r]
    logger.error(f"❌❌❌ Root cause routes: {root_cause_routes}")
    # Log all routes with their methods
    all_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            all_routes.append(f"{list(route.methods)} {route.path}")
    logger.error(f"❌❌❌ ALL ROUTES: {all_routes[:20]}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"Not Found: {request.method} {request.url.path}"}
    )

# Log customer insights chat route registration and verify it's accessible
logger.info("Registering customer insights chat route: POST /api/analytics/customer-insights/chat")
# Verify the route is actually in the app
main_route_found = False
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        if '/analytics/customer-insights/chat' in route.path and 'POST' in route.methods:
            logger.info(f"✅ Verified route in app: {list(route.methods)} {route.path}")
            if route.path == '/api/analytics/customer-insights/chat':
                main_route_found = True
if not main_route_found:
    logger.error("❌ Main route /api/analytics/customer-insights/chat NOT found in app routes after include_router!")
    logger.error(f"Available POST routes with 'customer-insights': {[f'{list(r.methods)} {r.path}' for r in app.routes if hasattr(r, 'path') and hasattr(r, 'methods') and 'POST' in r.methods and 'customer-insights' in r.path]}")

# Run locally with: python server.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )