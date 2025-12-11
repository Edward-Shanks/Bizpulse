# Remaining Endpoints Migration Plan

## Overview
This document outlines the plan to migrate the remaining endpoints from `server.py` to the new modular architecture.

## Endpoints to Migrate

### 1. Action Items (Simplest - Start Here)
- **GET** `/cockpit/action-items` - Get action items from MongoDB
- **POST** `/cockpit/action-items/seed` - Seed action items

**Files to Create:**
- `app/repositories/action_items_repository.py`
- `app/services/action_items_service.py`
- `app/api/v1/routes/action_items.py`

**Dependencies:**
- Models already exist: `ActionItem`, `ActionItemsResponse`

---

### 2. Root Cause Analysis (Simple)
- **GET** `/root-cause-analysis/issues` - Get root cause issues
- **POST** `/root-cause-analysis/generate` - Generate new issues using AI

**Files to Create:**
- `app/repositories/root_cause_repository.py`
- `app/services/root_cause_service.py`
- `app/api/v1/routes/root_cause.py`

**Dependencies:**
- Models already exist: `RootCauseIssue`, `RootCauseAnalysisResponse`
- Need to extract AI generation logic

---

### 3. Kanban (Medium Complexity)
- **GET** `/kanban/annual-goal` - Get annual goal metrics
- **GET** `/kanban/recommendations` - Get strategic recommendations
- **POST** `/kanban/generate-goals` - Generate goals using AI
- **POST** `/kanban/goals` - Create/update goal
- **GET** `/kanban/campaigns/{campaignId}/goals` - Get goals for campaign
- **POST** `/kanban/accept` - Accept campaign
- **POST** `/kanban/archive` - Archive campaign
- **POST** `/kanban/move-to-live` - Move campaign to live

**Files to Create:**
- `app/repositories/kanban_repository.py`
- `app/services/kanban_service.py`
- `app/api/v1/routes/kanban.py`

**Dependencies:**
- Models already exist: `StrategicRecommendation`, `GoalRequest`, `GoalResponse`, etc.
- Need to extract AI generation logic for recommendations and goals

---

### 4. Customer Insights Chat (Complex - AI-powered)
- **POST** `/analytics/customer-insights/chat` - AI chat for customer insights

**Files to Create:**
- `app/services/customer_insights_service.py`
- `app/api/v1/routes/customer_insights.py`

**Dependencies:**
- Models already exist: `CustomerInsightsChatRequest`, `CustomerInsightsChatResponse`
- Uses external module `customer_insights_fastapi` - need to check if this exists or needs migration
- Uses `shopify_data` collection

---

### 5. Insights Chat (Most Complex - AI-powered)
- **POST** `/insights/chat` - Main AI chatbot for all screens

**Files to Create:**
- `app/services/insights_service.py`
- `app/api/v1/routes/insights.py`

**Dependencies:**
- Models already exist: `InsightsChatRequest`, `InsightsChatResponse`
- Complex query building logic
- Perplexity API integration
- Pivot table generation
- Data context building

**Helper Functions to Extract:**
- `build_mongodb_query_from_context`
- `parse_query_from_natural_language`
- `get_comprehensive_data_context`
- `query_perplexity`
- `generate_pivot_table`
- And many more...

---

## Migration Order

1. ✅ **Action Items** (Simplest)
2. ✅ **Root Cause Analysis** (Simple)
3. ✅ **Kanban** (Medium)
4. ✅ **Customer Insights Chat** (Complex)
5. ✅ **Insights Chat** (Most Complex)

---

## Testing Strategy

After each migration:
1. Test endpoint with test script
2. Verify database operations
3. Check error handling
4. Verify authentication/authorization

---

## Notes

- All endpoints require authentication via `get_current_user` dependency
- Most AI endpoints use Perplexity API
- Some endpoints use external modules that may need migration
- Query building logic is complex and needs careful extraction

