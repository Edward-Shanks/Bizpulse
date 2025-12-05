# Average Margin - Explanation & Calculation

## What is Average Margin?

**Average Margin** (also called **Gross Profit Margin** or **Profit Margin**) is a financial metric that shows **what percentage of revenue remains as profit** after accounting for the cost of goods sold (COGS).

### Simple Definition
Average Margin tells you: **"Out of every €100 in sales, how many euros are profit?"**

---

## Formula

```
Average Margin = (Gross Profit / Revenue) × 100
```

### In Code
```javascript
const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
```

Where:
- **Gross Profit** = Total Revenue - Cost of Goods Sold (COGS)
- **Revenue** = Total Sales/Revenue
- Result is multiplied by 100 to get a percentage

---

## Real-World Example

### Example 1: Simple Calculation
```
Total Revenue: €100,000
Gross Profit: €30,000

Average Margin = (30,000 / 100,000) × 100
               = 0.30 × 100
               = 30%
```

**Meaning:** For every €100 in sales, you keep €30 as profit (after costs).

### Example 2: From Your Dashboard
```
Total Revenue: €117,800,000
Gross Profit: €35,700,000

Average Margin = (35,700,000 / 117,800,000) × 100
               = 0.303 × 100
               = 30.3%
```

**Meaning:** For every €100 in sales, you keep €30.30 as profit.

---

## What It Means

### High Margin (e.g., 40-60%+)
- ✅ **Good:** You're keeping a large portion of revenue as profit
- ✅ **Indicates:** Low cost of goods, efficient operations, or premium pricing
- ✅ **Example:** Software companies often have 70-80% margins

### Medium Margin (e.g., 20-40%)
- ✅ **Normal:** Typical for many businesses
- ✅ **Indicates:** Balanced pricing and costs
- ✅ **Example:** Retail businesses often have 25-35% margins

### Low Margin (e.g., < 20%)
- ⚠️ **Warning:** Small profit per sale
- ⚠️ **Indicates:** High costs, competitive pricing, or low-margin products
- ⚠️ **Example:** Grocery stores often have 5-15% margins

---

## How It's Calculated in Your System

### Step 1: Get Totals from Database
The backend aggregates all records matching your filters:

```python
# Backend calculation (MongoDB aggregation)
pipeline = [
    {"$match": query},  # Apply filters
    {"$group": {
        "_id": None,
        "total_revenue": {"$sum": {"$toDouble": "$Revenue"}},
        "total_profit": {"$sum": {"$toDouble": "$Gross_Profit"}},
        "total_units": {"$sum": {"$toDouble": "$Units"}}
    }}
]
```

### Step 2: Frontend Calculation
```javascript
// Get totals from API response
const totalRevenue = data?.total_revenue || 0;  // e.g., €117,800,000
const totalProfit = data?.total_profit || 0;    // e.g., €35,700,000

// Calculate margin
const avgMargin = totalRevenue > 0 
  ? (totalProfit / totalRevenue) * 100 
  : 0;

// Result: 30.3%
```

### Step 3: Display
```javascript
// Format to 1 decimal place
<p>{avgMargin.toFixed(1)}%</p>  // Shows: 30.3%
```

---

## Important Notes

### 1. This is Gross Profit Margin
- **Not Net Profit Margin:** This doesn't include operating expenses (salaries, rent, marketing, etc.)
- **Only COGS:** This is profit after direct costs of producing/selling products
- **Formula:** Revenue - Cost of Goods Sold = Gross Profit

### 2. It's an Average
- **Aggregated:** Calculated across ALL filtered data
- **Not per-item:** It's the overall margin, not margin per product
- **Weighted:** Naturally weighted by revenue (high-revenue items have more impact)

### 3. Filter-Dependent
- **Changes with filters:** If you filter by year, business, channel, etc., the margin recalculates
- **Example:**
  - All data: 30.3% margin
  - Filter by "Food" business: Might be 35% margin
  - Filter by "2024": Might be 32% margin

---

## Why It Matters

### Business Health Indicator
- **Profitability:** Shows if you're making money on sales
- **Efficiency:** Higher margin = more efficient operations
- **Pricing:** Helps evaluate if pricing is appropriate

### Comparison Tool
- **Year-over-year:** Compare margins across years
- **Business-to-business:** Compare margins across different businesses
- **Channel-to-channel:** Compare margins across sales channels

### Decision Making
- **Product mix:** Focus on high-margin products
- **Pricing strategy:** Adjust prices to improve margins
- **Cost control:** Identify areas where costs are too high

---

## Example Scenarios

### Scenario 1: High Margin Business
```
Revenue: €1,000,000
Profit: €600,000
Margin: 60%

Interpretation: Very profitable! For every €100 in sales, you keep €60.
This might be a software or service business with low COGS.
```

### Scenario 2: Low Margin Business
```
Revenue: €1,000,000
Profit: €100,000
Margin: 10%

Interpretation: Low profitability. For every €100 in sales, you keep only €10.
This might be a high-volume, low-margin business like grocery retail.
```

### Scenario 3: Your Current Data
```
Revenue: €117,800,000
Profit: €35,700,000
Margin: 30.3%

Interpretation: Good profitability! For every €100 in sales, you keep €30.30.
This is a healthy margin for most businesses.
```

---

## Data Flow in Your System

1. **Database:** MongoDB stores individual records with `Revenue` and `Gross_Profit` fields
2. **Backend API:** `/analytics/executive-overview` aggregates totals:
   - Sums all `Revenue` → `total_revenue`
   - Sums all `Gross_Profit` → `total_profit`
3. **Frontend:** Calculates margin:
   ```javascript
   avgMargin = (totalProfit / totalRevenue) × 100
   ```
4. **Display:** Shows as percentage with 1 decimal place (e.g., 30.3%)

---

## Calculation Verification

### From Your Screenshot Data:
```
Total Sales: €117.8M
Gross Profit: €35.7M
Avg. Margin: 30.3%

Let's verify:
Margin = (35.7 / 117.8) × 100
       = 0.303 × 100
       = 30.3% ✅ CORRECT
```

---

## Common Questions

### Q: Why is it called "Average" Margin?
**A:** Because it's calculated across all transactions/products in your filtered dataset. It's the average profitability across all sales.

### Q: Is 30% margin good?
**A:** It depends on your industry:
- **Software/Services:** 30% is moderate (often 50-80%)
- **Retail:** 30% is good (often 20-40%)
- **Manufacturing:** 30% is excellent (often 10-25%)

### Q: Can margin be negative?
**A:** Yes! If costs exceed revenue, margin is negative. This means you're losing money on sales.

### Q: Does this include all costs?
**A:** No, only **Cost of Goods Sold (COGS)**. It doesn't include:
- Operating expenses (salaries, rent)
- Marketing costs
- Administrative costs
- Taxes

---

## Summary

**Average Margin = (Gross Profit / Revenue) × 100**

- **Shows:** Percentage of revenue that becomes profit
- **Formula:** `(Total Profit / Total Revenue) × 100`
- **Your Value:** 30.3% means €30.30 profit per €100 in sales
- **Calculation:** Done in frontend from aggregated backend data
- **Updates:** Automatically when filters change

---

**Last Updated:** 2025
**Status:** ✅ Calculation Verified

