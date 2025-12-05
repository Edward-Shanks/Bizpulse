# Dashboard Card Calculations - Complete Documentation

## Overview
This document details all calculations used for the 8 KPI cards on the Business Compass dashboard.

---

## Card 1: Total Sales

### Display Value
- **Formula:** `data.total_revenue`
- **Format:** Currency with 1 decimal place (e.g., €117.8M)
- **Code:** `formatNumber(totalRevenue)`
- **Formatting Logic:**
  - If >= 1,000,000: `€X.XM` (e.g., €117.8M)
  - If >= 1,000: `€X.Xk` (e.g., €15.2k)
  - Otherwise: `€X` (e.g., €500)

### Growth Percentage
- **Formula:** `((Current Month Revenue - Previous Month Revenue) / Previous Month Revenue) × 100`
- **Calculation:**
  ```javascript
  const currentPeriod = monthlyData[monthlyData.length - 1];
  const previousPeriod = monthlyData[monthlyData.length - 2];
  const revenueGrowth = previousPeriod && previousPeriod.Revenue > 0
    ? ((currentPeriod.Revenue - previousPeriod.Revenue) / previousPeriod.Revenue) * 100
    : 0;
  ```
- **Format:** 1 decimal place (e.g., 13.5%)
- **Display:** Green if positive, Red if negative
- **Icon:** TrendingUp if positive, TrendingDown if negative

### Data Source
- `data.total_revenue` - Sum of all Revenue from filtered data
- `data.monthly_trend` - Array of monthly data for growth calculation

---

## Card 2: Gross Profit

### Display Value
- **Formula:** `data.total_profit`
- **Format:** Currency with 1 decimal place (e.g., €35.7M)
- **Code:** `formatNumber(totalProfit)`
- **Formatting Logic:** Same as Total Sales

### Growth Percentage
- **Formula:** `((Current Month Profit - Previous Month Profit) / Previous Month Profit) × 100`
- **Calculation:**
  ```javascript
  const currentPeriod = monthlyData[monthlyData.length - 1];
  const previousPeriod = monthlyData[monthlyData.length - 2];
  const profitGrowth = previousPeriod && previousPeriod.Gross_Profit > 0
    ? ((currentPeriod.Gross_Profit - previousPeriod.Gross_Profit) / previousPeriod.Gross_Profit) * 100
    : 0;
  ```
- **Format:** 1 decimal place (e.g., 14.0%)
- **Display:** Green if positive, Red if negative
- **Icon:** TrendingUp if positive, TrendingDown if negative

### Data Source
- `data.total_profit` - Sum of all Gross_Profit from filtered data
- `data.monthly_trend` - Array of monthly data for growth calculation

---

## Card 3: Cases Sold

### Display Value
- **Formula:** `data.total_units`
- **Format:** Number with 1 decimal place, no currency (e.g., 5.9M)
- **Code:** `formatUnits(totalUnits)`
- **Formatting Logic:**
  - If >= 1,000,000: `X.XM` (e.g., 5.9M)
  - If >= 1,000: `X.Xk` (e.g., 15.2k)
  - Otherwise: `X` (e.g., 500)

### Growth Percentage
- **Formula:** `((Current Month Units - Previous Month Units) / Previous Month Units) × 100`
- **Calculation:**
  ```javascript
  const currentPeriod = monthlyData[monthlyData.length - 1];
  const previousPeriod = monthlyData[monthlyData.length - 2];
  const unitsGrowth = previousPeriod && previousPeriod.Units > 0
    ? ((currentPeriod.Units - previousPeriod.Units) / previousPeriod.Units) * 100
    : 0;
  ```
- **Format:** 1 decimal place (e.g., 19.2%)
- **Display:** Green if positive, Red if negative
- **Icon:** TrendingUp if positive, TrendingDown if negative

### Data Source
- `data.total_units` - Sum of all Units from filtered data
- `data.monthly_trend` - Array of monthly data for growth calculation

---

## Card 4: Avg. Margin

