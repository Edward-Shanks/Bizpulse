"""
Test script for new backend architecture
Tests imports and basic structure
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test core imports
        from app.core.config import settings
        print("[OK] Config imported")
        
        from app.core.database import get_database, connect_to_mongo
        print("[OK] Database imported")
        
        from app.core.dependencies import get_current_user
        print("[OK] Dependencies imported")
        
        # Test model imports
        from app.models.user import User, LoginRequest, LoginResponse
        print("[OK] User models imported")
        
        from app.models.analytics import BusinessDataRecord, SyncStatusResponse
        print("[OK] Analytics models imported")
        
        from app.models.insights import InsightsChatRequest, InsightsChatResponse
        print("[OK] Insights models imported")
        
        from app.models.customer_insights import CustomerInsightsChatRequest, CustomerInsightsChatResponse
        print("[OK] Customer Insights models imported")
        
        from app.models.kanban import StrategicRecommendation, GoalRequest, GoalResponse
        print("[OK] Kanban models imported")
        
        from app.models.root_cause import RootCauseIssue, RootCauseAnalysisResponse
        print("[OK] Root Cause models imported")
        
        from app.models.action_items import ActionItem, ActionItemsResponse
        print("[OK] Action Items models imported")
        
        # Test repository imports
        from app.repositories.user_repository import UserRepository
        print("[OK] User repository imported")
        
        from app.repositories.business_data_repository import BusinessDataRepository
        print("[OK] Business data repository imported")
        
        from app.repositories.shopify_data_repository import ShopifyDataRepository
        print("[OK] Shopify data repository imported")
        
        # Test service imports
        from app.services.auth_service import AuthService
        print("[OK] Auth service imported")
        
        from app.services.user_service import UserService
        print("[OK] User service imported")
        
        from app.services.data_service import DataService
        print("[OK] Data service imported")
        
        # Test route imports
        from app.api.v1.routes import auth, users, data
        print("[OK] Routes imported")
        
        # Test utils
        from app.utils.helpers import safe_float, format_currency, parse_list
        print("[OK] Helpers imported")
        
        from app.utils.azure_storage import load_data_from_azure_blob
        print("[OK] Azure storage imported")
        
        print("\n[OK] All imports successful!")
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structure():
    """Test that the structure is correct"""
    print("\nTesting structure...")
    
    required_files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/core/dependencies.py",
        "app/models/__init__.py",
        "app/models/user.py",
        "app/models/analytics.py",
        "app/models/insights.py",
        "app/models/customer_insights.py",
        "app/models/kanban.py",
        "app/models/root_cause.py",
        "app/models/action_items.py",
        "app/repositories/__init__.py",
        "app/repositories/user_repository.py",
        "app/repositories/business_data_repository.py",
        "app/repositories/shopify_data_repository.py",
        "app/services/__init__.py",
        "app/services/auth_service.py",
        "app/services/user_service.py",
        "app/services/data_service.py",
        "app/utils/__init__.py",
        "app/utils/helpers.py",
        "app/utils/azure_storage.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/v1/api.py",
        "app/api/v1/routes/__init__.py",
        "app/api/v1/routes/auth.py",
        "app/api/v1/routes/users.py",
        "app/api/v1/routes/data.py",
        "app/main.py",
    ]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    missing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
        else:
            print(f"[OK] {file_path}")
    
    if missing_files:
        print(f"\n[FAIL] Missing files: {missing_files}")
        return False
    else:
        print("\n[OK] All required files exist!")
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("Testing New Backend Architecture")
    print("=" * 50)
    
    structure_ok = test_structure()
    imports_ok = test_imports()
    
    print("\n" + "=" * 50)
    if structure_ok and imports_ok:
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed")
        sys.exit(1)

