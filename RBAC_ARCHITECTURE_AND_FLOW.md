# RBAC Architecture & Complete User Flow

## 🤔 Your Question: Why MongoDB + ClickHouse?

**Good question!** Why not just use ClickHouse for everything?

Let me explain with a **complete flow diagram** and the **pros/cons** of each approach.

---

## 📊 Option 1: Hybrid Architecture (MongoDB + ClickHouse) - ⭐ RECOMMENDED

### Why This Approach?

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSACTIONAL DATA (MongoDB)                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Users (signup, login, profile)                                │
│  • User Permissions (RBAC rules)                                 │
│  • Sessions & Tokens                                             │
│  • Audit Logs (who accessed what)                                │
│  • Application State (Kanban, Action Items)                      │
│                                                                  │
│  WHY MongoDB?                                                    │
│    ✅ FAST writes (user signup, permission changes)             │
│    ✅ Flexible schema (permissions can evolve)                   │
│    ✅ Already proven in your pilot                               │
│    ✅ Great for user authentication                              │
│    ✅ Built-in replica sets & high availability                  │
└──────────────────────────────────────────────────────────────────┘
                            │
                            │ User logs in →
                            │ Get permissions from MongoDB
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  ANALYTICAL DATA (ClickHouse)                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Business Data (50-60 crore rows)                              │
│  • Sales Analytics                                               │
│  • Customer Data                                                 │
│  • Real-time Aggregations                                        │
│                                                                  │
│  WHY ClickHouse?                                                 │
│    ✅ 100x FASTER for aggregations                              │
│    ✅ Handles crores of rows                                     │
│    ✅ Sub-second queries                                         │
│    ✅ Columnar storage (efficient)                               │
│    ✅ Perfect for analytics                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Option 2: Pure ClickHouse - ❌ NOT RECOMMENDED

### What if we put RBAC in ClickHouse too?

```
┌──────────────────────────────────────────────────────────────────┐
│  EVERYTHING IN CLICKHOUSE                                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Users table                                                   │
│  • Permissions table                                             │
│  • Business data (50-60 crore rows)                              │
│  • Analytics                                                     │
└──────────────────────────────────────────────────────────────────┘

PROBLEMS:
  ❌ ClickHouse is NOT designed for transactional writes
  ❌ No built-in authentication/sessions
  ❌ Permissions changes would be SLOW (ClickHouse merges data)
  ❌ Complex user management
  ❌ No built-in encryption for passwords
  ❌ Overkill for small user tables (100-1000 users)
  ❌ You'd need MongoDB anyway for app state
```

---

## 🔄 COMPLETE USER FLOW with RBAC

Let me show you the **EXACT flow** from signup to dashboard to AI chatbot:

---

### PHASE 1: User Signup & Registration

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Admin Creates New User                                 │
└─────────────────────────────────────────────────────────────────┘

Admin opens "Create User" form:

┌────────────────────────────────────────────┐
│  Create New User                           │
│                                            │
│  Email:    [user@company.com            ] │
│  Name:     [John Doe                    ] │
│  Password: [••••••••                    ] │
│                                            │
│  ┌─────────────────────────────────────┐  │
│  │ Access Permissions                  │  │
│  │                                     │  │
│  │ Businesses:                         │  │
│  │   ☑ Food                            │  │
│  │   ☐ Beauty                          │  │
│  │                                     │  │
│  │ Channels:                           │  │
│  │   ☑ Convenience                     │  │
│  │   ☑ Direct                          │  │
│  │   ☐ Wholesale                       │  │
│  │                                     │  │
│  │ Brands:                             │  │
│  │   ☑ Heinz                           │  │
│  │   ☑ Coca Cola                       │  │
│  │   ☐ Pepsi                           │  │
│  │                                     │  │
│  │ Categories:                         │  │
│  │   ☑ Beverages                       │  │
│  │   ☐ Snacks                          │  │
│  │                                     │  │
│  │ Data Types:                         │  │
│  │   ☑ Revenue                         │  │
│  │   ☑ Profit                          │  │
│  │   ☐ Costs (Finance only)            │  │
│  └─────────────────────────────────────┘  │
│                                            │
│  [Create User]                             │
└────────────────────────────────────────────┘

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: FastAPI /users/create endpoint                        │
└─────────────────────────────────────────────────────────────────┘

