# ✅ How to Run Tests - CORRECT WAY

## 🔴 The Problem

You're running tests from the **wrong directory**!

- ❌ You're in: `backend\` 
- ✅ Tests are in: `backend\scripts\`

## ✅ Solution: Change to Scripts Directory First

### Option 1: Navigate to scripts folder (RECOMMENDED)

```powershell
# Step 1: Go to scripts folder
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts"

# Step 2: Run tests (use full Python path)
C:\Python314\python.exe test_tenant_enforcement.py
C:\Python314\python.exe test_time_filter_injection.py
C:\Python314\python.exe test_ai_simulation_queries.py
```

### Option 2: Run from backend with scripts path

```powershell
# Stay in backend folder
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"

# Run with scripts path
C:\Python314\python.exe scripts\test_tenant_enforcement.py
C:\Python314\python.exe scripts\test_time_filter_injection.py
C:\Python314\python.exe scripts\test_ai_simulation_queries.py
```

### Option 3: Use the helper script (EASIEST)

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts"
.\run_tests.ps1
```

---

## 📁 File Locations

```
backend\
  ├── scripts\
  │   ├── test_tenant_enforcement.py      ← HERE
  │   ├── test_time_filter_injection.py   ← HERE
  │   ├── test_ai_simulation_queries.py   ← HERE
  │   └── run_tests.ps1                   ← Helper script
  └── (you are here when you see the error)
```

---

## 🎯 Quick Fix Command

Copy and paste this:

```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts"; C:\Python314\python.exe test_tenant_enforcement.py
```

This will:
1. Change to the correct directory
2. Run the test with the correct Python

---

## ✅ Verify You're in the Right Place

Before running tests, check:

```powershell
# Should show: C:\Users\Sumit Mishra\Documents\Bizpulse\backend\scripts
pwd

# Should list the test files
ls test_*.py
```

If you see the test files listed, you're in the right place! ✅
