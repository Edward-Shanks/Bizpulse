# RBAC Implementation Quick Reference

## Overview
This document provides quick reference for implementing Role-Based Access Control (RBAC) in BizPulse.

## RBAC Requirements Summary

### Access Control Dimensions
Users must be restricted across ALL these dimensions:

1. **Business** - Business unit level access
2. **Brand** - Brand-level access
3. **Channel** - Sales channel access (Direct, Online, Retail, etc.)
4. **Customer** - Customer account access
5. **Category** - Product category access
6. **Sub-Category** - Sub-category level access
7. **SKU** - Individual product level access
8. **Data Types** - Metric access:
   - Revenue (sales data)
   - Units (volume data)
   - Gross Profit (profit/margin data)
   - Transfer Cost (restricted)
   - Group Cost (restricted)
   - Finance Data (LTA, Price Downs - highly restricted)

### Implementation Locations

#### 1. Dashboard RBAC
- ✅ Apply to ALL dashboard endpoints
- ✅ Filter MongoDB/ClickHouse queries with user permissions
- ✅ Remove restricted fields from responses

#### 2. AI Chatbot RBAC (CRITICAL)
- ✅ Extract user intent BEFORE querying database
- ✅ Validate access to requested data
- ✅ Return "Access Denied" message if unauthorized
- ✅ Apply permission filters to all queries

## User Permission Structure

```json
{
  "email": "user@company.com",
  "role": "brand_manager",
  "permissions": {
    "businesses": ["Business A", "Business C"],
    "brands": ["Brand X", "Brand Y"],
    "channels": ["Direct", "Online"],
    "customers": "*",
    "categories": ["Electronics"],
    "sub_categories": "*",
    "skus": "*",
    "data_access": {
      "revenue": true,
      "units": true,
      "gross_profit": true,
      "transfer_cost": false,
      "group_cost": false,
      "finance_data": false
    }
  }
}
```

## Quick Implementation Checklist

### Phase 1: Foundation (Week 1-3)
- [ ] Create `users` collection with permission schema
- [ ] Add JWT token with user permissions
- [ ] Create `apply_rbac_filters()` middleware
- [ ] Test with sample users

### Phase 2: Dashboard RBAC (Week 4-6)
- [ ] Apply to Executive Dashboard
- [ ] Apply to Business Compass
- [ ] Apply to Customer Deep Intelligence
- [ ] Apply to Sales Analysis
- [ ] Test each dashboard with different roles

### Phase 3: Chatbot RBAC (Week 7-10)
- [ ] Implement LLM intent extraction
- [ ] Create `validate_rbac_access()` function
- [ ] Add access denial responses
- [ ] Test edge cases (e.g., "show me all financial data")

### Phase 4: Admin UI (Week 11-13)
- [ ] User management interface
- [ ] Permission editor
- [ ] Audit log viewer

### Phase 5: Testing (Week 14-15)
- [ ] Security testing
- [ ] Performance testing
- [ ] User acceptance testing

## Code Snippets

### Apply RBAC to MongoDB Query
```python
async def apply_rbac_filters(user_email, base_query, db):
    user = await db.users.find_one({"email": user_email})
    permissions = user.get("permissions", {})
    
    rbac_filter = {}
    if permissions.get("businesses") != "*":
        rbac_filter["Business"] = {"$in": permissions["businesses"]}
    if permissions.get("brands") != "*":
        rbac_filter["Brand"] = {"$in": permissions["brands"]}
    
    return {**base_query, **rbac_filter}
```

### Validate Chatbot Access
```python
async def validate_rbac_access(user_email, intent, db):
    user = await db.users.find_one({"email": user_email})
    permissions = user.get("permissions", {})
    
    # Check brand access
    requested_brands = intent.get("requested_brands", "all")
    if requested_brands != "all":
        allowed_brands = permissions.get("brands", [])
        if allowed_brands != "*":
            unauthorized = set(requested_brands) - set(allowed_brands)
            if unauthorized:
                return False, f"No access to brands: {', '.join(unauthorized)}"
    
    # Check data type access
    if "finance" in intent.get("requested_data_types", []):
        if not permissions.get("data_access", {}).get("finance_data", False):
            return False, "No access to financial data"
    
    return True, ""
```

## Security Best Practices

1. **Default Deny**: Users have NO access by default
2. **Explicit Grants**: Must explicitly grant permissions
3. **Audit Everything**: Log all data access attempts
4. **Cache Wisely**: Cache permissions for 5 minutes max
5. **Validate Early**: Check permissions BEFORE querying database
6. **Clear Messages**: Tell users WHY access was denied

## Performance Optimization

### MongoDB Indexes
```javascript
// Create compound index for RBAC queries
db.business_data.createIndex({
  "Business": 1,
  "Brand": 1,
  "Customer": 1,
  "Year": -1
})
```

### Permission Caching
```python
# Cache in Redis for 5 minutes
user_permissions = await redis.get(f"permissions:{user_email}")
if not user_permissions:
    user_permissions = await db.users.find_one({"email": user_email})
    await redis.setex(f"permissions:{user_email}", 300, json.dumps(user_permissions))
```

## Testing Scenarios

### Test Case 1: Brand Manager
- **Has Access**: Assigned brands, revenue, profit
- **No Access**: Other brands, cost data, finance data
- **Expected**: See only assigned brand data

### Test Case 2: Sales Team
- **Has Access**: Assigned customers, revenue, units
- **No Access**: Profit data, cost data, finance data
- **Expected**: See customer sales volume only

### Test Case 3: Finance Team
- **Has Access**: All businesses, all financial data
- **No Access**: None (full access)
- **Expected**: See complete financial picture

### Test Case 4: Chatbot Edge Cases
- "Show me all brands" → Filter to allowed brands only
- "What's the transfer cost?" → Access denied if no permission
- "Compare Brand X and Brand Y" → Access denied if user only has Brand X

## Common Pitfalls

1. ❌ **Forgetting to apply RBAC to all endpoints**
2. ❌ **Checking permissions AFTER querying database**
3. ❌ **Not caching permissions (performance hit)**
4. ❌ **Using "*" wildcard incorrectly**
5. ❌ **Not logging access denial attempts**
6. ❌ **Forgetting to update indexes after adding RBAC**

## Support

For detailed implementation guide, see:
- `COMPLETE_SYSTEM_FLOW_AND_DATABASE_RECOMMENDATIONS.md` Section 5

---

**Quick Reference Version**: 1.0  
**Last Updated**: February 8, 2026