1. Hash password with bcrypt
2. Create user document in MongoDB:

   {
     "user_id": "usr_12345",
     "email": "user@company.com",
     "name": "John Doe",
     "password_hash": "$2b$12$...",
     "role": "sales",
     "is_active": true,
     
     "access_level": {
       "businesses": ["Food"],
       "channels": ["Convenience", "Direct"],
       "brands": ["Heinz", "Coca Cola"],
       "categories": ["Beverages"],
       "sub_categories": ["*"],
       "customers": ["*"],
       "data_types": ["revenue", "profit"]  // NO costs
     },
     
     "created_at": "2026-02-10T...",
     "updated_at": "2026-02-10T..."
   }

3. Save to MongoDB.users_permissions collection
4. Send welcome email to user

✅ User is now in the system!
```

---

### PHASE 2: User Login

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: User Logs In                                           │
└─────────────────────────────────────────────────────────────────┘

User enters:
  Email:    user@company.com
  Password: ••••••••

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: FastAPI /auth/login endpoint                          │
└─────────────────────────────────────────────────────────────────┘

1. Find user in MongoDB by email:
   
   user = await db.users_permissions.find_one({"email": "user@company.com"})

2. Verify password:
   
   bcrypt.checkpw(password, user["password_hash"])

3. If valid, create JWT token (MINIMAL - no permissions):

   token_payload = {
     "user_id": "usr_12345",
     "email": "user@company.com",
     "role": "sales",
     "perm_version": 1,  // ✅ Used for cache invalidation
     "exp": "2026-02-11T..."  // Token expires in 24 hours
   }
   
   # ⚠️ IMPORTANT: JWT does NOT contain permissions!
   # Why? If admin changes permissions, JWT would still have old permissions
   # until it expires (24 hours). This is a security risk.
   # Instead, permissions are fetched from MongoDB on EACH request.
   
   jwt_token = jwt.encode(token_payload, SECRET_KEY)

4. Return token to frontend:

   {
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "user": {
       "name": "John Doe",
       "email": "user@company.com",
       "role": "sales"
     }
   }

5. Frontend stores token in localStorage

✅ User is now authenticated!

**Security Note**: JWT contains ONLY user_id and perm_version.  
MongoDB is the **single source of truth** for permissions.
```

---

### PHASE 3: Dashboard - Load Data with RBAC

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: User Opens Dashboard                                   │
└─────────────────────────────────────────────────────────────────┘

User navigates to /dashboard/business-compass

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: React Dashboard Component                            │
└─────────────────────────────────────────────────────────────────┘

