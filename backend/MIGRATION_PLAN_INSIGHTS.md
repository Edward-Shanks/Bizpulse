# Insights Chat Migration Plan

## Overview
Migrating the two remaining AI chat endpoints:
1. Customer Insights Chat (`/analytics/customer-insights/chat`) - ✅ DONE
2. Insights Chat (`/insights/chat`) - IN PROGRESS

## Files to Create/Update

### 1. Customer Insights Chat ✅
- ✅ `app/services/customer_insights_service.py` - Created
- ✅ `app/api/v1/routes/customer_insights.py` - Created
- ✅ `app/models/customer_insights.py` - Already exists

### 2. Insights Chat (Complex)
- ⏳ `app/utils/data_context.py` - For `get_comprehensive_data_context` and `get_data_context_for_chart`
- ⏳ `app/utils/query_builder.py` - Add `parse_query_from_natural_language` and `build_mongodb_query_from_context`
- ⏳ `app/services/insights_service.py` - Main service for Insights Chat
- ⏳ `app/api/v1/routes/insights.py` - Route handler

## Helper Functions to Extract

### From `server.py`:
1. `parse_query_from_natural_language` (lines 5592-5808) → `app/utils/query_builder.py`
2. `build_mongodb_query_from_context` (lines 5810-5867) → `app/utils/query_builder.py`
3. `get_comprehensive_data_context` (lines 6127-6423) → `app/utils/data_context.py`
4. `get_data_context_for_chart` (lines 5869-6125) → `app/utils/data_context.py`
5. Main endpoint logic (lines 6425-7269) → `app/services/insights_service.py`

## Dependencies
- `app/utils/helpers.py` - Already has `safe_float`, `format_currency`, `format_units`, `parse_list`
- `app/utils/ai_service.py` - Already has `query_perplexity`
- `app/utils/query_builder.py` - Already has `apply_business_filter`

## Next Steps
1. Add query builder functions to `query_builder.py`
2. Create `data_context.py` with data context functions
3. Create `insights_service.py` with main logic
4. Create `insights.py` route
5. Update `app/api/v1/api.py` to include routes
6. Test endpoints