### Display Value
- **Formula:** `(Total Gross Profit / Total Revenue) × 100`
- **Calculation:**
  ```javascript
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  ```
- **Format:** 1 decimal place with % (e.g., 30.3%)
- **Code:** `avgMargin.toFixed(1) + '%'`

### Status Text
- **Display:** "Current" (static text)
- **Color:** Gray

### Data Source
- `data.total_revenue` - Total revenue
- `data.total_profit` - Total gross profit

---

## Card 5: YoY Growth

### Display Value
- **Formula:** `((Latest Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100`
- **Calculation:**
  ```javascript
  const sortedYears = yearlyData.sort((a, b) => b.Year - a.Year);
  const latestYear = sortedYears[0];
  const previousYear = sortedYears[1];
  const yoyGrowth = previousYear && previousYear.Revenue > 0
    ? ((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) * 100
    : 0;
  ```
- **Format:** 1 decimal place with % (e.g., 15.2%)
- **Code:** `yoyGrowth.toFixed(1) + '%'`

### Status Text
- **Logic:**
  - If >= 10%: "Strong" (green)
  - If >= 5%: "Moderate" (green)
  - If >= 0%: "Positive" (green)
  - If < 0%: "Declining" (red)
- **Icon:** TrendingUp if >= 0, TrendingDown if < 0

### Data Source
- `data.yearly_performance` - Array of yearly data with Revenue, Gross_Profit, Units

### Example Calculation
```
Year 2024 Revenue: €100,000,000
Year 2023 Revenue: €87,000,000

YoY Growth = ((100,000,000 - 87,000,000) / 87,000,000) × 100
           = (13,000,000 / 87,000,000) × 100
           = 14.9%
```

---

## Card 6: New Customers

### Display Value
- **Current:** `0` or `N/A` (customer data not available in business_data)
- **Format:** Number with comma separators if available, otherwise "N/A"
- **Code:** `customerAcquisition > 0 ? customerAcquisition.toLocaleString() : 'N/A'`

### Status Text
- **If data available:** Shows growth percentage (e.g., "8.5%") in green
- **If not available:** Shows "Not available" in gray

### Note
- Customer data is not in the `business_data` collection
- To implement, would need to:
  1. Fetch from `/analytics/customer-analysis` endpoint
  2. Count unique customers marked as "New" in the period
  3. Calculate growth from previous period

### Data Source
- Currently: Not available (hardcoded to 0)
- Future: Customer analysis endpoint or customer collection

---

## Card 7: Market Share

### Display Value
- **Formula:** `(Total Revenue / Sum of All Businesses Revenue) × 100`
- **Calculation:**
  ```javascript
  const totalMarketRevenue = businessData.reduce((sum, b) => sum + (b.Revenue || 0), 0);
  const marketShare = totalMarketRevenue > 0
    ? (totalRevenue / totalMarketRevenue) * 100
    : 0;
  ```
- **Format:** 1 decimal place with % (e.g., 28.5%)
- **Code:** `marketShare.toFixed(1) + '%'`

### Growth Percentage
- **Formula:** `((Current Market Share - Previous Market Share) / Previous Market Share) × 100`
- **Calculation:** Compares current market share vs baseline (25.3%)
- **Format:** 1 decimal place (e.g., 3.2%)
- **Display:** Green if positive

### Data Source
- `data.total_revenue` - Total revenue for filtered data
- `data.business_performance` - Array of business data with Revenue

### Example Calculation
```
Total Revenue (filtered): €50,000,000
Sum of All Businesses Revenue: €175,000,000

Market Share = (50,000,000 / 175,000,000) × 100
             = 28.6%
```

### Note
- This is **relative market share** within the dataset (not absolute market share)
- Absolute market share would require external market size data

---

## Card 8: Efficiency

### Display Value
- **Formula:** `Average Margin` (using profit margin as efficiency proxy)
- **Calculation:**
  ```javascript
  const operationalEfficiency = avgMargin; // (totalProfit / totalRevenue) × 100
  ```