1. Frontend sends request with JWT token:

   GET /api/analytics/business-compass
   Headers: {
     "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: FastAPI /analytics/business-compass endpoint          │
└─────────────────────────────────────────────────────────────────┘

2. Decode JWT token and fetch FRESH permissions from MongoDB:

   # Step 2a: Decode JWT (get user_id only)
   token_data = jwt.decode(token, SECRET_KEY)
   user_id = token_data["user_id"]
   jwt_perm_version = token_data["perm_version"]
   
   # Step 2b: Fetch permissions from MongoDB (single source of truth)
   user = await db.users_permissions.find_one({"user_id": user_id})
   access_level = user["access_level"]
   
   # Step 2c: Verify perm_version (cache invalidation)
   if jwt_perm_version != user["perm_version"]:
       return {"error": "Token outdated, please login again"}
   
   # Now we have FRESH permissions from MongoDB:
   # - businesses: ["Food"]
   # - channels: ["Convenience", "Direct"]
   # - brands: ["Heinz", "Coca Cola"]
   # - data_types: ["revenue", "profit"]  // NO costs
   
   # ✅ If admin changed permissions 5 seconds ago, we see the change NOW
   # ✅ If user was fired, is_active=False blocks access immediately

3. Build ClickHouse query with RBAC filters:

   # Base query
   query = "SELECT"
   
   # RBAC Layer 1: Column filtering by data_types
   if "costs" in access_level["data_types"]:
       columns = "*, group_cost, lta, transfer_cost"
   elif "profit" in access_level["data_types"]:
       columns = "date, business, channel, brand, gsales, cases, fgp"
   else:  # Only revenue
       columns = "date, business, channel, brand, gsales, cases"
   
   query += f" {columns} FROM sales_analytics WHERE 1=1"
   
   # RBAC Layer 2: Row filtering by businesses
   if access_level["businesses"] != ["*"]:
       businesses = "', '".join(access_level["businesses"])
       query += f" AND business IN ('{businesses}')"
   
   # RBAC Layer 3: Row filtering by channels
   if access_level["channels"] != ["*"]:
       channels = "', '".join(access_level["channels"])
       query += f" AND channel IN ('{channels}')"
   
   # RBAC Layer 4: Row filtering by brands
   if access_level["brands"] != ["*"]:
       brands = "', '".join(access_level["brands"])
       query += f" AND brand IN ('{brands}')"
   
   # RBAC Layer 5: Row filtering by categories
   if access_level["categories"] != ["*"]:
       categories = "', '".join(access_level["categories"])
       query += f" AND category IN ('{categories}')"
   
   # Final query looks like:
   query = """
       SELECT date, business, channel, brand, gsales, cases, fgp
       FROM sales_analytics
       WHERE 1=1
       AND business IN ('Food')
       AND channel IN ('Convenience', 'Direct')
       AND brand IN ('Heinz', 'Coca Cola')
       AND category IN ('Beverages')
   """

4. Execute query on ClickHouse:

   ch_client = ClickHouseClient(host="192.168.50.29")
   results = ch_client.execute(query)

5. Aggregate results:

   total_sales = sum([row['gsales'] for row in results])
   total_profit = sum([row['fgp'] for row in results])
   total_cases = sum([row['cases'] for row in results])

6. Return to frontend:

   {
     "total_sales": 5234567.89,
     "total_profit": 1234567.89,
     "total_cases": 12345,
     "sales_by_business": [...],
     "sales_by_channel": [...]
   }

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Display Dashboard                                    │
└─────────────────────────────────────────────────────────────────┘

User sees:
  • Total Sales: €5.2M (ONLY Food business)
  • Total Profit: €1.2M (visible because data_types includes "profit")
  • Total Cases: 12.3K
  • Sales by Channel: Convenience, Direct (ONLY these 2)
  • Sales by Brand: Heinz, Coca Cola (ONLY these 2)

User CANNOT see:
  • Beauty business data (not in their access)
  • Wholesale channel data (not in their access)
  • Cost columns (not in their data_types)
  • Other brands (not in their access)

✅ Dashboard shows ONLY user's authorized data!
```

---

### PHASE 4: AI Assistant Chatbot with RBAC

---
**🔒 PRODUCTION IMPLEMENTATION NOTE (CRITICAL)**:  

The detailed flow below shows the **conceptual approach** for understanding RBAC in AI.  

For **PRODUCTION**, you **MUST** use the **intent-based approach** from `RBAC_PRODUCTION_HARDENED_VERSION.md`:
- ✅ LLM generates **structured intent** (JSON with metrics, dimensions, filters)
- ✅ Backend **builds safe SQL** from intent + RBAC rules
- ✅ Backend **validates SQL** before execution
- ❌ LLM does **NOT** generate raw SQL directly (security risk)

**Why?**  
- LLMs can hallucinate table/column names
- LLMs might forget RBAC filters  
- SQL strings are hard to validate/sanitize
- Intent-based is safer and more deterministic

See `RBAC_PRODUCTION_HARDENED_VERSION.md` **Section 2** for complete implementation.
---

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: User Asks Question in AI Chatbot                       │
└─────────────────────────────────────────────────────────────────┘

User types in chatbot:
  "What were my total sales in January 2025?"

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Send to AI Chatbot API                               │
└─────────────────────────────────────────────────────────────────┘

POST /api/chat/ask
Headers: {
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
Body: {
  "question": "What were my total sales in January 2025?"
}

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: AI Chatbot with RBAC                                  │
└─────────────────────────────────────────────────────────────────┘

1. Decode JWT and fetch FRESH permissions from MongoDB:

   # Decode JWT (get user_id only)
   token_data = jwt.decode(token, SECRET_KEY)
   user_id = token_data["user_id"]
   jwt_perm_version = token_data["perm_version"]
   
   # Fetch FRESH permissions from MongoDB
   user = await db.users_permissions.find_one({"user_id": user_id})
   access_level = user["access_level"]
   
   # Verify perm_version
   if jwt_perm_version != user["perm_version"]:
       return {"error": "Token outdated, please login again"}

2. Send question to LLM with CONTEXT about user's access:

   prompt = f"""
   You are a business analytics assistant.
   
   USER CONTEXT:
   - User has access to: {access_level}
   - They can ONLY see data for:
     * Businesses: {access_level['businesses']}
     * Channels: {access_level['channels']}
     * Brands: {access_level['brands']}
     * Data types: {access_level['data_types']}
   
   USER QUESTION: {user_question}
   
   ⚠️ IMPORTANT: Generate a STRUCTURED INTENT, NOT raw SQL.
   Return JSON with:
   - intent: what user wants (e.g., "get_total_sales")
   - metrics: what to calculate (e.g., ["gsales", "fgp"])
   - dimensions: how to group (e.g., ["month", "business"])
   - filters: what to filter (e.g., {"year": 2025, "business": ["Food"]})
   - timeframe: time period (e.g., "January 2025")
   """

3. LLM generates STRUCTURED INTENT (NOT raw SQL):

   LLM Response:
   {
     "intent": "get_total_sales",
     "timeframe": "January 2025",
     "query": """
       SELECT sum(gsales) as total_sales
       FROM sales_analytics
       WHERE 1=1
       AND year = 2025
       AND month = 1
       AND business IN ('Food')
       AND channel IN ('Convenience', 'Direct')
       AND brand IN ('Heinz', 'Coca Cola')
     """
   }

4. RBAC SAFETY CHECK (Backend validates):

   # Extract tables/columns from query
   tables = extract_tables(query)  # ['sales_analytics']
   columns = extract_columns(query)  # ['gsales']
   where_clauses = extract_where(query)
   
   # Verify user can access these tables
   if 'sales_analytics' not in allowed_tables:
       return {"error": "Access denied"}
   
   # Verify query includes RBAC filters
   required_filters = {
       'business': access_level['businesses'],
       'channel': access_level['channels'],
       'brand': access_level['brands']
   }
   
   for filter_field, allowed_values in required_filters.items():
       if allowed_values != ["*"]:  # If not "all access"
           if filter_field not in where_clauses:
               # Add missing filter
               query += f" AND {filter_field} IN ({allowed_values})"
   
   # Verify user can see these columns
   if 'group_cost' in columns and 'costs' not in access_level['data_types']:
       return {"error": "Access denied: You cannot see cost data"}

5. Execute query on ClickHouse:

   ch_client = ClickHouseClient(host="192.168.50.29")
   results = ch_client.execute(query)
   # Results: [(1234567.89,)]

6. Send results back to LLM for natural language response:

   prompt = f"""
   USER QUESTION: What were my total sales in January 2025?
   
   QUERY RESULT: {results}
   
   Generate a friendly, human-readable response.
   """
   
   LLM Response:
   "Your total sales for January 2025 were €1.23M. 
    This is for the Food business through Convenience and Direct 
    channels, covering Heinz and Coca Cola brands."

7. Return to frontend:

   {
     "answer": "Your total sales for January 2025 were €1.23M...",
     "data": {
       "total_sales": 1234567.89
     },
     "chart": {
       "type": "bar",
       "data": [...]
     }
   }

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Display AI Response                                  │
└─────────────────────────────────────────────────────────────────┘

User sees:
  "Your total sales for January 2025 were €1.23M. This is for 
   the Food business through Convenience and Direct channels, 
   covering Heinz and Coca Cola brands."

User CANNOT ask about:
  • Beauty business (will return "Access denied")
  • Cost data (will return "Access denied")
  • Wholesale channel (will return no data)

✅ AI chatbot respects RBAC at every step!
```

---

### PHASE 5: User Tries to Access Unauthorized Data

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: User Asks About Data They Don't Have Access To         │
└─────────────────────────────────────────────────────────────────┘

User types in chatbot:
  "What were Beauty business sales last month?"

                    ↓

┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: RBAC Check BEFORE Query                               │
└─────────────────────────────────────────────────────────────────┘

1. LLM generates intent (or in old approach, SQL):
   
   Intent:
   {
     "intent": "get_total_sales",
     "filters": {"business": ["Beauty"]}
   }

2. RBAC validation (Backend checks intent against MongoDB permissions):
   
   # Fetch FRESH permissions from MongoDB
   user = await db.users_permissions.find_one({"user_id": user_id})
   user_businesses = user["access_level"]["businesses"]  # ["Food"]
   
   # Check requested businesses
   requested_businesses = intent["filters"]["business"]  # ["Beauty"]
   
   if "Beauty" not in user_businesses:
       return {
         "error": "Access Denied",
         "message": "You don't have access to Beauty business data"
       }

3. Return to frontend:

   {
     "answer": "I'm sorry, but you don't have access to view 
                Beauty business data. Please contact your 
                administrator if you need access.",
     "error": "access_denied"
   }

✅ User is blocked from accessing unauthorized data!
```

---

## 🔐 Multi-Layer RBAC Defense

### Layer 1: JWT Token (Authentication)
```
✓ User must be logged in
✓ Token expires after 24 hours
✓ Token contains ONLY user_id and perm_version (NOT full permissions)
✓ Permissions are fetched from MongoDB on each request
```

### Layer 2: MongoDB Permissions (Authorization)
```
✓ Permissions stored in MongoDB
✓ Easy to update (admin changes permissions)
✓ Flexible schema (can add new permission types)
```

### Layer 3: ClickHouse Query Filters (Backend-Enforced)
```
✓ Backend builds WHERE clause filters by business/channel/brand
✓ Column selection based on data_types
✓ Backend enforces RBAC via WHERE clauses sent to ClickHouse
✓ ClickHouse executes queries, does NOT enforce permissions itself
```

### Layer 4: LLM Context (AI Safety)
```
✓ LLM knows user's access level
✓ LLM generates queries with RBAC filters
✓ Backend validates LLM-generated queries
```

### Layer 5: Backend Validation (Final Check)
```
✓ Backend validates all queries before execution
✓ Checks if user can access requested tables/columns
✓ Adds missing RBAC filters if LLM forgot
✓ Returns "Access Denied" if validation fails
```

---

## 📊 Why Hybrid Architecture is Better

| Aspect | MongoDB (Users/RBAC) | ClickHouse (Analytics) |
|--------|---------------------|------------------------|
| **Write Speed** | ✅ Fast (ms) | ⚠️ Slow (seconds) |
| **Read Speed (Small)** | ✅ Fast | ⚠️ Overkill |
| **Read Speed (Large)** | ❌ Slow | ✅ 100x Faster |
| **Schema Flexibility** | ✅ JSON documents | ⚠️ Fixed schema |
| **Transactions** | ✅ ACID | ❌ No transactions |
| **User Management** | ✅ Built for it | ❌ Not designed for it |
| **Analytics** | ❌ Slow on big data | ✅ Perfect for it |
| **Cost** | ✅ Cheap for small data | ⚠️ Expensive for small data |

### Summary:
- **MongoDB**: Perfect for users, permissions, app state (small, frequent writes)
- **ClickHouse**: Perfect for business data, analytics (large, read-heavy)

---

## 🎯 Final Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER                                   │
│                                                                  │
│  [Login] → [Dashboard] → [AI Chatbot]                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ JWT Token with permissions
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│                                                                  │
│  1. Decode JWT (get user_id + perm_version)                     │
│  2. Fetch FRESH permissions from MongoDB                         │
│  3. Verify perm_version (cache invalidation)                     │
│  4. Build ClickHouse query with RBAC filters                     │
│  5. Validate SQL (final safety check)                            │
│  6. Execute query on ClickHouse                                  │
│  7. Return filtered results                                      │
└─────────────────────────────────────────────────────────────────┘
          │                                    │
          │ Fetch permissions                  │ Execute analytics query
          │ (source of truth)                  │ (with RBAC filters)
          ↓                                    ↓
┌──────────────────────┐          ┌──────────────────────┐
│  MONGODB             │          │  CLICKHOUSE          │
│                      │          │                      │
│  • users_permissions │          │  • sales_analytics   │
│  • users             │          │    (50-60 crore rows)│
│  • sessions          │          │                      │
│  • audit_logs        │          │  Performance:        │
│                      │          │    < 500ms queries   │
│  Fast writes         │          │                      │
│  100-1000 users      │          │  Fast reads          │
└──────────────────────┘          └──────────────────────┘
```

---

## ✅ Benefits of This Architecture

### 1. Security (Multi-Layer)
- ✅ JWT authentication
- ✅ MongoDB permissions
- ✅ ClickHouse query filters
- ✅ Backend validation
- ✅ LLM context awareness

### 2. Performance
- ✅ MongoDB: Fast user lookups (< 10ms)
- ✅ ClickHouse: Fast analytics (< 500ms for crores)
- ✅ Caching: JWT tokens cached in memory

### 3. Scalability
- ✅ MongoDB: Handles millions of users
- ✅ ClickHouse: Handles billions of rows
- ✅ Separate scaling for each component

### 4. Flexibility
- ✅ Easy to add new permissions
- ✅ Easy to add new users
- ✅ Easy to modify access levels
- ✅ No need to recreate ClickHouse views

### 5. Maintainability
- ✅ Clear separation of concerns
- ✅ Easy to debug (separate databases)
- ✅ Easy to backup (separate backups)
- ✅ Your pilot keeps running (MongoDB unchanged)

---

## 🔧 Alternative: Pure ClickHouse (If You Insist)

If you REALLY want to use only ClickHouse:

### Option A: ClickHouse Users + Views (Static RBAC)
```sql
-- Create ClickHouse user for each role
CREATE USER sales_user IDENTIFIED BY 'password';

-- Create view for sales
CREATE VIEW sales_food_view AS
SELECT * FROM sales_analytics 
WHERE business = 'Food';

-- Grant access
GRANT SELECT ON sales_food_view TO sales_user;
```

**Problems**:
- ❌ Must create new ClickHouse user for EACH user (not scalable)
- ❌ Must create new VIEW for each permission combination
- ❌ Can't change permissions without recreating views
- ❌ No UI for user management
- ❌ Still need MongoDB for app state anyway

### Option B: ClickHouse with RBAC Table
```sql
-- Create permissions table in ClickHouse
CREATE TABLE user_permissions (
    user_id String,
    businesses Array(String),
    channels Array(String)
);

-- Join with analytics
SELECT * FROM sales_analytics sa
JOIN user_permissions up ON up.user_id = 'usr_123'
WHERE sa.business IN up.businesses;
```

**Problems**:
- ❌ JOIN makes queries slower
- ❌ ClickHouse not optimized for this
- ❌ Still need MongoDB for authentication
- ❌ More complex queries
- ❌ Harder to maintain

---

## 💡 Recommendation

**Use Hybrid Architecture (MongoDB + ClickHouse)**

**Why?**
1. Each database does what it's best at
2. Your pilot stays unchanged (MongoDB)
3. Better performance (100x faster analytics)
4. Easier to maintain
5. More secure (multi-layer RBAC)
6. Industry best practice

**You'll need MongoDB anyway** for:
- User authentication
- Sessions & tokens
- Application state (Kanban, Action Items)
- Audit logs
- Real-time notifications

**So why not use it for permissions too?** ✅

---

## 📝 Summary

| Component | Database | Purpose |
|-----------|----------|---------|
| **User Signup** | MongoDB | Store user + permissions |
| **User Login** | MongoDB | Verify password, create JWT |
| **Dashboard** | ClickHouse | Fast analytics with RBAC filters |
| **AI Chatbot** | ClickHouse | LLM queries with RBAC |
| **Permissions** | MongoDB | Easy to update, flexible |
| **Audit Logs** | MongoDB | Track access |

**Result**: Fast, Secure, Scalable, Maintainable ✅

---

**Document Status**: ✅ Complete Architecture Explanation  
**Date**: February 10, 2026  
**Version**: 1.0
