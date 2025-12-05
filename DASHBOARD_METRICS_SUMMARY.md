# Dashboard Metrics - Summary & Formulas

## ✅ Fixed Metrics (Now Calculated from Real Data)

### 1. **Avg. Margin (30.4%)**
- **Formula:** `(Total Gross Profit / Total Revenue) × 100`
- **Status:** ✅ **CORRECT** - Was already calculated correctly
- **Code:** `const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;`

### 2. **YoY Growth (15.2%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `15.2`
- **New Formula:** `((Latest Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100`
- **Calculation:**
  ```javascript
  const sortedYears = yearlyData.sort((a, b) => b.Year - a.Year);
  const latestYear = sortedYears[0];
  const previousYear = sortedYears[1];
  const yoyGrowth = ((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) * 100;
  ```
- **Data Source:** `data.yearly_performance` array
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA**

### 3. **Market Share (28.5%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `28.5`
- **New Formula:** `(Total Revenue / Sum of All Businesses Revenue) × 100`
- **Calculation:**
  ```javascript
  const totalMarketRevenue = businessData.reduce((sum, b) => sum + b.Revenue, 0);
  const marketShare = (totalRevenue / totalMarketRevenue) * 100;
  ```
- **Data Source:** `data.business_performance` array
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA** (Relative market share within dataset)

### 4. **Efficiency (92%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `92`
- **New Formula:** Uses Average Margin as efficiency metric
- **Calculation:** `const operationalEfficiency = avgMargin;`
- **Note:** This uses profit margin as a proxy for operational efficiency. If a different efficiency metric is needed, it can be updated.
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA**

### 5. **Revenue Growth (8.2%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `8.2`
- **New Formula:** `((Current Period Revenue - Previous Period Revenue) / Previous Period Revenue) × 100`
- **Calculation:** Compares latest month vs previous month from `monthlyData`
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA**

### 6. **Profit Growth (5.1%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `5.1`
- **New Formula:** `((Current Period Profit - Previous Period Profit) / Previous Period Profit) × 100`
- **Calculation:** Compares latest month vs previous month from `monthlyData`
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA**

### 7. **Units Growth (-2.3%)** - ✅ **FIXED**
- **Previous:** Hardcoded value `-2.3`
- **New Formula:** `((Current Period Units - Previous Period Units) / Previous Period Units) × 100`
- **Calculation:** Compares latest month vs previous month from `monthlyData`
- **Status:** ✅ **NOW CALCULATED FROM REAL DATA**

### 8. **New Customers (245)** - ⚠️ **PARTIALLY FIXED**
- **Previous:** Hardcoded value `245`
- **Current:** Shows `0` or `N/A` because customer data is not in `business_data` collection
- **Status:** ⚠️ **DATA NOT AVAILABLE** - Customer data would need to come from:
  - Customer analysis endpoint (`/analytics/customer-analysis`)
  - Or a separate customer collection
- **Note:** To fully implement, would need to:
  1. Fetch customer data from customer endpoint
  2. Count unique new customers in the period
  3. Calculate growth percentage

---

## 📊 Complete Formula Reference

### All Metrics Now Calculated:

| Metric | Formula | Data Source | Status |
|--------|---------|-------------|--------|
| **Total Sales** | Sum of all Revenue | `data.total_revenue` | ✅ Correct |
| **Gross Profit** | Sum of all Gross_Profit | `data.total_profit` | ✅ Correct |
| **Cases Sold** | Sum of all Units | `data.total_units` | ✅ Correct |
| **Avg. Margin** | `(Profit / Revenue) × 100` | Calculated | ✅ Correct |
| **YoY Growth** | `((Current Year - Previous Year) / Previous Year) × 100` | `yearlyData` | ✅ Fixed |
| **Revenue Growth** | `((Current Month - Previous Month) / Previous Month) × 100` | `monthlyData` | ✅ Fixed |
| **Profit Growth** | `((Current Month - Previous Month) / Previous Month) × 100` | `monthlyData` | ✅ Fixed |
| **Units Growth** | `((Current Month - Previous Month) / Previous Month) × 100` | `monthlyData` | ✅ Fixed |
| **Market Share** | `(Total Revenue / Sum of All Businesses) × 100` | `businessData` | ✅ Fixed |
| **Efficiency** | `Avg Margin` (profit margin as proxy) | Calculated | ✅ Fixed |
| **New Customers** | Count of new customers | Customer data | ⚠️ Not Available |

---

## 🔍 How Each Metric Works

### YoY Growth Calculation Example:
```
Year 2024 Revenue: €100,000,000
Year 2023 Revenue: €87,000,000

YoY Growth = ((100,000,000 - 87,000,000) / 87,000,000) × 100
           = (13,000,000 / 87,000,000) × 100
           = 14.9%
```

### Market Share Calculation Example:
```
Total Revenue (filtered): €50,000,000
Sum of All Businesses Revenue: €175,000,000

Market Share = (50,000,000 / 175,000,000) × 100
             = 28.6%
```

### Period Growth Calculation Example:
```
November Revenue: €12,000,000
October Revenue: €11,000,000

Revenue Growth = ((12,000,000 - 11,000,000) / 11,000,000) × 100
               = (1,000,000 / 11,000,000) × 100
               = 9.1%
```

---

## 📝 Notes

1. **Market Share** is calculated as relative share within the dataset (not absolute market share, which would require external market data)

2. **Efficiency** currently uses profit margin as a proxy. If a different efficiency metric is needed (e.g., operational efficiency, resource utilization), it can be updated.

3. **New Customers** requires customer data which is not in the `business_data` collection. To implement:
   - Fetch from `/analytics/customer-analysis` endpoint
   - Or query customer collection if available
   - Count unique customers marked as "New" in the period

4. **All growth percentages** now dynamically calculate based on available data and will show negative values if there's a decline.

5. **All metrics respect filters** - they calculate based on the selected filters (year, month, business, channel, brand, category).

---

## ✅ Changes Made

1. ✅ Removed all hardcoded values
2. ✅ Implemented YoY Growth calculation from yearly data
3. ✅ Implemented Market Share calculation from business data
4. ✅ Implemented Efficiency calculation (using margin)
5. ✅ Implemented period growth calculations (revenue, profit, units)
6. ✅ Updated New Customers to show "N/A" when data not available
7. ✅ Added proper formatting (toFixed(1)) for all percentages
8. ✅ Added dynamic status indicators (Strong/Moderate/Positive/Declining)

---

## 🎯 Result

All metrics (except New Customers which requires separate data source) are now calculated from real data and will update dynamically based on:
- Selected filters
- Available data
- Time periods

The dashboard now shows accurate, real-time metrics instead of hardcoded values!

---

**Last Updated:** 2025
**Status:** ✅ All Metrics Fixed (Except New Customers - Data Not Available)

