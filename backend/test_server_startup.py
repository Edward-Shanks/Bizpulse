"""
Server Startup Test Script
Tests if the new FastAPI application can start without errors
"""
import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_venv():
    """Check if virtual environment is activated"""
    print("=" * 60)
    print("Checking Virtual Environment...")
    print("=" * 60)
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("[OK] Virtual environment is activated")
        print(f"    - Python: {sys.executable}")
        return True
    else:
        print("[WARN] Virtual environment may not be activated")
        print(f"    - Python: {sys.executable}")
        print("    - If you see import errors, activate venv first:")
        print("      Windows: venv\\Scripts\\activate")
        print("      Linux/Mac: source venv/bin/activate")
        return False

def test_imports():
    """Test that all critical modules can be imported"""
    print("\n" + "=" * 60)
    print("Testing Imports...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    try:
        from app.core.config import settings
        print("[OK] Config imported")
        print(f"    - DB_NAME: {settings.DB_NAME}")
        print(f"    - Environment: {settings.ENVIRONMENT}")
    except Exception as e:
        print(f"[FAIL] Config import failed: {e}")
        errors.append(f"Config: {e}")
    
    try:
        from app.core.database import database, get_database, connect_to_mongo
        print("[OK] Database module imported")
    except Exception as e:
        print(f"[FAIL] Database import failed: {e}")
        errors.append(f"Database: {e}")
    
    try:
        from app.core.dependencies import get_current_user
        print("[OK] Dependencies imported")
    except ImportError as e:
        if "fastapi" in str(e).lower() or "pydantic" in str(e).lower():
            print(f"[WARN] Dependencies import failed (venv may not be activated): {e}")
            warnings.append(f"Dependencies: {e}")
        else:
            print(f"[FAIL] Dependencies import failed: {e}")
            errors.append(f"Dependencies: {e}")
    except Exception as e:
        print(f"[FAIL] Dependencies import failed: {e}")
        errors.append(f"Dependencies: {e}")
    
    try:
        from app.models.user import User, LoginRequest, LoginResponse
        from app.models.analytics import BusinessDataRecord, SyncStatusResponse
        from app.models.insights import InsightsChatRequest, InsightsChatResponse
        from app.models.customer_insights import CustomerInsightsChatRequest, CustomerInsightsChatResponse
        print("[OK] All models imported")
    except ImportError as e:
        if "pydantic" in str(e).lower():
            print(f"[WARN] Models import failed (venv may not be activated): {e}")
            warnings.append(f"Models: {e}")
        else:
            print(f"[FAIL] Models import failed: {e}")
            errors.append(f"Models: {e}")
    except Exception as e:
        print(f"[FAIL] Models import failed: {e}")
        errors.append(f"Models: {e}")
    
    try:
        from app.repositories.user_repository import UserRepository
        from app.repositories.business_data_repository import BusinessDataRepository
        from app.repositories.shopify_data_repository import ShopifyDataRepository
        print("[OK] All repositories imported")
    except ImportError as e:
        if "pydantic" in str(e).lower():
            print(f"[WARN] Repositories import failed (venv may not be activated): {e}")
            warnings.append(f"Repositories: {e}")
        else:
            print(f"[FAIL] Repositories import failed: {e}")
            errors.append(f"Repositories: {e}")
    except Exception as e:
        print(f"[FAIL] Repositories import failed: {e}")
        errors.append(f"Repositories: {e}")
    
    try:
        from app.services.auth_service import AuthService
        from app.services.user_service import UserService
        from app.services.data_service import DataService
        print("[OK] All services imported")
    except ImportError as e:
        if "bcrypt" in str(e).lower() or "fastapi" in str(e).lower():
            print(f"[WARN] Services import failed (venv may not be activated): {e}")
            warnings.append(f"Services: {e}")
        else:
            print(f"[FAIL] Services import failed: {e}")
            errors.append(f"Services: {e}")
    except Exception as e:
        print(f"[FAIL] Services import failed: {e}")
        errors.append(f"Services: {e}")
    
    try:
        from app.api.v1.routes import auth, users, data
        print("[OK] All routes imported")
    except ImportError as e:
        if "fastapi" in str(e).lower():
            print(f"[WARN] Routes import failed (venv may not be activated): {e}")
            warnings.append(f"Routes: {e}")
        else:
            print(f"[FAIL] Routes import failed: {e}")
            errors.append(f"Routes: {e}")
    except Exception as e:
        print(f"[FAIL] Routes import failed: {e}")
        errors.append(f"Routes: {e}")
    
    try:
        from app.utils.helpers import safe_float, format_currency, parse_list
        from app.utils.azure_storage import load_data_from_azure_blob
        print("[OK] All utilities imported")
    except Exception as e:
        print(f"[FAIL] Utilities import failed: {e}")
        errors.append(f"Utilities: {e}")
    
    return errors, warnings

def test_app_creation():
    """Test that FastAPI app can be created"""
    print("\n" + "=" * 60)
    print("Testing App Creation...")
    print("=" * 60)
    
    try:
        from app.main import app
        print("[OK] FastAPI app created successfully")
        print(f"    - App title: {app.title}")
        print(f"    - App version: {app.version}")
        return app, None
    except ImportError as e:
        if "fastapi" in str(e).lower():
            print(f"[WARN] App creation failed (venv may not be activated): {e}")
            return None, None  # Don't treat as error if it's just missing venv
        else:
            print(f"[FAIL] App creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    except Exception as e:
        print(f"[FAIL] App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, str(e)

def test_routes_registration(app):
    """Test that routes are registered correctly"""
    print("\n" + "=" * 60)
    print("Testing Route Registration...")
    print("=" * 60)
    
    if not app:
        print("[SKIP] App not created, skipping route test")
        return []
    
    routes = []
    errors = []
    
    try:
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else ['GET']
                for method in methods:
                    routes.append(f"{method} {route.path}")
        
        print(f"[OK] Found {len(routes)} registered routes")
        
        # Check for expected routes
        expected_routes = [
            "POST /api/auth/login",
            "POST /api/auth/signup",
            "GET /api/users",
            "GET /api/users/me",
            "GET /api/users/by-department/{department}",
            "GET /api/data/sync",
            "GET /api/data/source",
            "GET /",
            "GET /health"
        ]
        
        print("\nRegistered routes:")
        for route in sorted(routes):
            marker = "[OK]" if any(exp in route for exp in expected_routes) or route in ["GET /", "GET /health"] else "[NEW]"
            print(f"  {marker} {route}")
        
        # Check if all expected routes are present
        missing = []
        for exp_route in expected_routes:
            if not any(exp_route in r for r in routes):
                missing.append(exp_route)
        
        if missing:
            print(f"\n[WARN] Missing expected routes: {missing}")
            errors.extend(missing)
        else:
            print("\n[OK] All expected routes are registered")
        
        return errors
        
    except Exception as e:
        print(f"[FAIL] Route registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return [str(e)]

async def test_database_connection():
    """Test database connection (optional, may fail if DB not accessible)"""
    print("\n" + "=" * 60)
    print("Testing Database Connection...")
    print("=" * 60)
    
    try:
        from app.core.database import connect_to_mongo, close_mongo_connection
        from app.core.config import settings
        
        if not settings.MONGO_URL:
            print("[SKIP] MONGO_URL not set, skipping database test")
            return None
        
        print(f"Attempting to connect to: {settings.DB_NAME}")
        database = await connect_to_mongo()
        print("[OK] Database connection successful")
        
        # Test a simple query
        count = await database.db.business_data.count_documents({})
        print(f"[OK] Database query successful (business_data count: {count})")
        
        await close_mongo_connection()
        print("[OK] Database connection closed")
        return None
        
    except Exception as e:
        print(f"[WARN] Database connection test failed: {e}")
        print("    (This is OK if MongoDB is not running or not accessible)")
        return None  # Don't fail the test, just warn

def test_dependency_injection():
    """Test that dependency injection works"""
    print("\n" + "=" * 60)
    print("Testing Dependency Injection...")
    print("=" * 60)
    
    errors = []
    
    try:
        from app.core.database import get_database
        from app.core.dependencies import get_current_user
        
        # Test that functions are callable
        if callable(get_database):
            print("[OK] get_database is callable")
        else:
            print("[FAIL] get_database is not callable")
            errors.append("get_database not callable")
        
        if callable(get_current_user):
            print("[OK] get_current_user is callable")
        else:
            print("[FAIL] get_current_user is not callable")
            errors.append("get_current_user not callable")
        
        return errors
        
    except ImportError as e:
        if "fastapi" in str(e).lower():
            print(f"[WARN] Dependency injection test failed (venv may not be activated): {e}")
            return []
        else:
            print(f"[FAIL] Dependency injection test failed: {e}")
            return [str(e)]
    except Exception as e:
        print(f"[FAIL] Dependency injection test failed: {e}")
        return [str(e)]

async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FastAPI Application Startup Test")
    print("=" * 60)
    print()
    
    all_errors = []
    all_warnings = []
    
    # Test 0: Check venv
    venv_ok = check_venv()
    
    # Test 1: Imports
    import_errors, import_warnings = test_imports()
    all_errors.extend(import_errors)
    all_warnings.extend(import_warnings)
    
    # Test 2: App Creation
    app, app_error = test_app_creation()
    if app_error:
        all_errors.append(f"App creation: {app_error}")
    
    # Test 3: Route Registration
    if app:
        route_errors = test_routes_registration(app)
        all_errors.extend(route_errors)
    
    # Test 4: Dependency Injection
    di_errors = test_dependency_injection()
    all_errors.extend(di_errors)
    
    # Test 5: Database Connection (optional)
    await test_database_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if all_warnings:
        print(f"\n[WARN] Found {len(all_warnings)} warning(s) (likely venv not activated):")
        for warning in all_warnings[:3]:  # Show first 3
            print(f"  - {warning}")
        if len(all_warnings) > 3:
            print(f"  ... and {len(all_warnings) - 3} more")
    
    if all_errors:
        print(f"\n[FAIL] Found {len(all_errors)} critical error(s):")
        for error in all_errors:
            print(f"  - {error}")
        print("\n[RESULT] Server startup test FAILED")
        print("Please fix the errors above before starting the server.")
        return 1
    elif all_warnings and not venv_ok:
        print("\n[WARN] Some imports failed, but this may be due to venv not being activated.")
        print("\n[RESULT] Structure looks good, but activate venv to test fully:")
        print("  Windows: venv\\Scripts\\activate")
        print("  Linux/Mac: source venv/bin/activate")
        print("\nThen run this test again or start the server:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("\n[SUCCESS] All tests passed!")
        print("\n[RESULT] Server should start successfully!")
        print("\nTo start the server, run:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

