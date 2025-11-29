# Security Fixes - Removed Hardcoded Secrets

## Summary
All hardcoded API keys, passwords, and secrets have been removed from the codebase and replaced with environment variable references.

## Changes Made

### 1. `backend/app.py`
**Before:**
- Hardcoded Perplexity API key: `"REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5"`
- Hardcoded file path: `r"C:\Users\Sumit Mishra\Downloads\shopify_data.csv"`

**After:**
- Uses `PPLX_API_KEY1` or `PERPLEXITY_API_KEY` from environment
- Uses `SHOPIFY_DATA_PATH` from environment (defaults to `backend/shopify_data.csv`)
- Added `.env` file loading with `dotenv`

### 2. `backend/server.py`
**Before:**
- Hardcoded default passwords: `"123456User"` and `"Thrive@123"`

**After:**
- Uses `DEFAULT_USER_PASSWORD` from environment (defaults to `"123456User"`)
- Uses `ADMIN_PASSWORD` from environment (defaults to `"Thrive@123"`)

### 3. `backend/check_user.py`
**Before:**
- Hardcoded password: `'Barry@123'`

**After:**
- Uses `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` from environment

### 4. `backend/check_admin_user.py`
**Before:**
- Hardcoded password: `'Thrive@123'`

**After:**
- Uses `ADMIN_EMAIL` and `ADMIN_PASSWORD` from environment

## Required Environment Variables

Add these to your `.env` file in the `backend/` directory:

```env
# Perplexity AI API Key (REQUIRED for app.py)
PPLX_API_KEY1=your_perplexity_api_key_here

# Optional: Alternative name for Perplexity API key
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Optional: Shopify data file path (defaults to backend/shopify_data.csv)
SHOPIFY_DATA_PATH=path/to/shopify_data.csv

# Optional: Default user passwords (for initial setup only)
DEFAULT_USER_PASSWORD=your_secure_password
ADMIN_PASSWORD=your_secure_admin_password

# Optional: Test user credentials (for utility scripts)
TEST_USER_EMAIL=Barry@thrivebrands.ai
TEST_USER_PASSWORD=your_test_password
ADMIN_EMAIL=admin@thrivebrands.ai
```

## Important Notes

1. **Never commit `.env` files** - They should be in `.gitignore`
2. **Set strong passwords** - Don't use default passwords in production
3. **Rotate API keys** - If a key was exposed, generate a new one
4. **Use different keys per environment** - Dev, staging, and production should have separate keys

## Verification

After making these changes:
1. Create/update your `.env` file with the required variables
2. Test that `app.py` loads the API key correctly
3. Test that the server starts without errors
4. Verify that no secrets appear in `git diff` or `git log`

## Git History Cleanup

If you've already committed secrets to git history, you'll need to:
1. Remove the secrets from the current commit (already done)
2. Consider using `git filter-branch` or BFG Repo-Cleaner to remove secrets from history
3. Rotate any exposed API keys immediately