- **Format:** 1 decimal place with % (e.g., 92.0%)
- **Code:** `operationalEfficiency.toFixed(1) + '%'`

### Growth Percentage
- **Formula:** `((Current Efficiency - Baseline Efficiency) / Baseline Efficiency) × 100`
- **Calculation:** Compares current efficiency vs baseline (89%)
- **Format:** 1 decimal place (e.g., 3.0%)
- **Display:** Green if positive

### Data Source
- `data.total_revenue` - Total revenue
- `data.total_profit` - Total gross profit

### Note
- Currently uses profit margin as a proxy for operational efficiency
- Could be updated to use a different efficiency metric if defined:
  - Resource utilization
  - Operational cost efficiency
  - Revenue per unit efficiency
  - Target vs actual performance

---

## Common Formatting Rules

### Number Formatting
- **Currency (Revenue, Profit):**
  - >= 1M: `€X.XM` (1 decimal)
  - >= 1k: `€X.Xk` (1 decimal)
  - < 1k: `€X` (no decimals)

- **Units (Cases):**
  - >= 1M: `X.XM` (1 decimal)
  - >= 1k: `X.Xk` (1 decimal)
  - < 1k: `X` (no decimals)

### Percentage Formatting
- **All percentages:** 1 decimal place (e.g., 13.5%, 30.3%)
- **Code:** `.toFixed(1) + '%'`

### Growth Indicators
- **Green:** Positive growth (>= 0)
- **Red:** Negative growth (< 0)
- **Icon:** TrendingUp (positive) or TrendingDown (negative)

### Text Overflow Prevention
- **All card values:** Use `truncate` class to prevent overflow
- **Labels:** Use `whitespace-nowrap` to prevent wrapping

---

## Data Flow

1. **API Call:** `/analytics/executive-overview` with filters
2. **Response Contains:**
   - `total_revenue` - Sum of all Revenue
   - `total_profit` - Sum of all Gross_Profit
   - `total_units` - Sum of all Units
   - `yearly_performance` - Array of yearly data
   - `business_performance` - Array of business data
   - `monthly_trend` - Array of monthly data
   - `channel_performance` - Array of channel data

3. **Calculations:**
   - Totals: Direct from API response
   - Growth: Calculated from monthly/yearly data
   - Percentages: Calculated from totals
   - Market Share: Calculated from business data

4. **Formatting:**
   - Apply number formatting functions
   - Round to 1 decimal place for percentages
   - Add appropriate units (€, M, k, %)

---

## Edge Cases Handled

1. **No Data:**
   - All calculations default to 0
   - Display shows "0" or "N/A" appropriately

2. **Division by Zero:**
   - All division operations check for zero before dividing
   - Returns 0 if denominator is 0

3. **Missing Periods:**
   - Growth calculations check if previous period exists
   - Returns 0 if no previous period available

4. **Empty Arrays:**
   - All array operations check for length
   - Default to empty array if undefined

5. **Text Overflow:**
   - All values use `truncate` class
   - Labels use `whitespace-nowrap`

---

## Summary Table

| Card | Main Value | Formula | Growth/Status | Format |
|------|------------|---------|--------------|--------|
| Total Sales | Revenue | `data.total_revenue` | Month-over-month % | €X.XM |
| Gross Profit | Profit | `data.total_profit` | Month-over-month % | €X.XM |
| Cases Sold | Units | `data.total_units` | Month-over-month % | X.XM |
| Avg. Margin | Margin % | `(Profit/Revenue)×100` | "Current" | X.X% |
| YoY Growth | Growth % | `((Yr2-Yr1)/Yr1)×100` | Status text | X.X% |
| New Customers | Count | Not available | N/A | Number or "N/A" |
| Market Share | Share % | `(Revenue/Total)×100` | vs baseline % | X.X% |
| Efficiency | Margin % | `(Profit/Revenue)×100` | vs baseline % | X.X% |

---

**Last Updated:** 2025
**Status:** ✅ All Calculations Documented

