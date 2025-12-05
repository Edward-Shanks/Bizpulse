# Dashboard Metrics - Formulas & Calculations

## Current Status

### ✅ Correctly Calculated Metrics

1. **Avg. Margin (30.4%)**
   - **Formula:** `(Total Gross Profit / Total Revenue) × 100`
   - **Code:** `const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;`
   - **Status:** ✅ **CORRECT** - Calculated from actual data
   - **Location:** `frontend/src/pages/DashboardNew.js:438`

2. **Total Sales, Gross Profit, Cases Sold**
   - **Formula:** Sum of all records based on filters
   - **Status:** ✅ **CORRECT** - Calculated from actual data

### ❌ Hardcoded Metrics (NEED TO BE FIXED)

3. **YoY Growth (15.2%)**
   - **Current:** Hardcoded value `15.2`
   - **Should be:** Calculated from yearly performance data
   - **Formula:** `((Current Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100`
   - **Location:** `frontend/src/pages/DashboardNew.js:444`
   - **Status:** ❌ **INCORRECT** - Hardcoded

4. **New Customers (245)**
   - **Current:** Hardcoded value `245`
   - **Should be:** Calculated from customer data (if available)
   - **Formula:** Count of unique new customers in the period
   - **Location:** `frontend/src/pages/DashboardNew.js:445`
   - **Status:** ❌ **INCORRECT** - Hardcoded (may not be available in business_data)

5. **Market Share (28.5%)**
   - **Current:** Hardcoded value `28.5`
   - **Should be:** Calculated based on business performance
   - **Formula:** `(Business Revenue / Total Market Revenue) × 100` OR `(Business Revenue / Sum of All Businesses Revenue) × 100`
   - **Location:** `frontend/src/pages/DashboardNew.js:446`
   - **Status:** ❌ **INCORRECT** - Hardcoded (requires market data or relative calculation)

6. **Efficiency (92%)**
   - **Current:** Hardcoded value `92`
   - **Should be:** Calculated from operational metrics
   - **Possible Formulas:**
     - Option 1: `(Gross Profit / Revenue) × 100` (same as margin, but could be different)
     - Option 2: `(Actual Profit / Target Profit) × 100`
     - Option 3: `(Revenue per Unit / Average Revenue per Unit) × 100`
   - **Location:** `frontend/src/pages/DashboardNew.js:447`
   - **Status:** ❌ **INCORRECT** - Hardcoded (needs definition)

## Proposed Formulas

### 1. YoY Growth (Year-over-Year Growth)

**Formula:**
```javascript
// Get latest year and previous year from yearlyData
const sortedYears = yearlyData.sort((a, b) => b.Year - a.Year);
const latestYear = sortedYears[0];
const previousYear = sortedYears[1];

const yoyGrowth = previousYear && previousYear.Revenue > 0
  ? ((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) * 100
  : 0;
```

**Data Source:** `data.yearly_performance` array

**Example:**
- 2024 Revenue: €100M
- 2023 Revenue: €87M
- YoY Growth: ((100 - 87) / 87) × 100 = 14.9%

---

### 2. New Customers

**Issue:** Customer data may not be in `business_data` collection. Need to check if customer data is available.

**If Customer Data Available:**
```javascript
// Count unique customers marked as "New" in the period
const newCustomers = customerData.filter(c => c.isNew === true).length;
```

**If Not Available:**
- Option 1: Remove this metric
- Option 2: Calculate from a different source (e.g., customer analysis endpoint)
- Option 3: Show "N/A" or "Not Available"

**Data Source:** May need to fetch from `/analytics/customer-analysis` endpoint

---

### 3. Market Share

**Option 1: Relative Market Share (Within Business Data)**
```javascript
// Calculate as percentage of total revenue across all businesses
const totalMarketRevenue = businessData.reduce((sum, b) => sum + b.Revenue, 0);
const marketShare = totalRevenue > 0 
  ? (totalRevenue / totalMarketRevenue) * 100 
  : 0;
```

**Option 2: Absolute Market Share (Requires External Data)**
- Would need total market size data (not available in current dataset)
- Could be configured as a constant or fetched from external source

**Recommended:** Use Option 1 (relative share within the dataset)

**Data Source:** `data.business_performance` array

---

### 4. Efficiency

**Option 1: Profit Efficiency (Profit Margin)**
```javascript
// Same as avgMargin, but could be calculated differently
const efficiency = totalRevenue > 0 
  ? (totalProfit / totalRevenue) * 100 
  : 0;
```

**Option 2: Revenue per Unit Efficiency**
```javascript
// Compare actual revenue per unit vs target
const revenuePerUnit = totalUnits > 0 ? totalRevenue / totalUnits : 0;
const efficiency = revenuePerUnit > 0 ? (revenuePerUnit / targetRevenuePerUnit) * 100 : 0;
```

**Option 3: Operational Efficiency (Based on Business Performance)**
```javascript
// Calculate based on best performing business
const bestBusinessRevenue = Math.max(...businessData.map(b => b.Revenue));
const efficiency = bestBusinessRevenue > 0 
  ? (totalRevenue / bestBusinessRevenue) * 100 
  : 0;
```

**Recommended:** Use Option 1 (same as margin) OR define a specific efficiency metric based on business requirements

**Data Source:** `data.business_performance` or calculated from totals

---

## Growth Percentages (Currently Hardcoded)

The following growth percentages are also hardcoded and should be calculated:

1. **Revenue Growth (8.2%)**
   - Should compare current period vs previous period
   
2. **Profit Growth (5.1%)**
   - Should compare current period profit vs previous period profit

3. **Units Growth (-2.3%)**
   - Should compare current period units vs previous period units

**Formula for Period Growth:**
```javascript
// Compare latest month/period vs previous month/period
const currentPeriod = monthlyData[monthlyData.length - 1];
const previousPeriod = monthlyData[monthlyData.length - 2];

const revenueGrowth = previousPeriod && previousPeriod.Revenue > 0
  ? ((currentPeriod.Revenue - previousPeriod.Revenue) / previousPeriod.Revenue) * 100
  : 0;
```

---

## Implementation Plan

### Step 1: Fix YoY Growth
- ✅ Calculate from `yearlyData`
- ✅ Compare latest year vs previous year
- ✅ Handle edge cases (no previous year, zero revenue)

### Step 2: Fix New Customers
- ⚠️ Check if customer data is available
- ⚠️ If available, calculate from customer data
- ⚠️ If not available, either remove or fetch from customer endpoint

### Step 3: Fix Market Share
- ✅ Calculate relative market share from business data
- ✅ Show as percentage of total business revenue

### Step 4: Fix Efficiency
- ⚠️ Define what "Efficiency" means for the business
- ⚠️ Implement appropriate formula
- ⚠️ Could use profit margin as a proxy

### Step 5: Fix Growth Percentages
- ✅ Calculate revenue, profit, and units growth from monthly/period data
- ✅ Compare current vs previous period

---

## Data Available

From the API endpoint `/analytics/executive-overview`, we have:
- `total_revenue` - Total revenue
- `total_profit` - Total gross profit
- `total_units` - Total cases/units
- `yearly_performance` - Array of yearly data with Revenue, Gross_Profit, Units
- `business_performance` - Array of business data with Revenue, Gross_Profit, Units
- `monthly_trend` - Array of monthly data with Revenue, Gross_Profit, Units
- `channel_performance` - Array of channel data

---

## Next Steps

1. ✅ Document current formulas (this file)
2. ⏳ Fix YoY Growth calculation
3. ⏳ Fix Market Share calculation
4. ⏳ Fix Efficiency calculation (after defining what it means)
5. ⏳ Fix New Customers (check data availability)
6. ⏳ Fix growth percentages (revenue, profit, units)

---

**Last Updated:** 2025
**Status:** Documentation Complete, Implementation Pending

