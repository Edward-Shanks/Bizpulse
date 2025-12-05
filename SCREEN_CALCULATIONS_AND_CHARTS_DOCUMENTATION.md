# Complete Screen Calculations and Charts Documentation

This document provides a comprehensive breakdown of all calculations, charts, graphs, and column usage across all screens in the BizPulse application.

---

## Table of Contents

1. [Business Compass (Dashboard)](#1-business-compass-dashboard)
2. [Brands Analysis](#2-brands-analysis)
3. [Customers Analysis](#3-customers-analysis)
4. [Categories Analysis](#4-categories-analysis)
5. [Sales Analysis](#5-sales-analysis)

---

## 1. Business Compass (Dashboard)

**File:** `frontend/src/pages/DashboardNew.js`  
**API Endpoint:** `/analytics/executive-overview`

### KPI Cards (Summary Metrics)

#### 1.1 Total Sales Card
- **Display Value:** `totalRevenue`
- **Data Source:** `data.total_revenue` (from API)
- **Calculation:**
  ```javascript
  const totalRevenue = data?.total_revenue || 0;
  ```
- **Column Used:** `Revenue` (summed from all records)
- **Format:** Formatted using `formatNumber()` (e.g., €117.8M)
- **Growth Calculation:**
  ```javascript
  const revenueGrowth = ((currentPeriod.Revenue - previousPeriod.Revenue) / previousPeriod.Revenue) * 100;
  ```
  - Uses last 2 months from `monthly_trend` array
  - Format: 1 decimal place (e.g., 13.5%)

#### 1.2 Gross Profit Card
- **Display Value:** `totalProfit`
- **Data Source:** `data.total_profit` (from API)
- **Calculation:**
  ```javascript
  const totalProfit = data?.total_profit || 0;
  ```
- **Column Used:** `Gross_Profit` (summed from all records)
- **Format:** Formatted using `formatNumber()` (e.g., €35.7M)
- **Growth Calculation:**
  ```javascript
  const profitGrowth = ((currentPeriod.Gross_Profit - previousPeriod.Gross_Profit) / previousPeriod.Gross_Profit) * 100;
  ```
  - Uses last 2 months from `monthly_trend` array
  - Format: 1 decimal place (e.g., 14.0%)

#### 1.3 Cases Sold Card
- **Display Value:** `totalUnits`
- **Data Source:** `data.total_units` (from API)
- **Calculation:**
  ```javascript
  const totalUnits = data?.total_units || 0;
  ```
- **Column Used:** `Units` (summed from all records)
- **Format:** Formatted using `formatNumber()` (e.g., 5.9M)
- **Growth Calculation:**
  ```javascript
  const unitsGrowth = ((currentPeriod.Units - previousPeriod.Units) / previousPeriod.Units) * 100;
  ```
  - Uses last 2 months from `monthly_trend` array
  - Format: 1 decimal place (e.g., 19.2%)

#### 1.4 Avg. Margin Card
- **Display Value:** `avgMargin`
- **Data Source:** Calculated from `totalRevenue` and `totalProfit`
- **Calculation:**
  ```javascript
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  ```
- **Formula:** `(Gross Profit / Revenue) × 100`
- **Columns Used:** `Gross_Profit` and `Revenue` (aggregated)
- **Format:** 1 decimal place with % (e.g., 30.3%)

#### 1.5 YoY Growth Card (Commented Out)
- **Display Value:** `yoyGrowth`
- **Data Source:** `yearly_performance` array
- **Calculation:**
  ```javascript
  const sortedYears = [...yearlyData].sort((a, b) => b.Year - a.Year);
  const latestYear = sortedYears[0];
  const previousYear = sortedYears[1];
  yoyGrowth = ((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) * 100;
  ```
- **Columns Used:** `Year`, `Revenue` from yearly aggregation
- **Format:** 1 decimal place (e.g., 0.0%)

#### 1.6 New Customers Card (Commented Out)
- **Display Value:** "N/A"
- **Status:** Not available (customer data not in current endpoint)
- **Calculation:** `customerAcquisition = 0`

#### 1.7 Market Share Card (Commented Out)
- **Display Value:** `marketShare`
- **Data Source:** Calculated from `business_performance` array
- **Calculation:**
  ```javascript
  const totalMarketRevenue = businessData.reduce((sum, b) => sum + (b.Revenue || 0), 0);
  marketShare = (totalRevenue / totalMarketRevenue) * 100;
  ```
- **Columns Used:** `Revenue` from business aggregation
- **Format:** 1 decimal place (e.g., 100.0%)

#### 1.8 Efficiency Card (Commented Out)
- **Display Value:** `operationalEfficiency`
- **Data Source:** Same as `avgMargin`
- **Calculation:**
  ```javascript
  const operationalEfficiency = avgMargin;
  ```
- **Format:** 1 decimal place (e.g., 31.5%)

---

### Charts and Graphs

#### 1.9 Sales Trend (YTD) - Line Chart
- **Chart Type:** Line Chart
- **Chart Name:** `salesTrend`
- **Data Source:** `monthly_trend` array
- **X-Axis:** `Month_Name` (sorted: Jan, Feb, Mar, ..., Dec)
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Month_Name` (labels)
  - `Revenue` (data points)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 1.10 Revenue vs Expenses - Bar Chart
- **Chart Type:** Bar Chart (Grouped)
- **Chart Name:** `revenueExpenses`
- **Data Source:** `yearly_performance` array
- **X-Axis:** `Year`
- **Y-Axis:** Two datasets
  - **Dataset 1 (Revenue):** `Revenue` column
  - **Dataset 2 (Expenses):** Calculated as `Revenue - Gross_Profit`
- **Columns Used:**
  - `Year` (labels)
  - `Revenue` (first bar)
  - `Gross_Profit` (for calculating expenses)
- **Calculation:**
  ```javascript
  Expenses = Revenue - Gross_Profit
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 1.11 Business vs Cases - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `businessCases`
- **Data Source:** `business_performance` array
- **X-Axis:** `Business` (rotated 45°)
- **Y-Axis:** `Units`
- **Columns Used:**
  - `Business` (labels)
  - `Units` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatUnits(value)` with "cases" suffix

#### 1.12 Business vs Sales - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `businessSales`
- **Data Source:** `business_performance` array
- **X-Axis:** `Business` (rotated 45°)
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Business` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 1.13 Business vs Gross Profit - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `businessProfit`
- **Data Source:** `business_performance` array
- **X-Axis:** `Business` (rotated 45°)
- **Y-Axis:** `Gross_Profit`
- **Columns Used:**
  - `Business` (labels)
  - `Gross_Profit` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 1.14 Channel Distribution - Doughnut Chart
- **Chart Type:** Doughnut Chart
- **Chart Name:** `channelDist`
- **Data Source:** `channel_performance` array
- **Labels:** `Channel`
- **Data:** `Revenue`
- **Columns Used:**
  - `Channel` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatNumber(value)`

#### 1.15 Business Performance - Pie Chart
- **Chart Type:** Pie Chart
- **Chart Name:** `businessPerf`
- **Data Source:** `business_performance` array
- **Labels:** `Business`
- **Data:** `Revenue`
- **Columns Used:**
  - `Business` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatNumber(value)`

#### 1.16 Top Performers - Bar Chart
- **Chart Type:** Bar Chart (Grouped)
- **Chart Name:** `topPerformers`
- **Data Source:** `business_performance` array (top 5)
- **X-Axis:** `Business` (top 5 only)
- **Y-Axis:** Two datasets
  - **Dataset 1 (Revenue):** `Revenue` column
  - **Dataset 2 (Profit):** `Gross_Profit` column
- **Columns Used:**
  - `Business` (labels, sliced to top 5)
  - `Revenue` (first bar)
  - `Gross_Profit` (second bar)
- **Calculation:**
  ```javascript
  const top5 = businessData.slice(0, 5);
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

---

## 2. Brands Analysis

**File:** `frontend/src/pages/BrandAnalysisNew.js`  
**API Endpoint:** `/analytics/brand-analysis`

### KPI Cards (Summary Metrics)

#### 2.1 Total Revenue Card
- **Display Value:** `totalRevenue`
- **Data Source:** `data.total_revenue` or calculated from `brand_performance`
- **Calculation:**
  ```javascript
  const totalRevenue = data?.total_revenue ?? brandData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  ```
- **Columns Used:** `Revenue` from `brand_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €117.8M)

#### 2.2 Total Profit Card
- **Display Value:** `totalProfit`
- **Data Source:** `data.total_profit` or calculated from `brand_performance`
- **Calculation:**
  ```javascript
  const totalProfit = data?.total_profit ?? brandData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  ```
- **Columns Used:** `Gross_Profit` from `brand_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €35.7M)
- **Additional Display:** Shows `avgMargin.toFixed(1)%` margin

#### 2.3 Active Brands Card
- **Display Value:** `activeBrands`
- **Data Source:** `data.active_brands` or calculated from `brand_performance`
- **Calculation:**
  ```javascript
  const activeBrands = data?.active_brands ?? brandData.filter(item => item && item.Brand && item.Revenue > 0).length;
  ```
- **Columns Used:** `Brand`, `Revenue` from `brand_performance` array
- **Logic:** Counts brands with `Revenue > 0`

#### 2.4 Average Margin
- **Display Value:** `avgMargin`
- **Data Source:** Calculated from `totalRevenue` and `totalProfit`
- **Calculation:**
  ```javascript
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  ```
- **Formula:** `(Total Profit / Total Revenue) × 100`
- **Format:** 1 decimal place (e.g., 30.3%)

---

### Charts and Graphs

#### 2.5 Top Brands by Revenue - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `revenueTop`
- **Data Source:** `brand_performance` array (sorted by Revenue, top 15)
- **X-Axis:** `Brand`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Brand` (labels)
  - `Revenue` (data)
- **Calculation:**
  ```javascript
  const brandData = (data?.brand_performance || []).slice(0, 15);
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 2.6 Brand Revenue Distribution - Doughnut Chart
- **Chart Type:** Doughnut Chart
- **Chart Name:** `revenueDistribution`
- **Data Source:** `brand_performance` array
- **Labels:** `Brand`
- **Data:** `Revenue`
- **Columns Used:**
  - `Brand` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatNumber(value)`

#### 2.7 Top Brands by Profit - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `profitTop`
- **Data Source:** `brand_performance` array (sorted by Gross_Profit)
- **X-Axis:** `Brand`
- **Y-Axis:** `Gross_Profit`
- **Columns Used:**
  - `Brand` (labels)
  - `Gross_Profit` (data)
- **Calculation:**
  ```javascript
  const profitSorted = [...brandData].sort((a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0));
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 2.8 Brand Performance by Business - Bar Chart
- **Chart Type:** Bar Chart (Grouped)
- **Chart Name:** `brandByBusiness`
- **Data Source:** `brand_by_business` array
- **X-Axis:** `Business`
- **Y-Axis:** `Revenue` (grouped by Brand)
- **Columns Used:**
  - `Business` (labels)
  - `Brand` (grouping)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

---

## 3. Customers Analysis

**File:** `frontend/src/pages/CustomerAnalysisNew.js`  
**API Endpoint:** `/analytics/customer-analysis`

### KPI Cards (Summary Metrics)

#### 3.1 Total Revenue Card
- **Display Value:** `totalRevenue`
- **Data Source:** `data.total_revenue` or calculated from `channel_performance`
- **Calculation:**
  ```javascript
  const totalRevenue = data?.total_revenue ?? channelData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  ```
- **Columns Used:** `Revenue` from `channel_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €117.8M)

#### 3.2 Total Profit Card
- **Display Value:** `totalProfit`
- **Data Source:** `data.total_profit` or calculated from `channel_performance`
- **Calculation:**
  ```javascript
  const totalProfit = data?.total_profit ?? channelData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  ```
- **Columns Used:** `Gross_Profit` from `channel_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €35.7M)
- **Additional Display:** Shows `avgMargin.toFixed(1)%` margin

#### 3.3 Total Cases Card
- **Display Value:** `totalUnits`
- **Data Source:** `data.total_units` or calculated from `channel_performance`
- **Calculation:**
  ```javascript
  const totalUnits = data?.total_units ?? channelData.reduce((sum, item) => sum + (item.Units || 0), 0);
  ```
- **Columns Used:** `Units` from `channel_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., 5.9M)

#### 3.4 Active Channels Card
- **Display Value:** `activeChannels`
- **Data Source:** `data.active_channels` or calculated from `channel_performance`
- **Calculation:**
  ```javascript
  const activeChannels = data?.active_channels ?? channelData.filter(item => item && item.Channel && item.Revenue > 0).length;
  ```
- **Columns Used:** `Channel`, `Revenue` from `channel_performance` array
- **Logic:** Counts channels with `Revenue > 0`

#### 3.5 Average Margin
- **Display Value:** `avgMargin`
- **Data Source:** Calculated from `totalRevenue` and `totalProfit`
- **Calculation:**
  ```javascript
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  ```
- **Formula:** `(Total Profit / Total Revenue) × 100`
- **Format:** 1 decimal place (e.g., 30.3%)

---

### Charts and Graphs

#### 3.6 Revenue by Channel - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `revenueByChannel`
- **Data Source:** `channel_performance` array
- **X-Axis:** `Channel`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Channel` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 3.7 Top Customers - Pie Chart
- **Chart Type:** Pie Chart
- **Chart Name:** `topCustomers`
- **Data Source:** `top_customers` array (top 10)
- **Labels:** `Customer`
- **Data:** `Revenue`
- **Columns Used:**
  - `Customer` (labels)
  - `Revenue` (data)
- **Calculation:**
  ```javascript
  const topCustomers = (data?.top_customers || []).slice(0, 10);
  ```
- **Formatting:** Tooltip shows `formatNumber(value)`

#### 3.8 Profit by Channel - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `profitByChannel`
- **Data Source:** `channel_performance` array (sorted by Gross_Profit)
- **X-Axis:** `Channel`
- **Y-Axis:** `Gross_Profit`
- **Columns Used:**
  - `Channel` (labels)
  - `Gross_Profit` (data)
- **Calculation:**
  ```javascript
  const profitSorted = [...channelData].sort((a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0));
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 3.9 Cases by Channel - Doughnut Chart
- **Chart Type:** Doughnut Chart
- **Chart Name:** `unitsByChannel`
- **Data Source:** `channel_performance` array
- **Labels:** `Channel`
- **Data:** `Units`
- **Columns Used:**
  - `Channel` (labels)
  - `Units` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatUnits(value)` with "cases" suffix

---

## 4. Categories Analysis

**File:** `frontend/src/pages/CategoryAnalysisNew.js`  
**API Endpoint:** `/analytics/category-analysis`

### KPI Cards (Summary Metrics)

#### 4.1 Total Revenue Card
- **Display Value:** `totalRevenue`
- **Data Source:** `data.total_revenue` or calculated from `category_performance`
- **Calculation:**
  ```javascript
  const totalRevenue = data?.total_revenue ?? categoryData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  ```
- **Columns Used:** `Revenue` from `category_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €117.8M)

#### 4.2 Total Profit Card
- **Display Value:** `totalProfit`
- **Data Source:** `data.total_profit` or calculated from `category_performance`
- **Calculation:**
  ```javascript
  const totalProfit = data?.total_profit ?? categoryData.reduce((sum, item) => sum + (item.Gross_Profit || 0), 0);
  ```
- **Columns Used:** `Gross_Profit` from `category_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €35.7M)
- **Additional Display:** Shows `avgMargin.toFixed(1)%` margin

#### 4.3 Active Categories Card
- **Display Value:** `activeCategories`
- **Data Source:** `data.active_categories` or calculated from `category_performance`
- **Calculation:**
  ```javascript
  const activeCategories = data?.active_categories ?? categoryData.filter(item => item && item.Category && item.Revenue > 0).length;
  ```
- **Columns Used:** `Category`, `Revenue` from `category_performance` array
- **Logic:** Counts distinct normalized categories with `Revenue > 0`
- **Note:** Categories are normalized (case-insensitive) to handle duplicates like "Compost Sacks" and "Compost sacks"

#### 4.4 Average Margin
- **Display Value:** `avgMargin`
- **Data Source:** Calculated from `totalRevenue` and `totalProfit`
- **Calculation:**
  ```javascript
  const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
  ```
- **Formula:** `(Total Profit / Total Revenue) × 100`
- **Format:** 1 decimal place (e.g., 30.3%)

---

### Charts and Graphs

#### 4.5 Category Revenue - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `categoryRevenue`
- **Data Source:** `category_performance` array (top 15)
- **X-Axis:** `Category`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Category` (labels, normalized)
  - `Revenue` (data)
- **Calculation:**
  ```javascript
  const categoryData = (data?.category_performance || []).slice(0, 15);
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 4.6 Category Distribution - Doughnut Chart
- **Chart Type:** Doughnut Chart
- **Chart Name:** `categoryDistribution`
- **Data Source:** `category_performance` array
- **Labels:** `Category` (normalized)
- **Data:** `Revenue`
- **Columns Used:**
  - `Category` (labels, normalized)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Tooltip shows `formatNumber(value)`

#### 4.7 Category Profit - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `categoryProfit`
- **Data Source:** `category_performance` array (sorted by Gross_Profit)
- **X-Axis:** `Category` (normalized)
- **Y-Axis:** `Gross_Profit`
- **Columns Used:**
  - `Category` (labels, normalized)
  - `Gross_Profit` (data)
- **Calculation:**
  ```javascript
  const profitSorted = [...categoryData].sort((a, b) => (b?.Gross_Profit || 0) - (a?.Gross_Profit || 0));
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 4.8 Sub-Category Revenue - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `subcategoryRevenue`
- **Data Source:** `subcategory_performance` array (top 20)
- **X-Axis:** `Sub_Category`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Sub_Category` (labels)
  - `Revenue` (data)
- **Calculation:**
  ```javascript
  const subCategoryData = (data?.subcategory_performance || []).slice(0, 20);
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

---

## 5. Sales Analysis

**File:** `frontend/src/pages/SalesAnalysis.js`  
**API Endpoint:** `/analytics/executive-overview`

### KPI Cards (Summary Metrics)

#### 5.1 Total Sales Card
- **Display Value:** `totalRevenue`
- **Data Source:** `data.total_revenue` or calculated from `yearly_performance`
- **Calculation:**
  ```javascript
  const totalRevenue = data?.total_revenue ?? yearlyData.reduce((sum, item) => sum + (item.Revenue || 0), 0);
  ```
- **Columns Used:** `Revenue` from `yearly_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., €117.8M)

#### 5.2 Total Cases Card
- **Display Value:** `totalUnits`
- **Data Source:** `data.total_units` or calculated from `yearly_performance`
- **Calculation:**
  ```javascript
  const totalUnits = data?.total_units ?? yearlyData.reduce((sum, item) => sum + (item.Units || 0), 0);
  ```
- **Columns Used:** `Units` from `yearly_performance` array
- **Format:** Formatted using `formatNumber()` (e.g., 5.9M)

#### 5.3 Average Price Card
- **Display Value:** `avgPrice`
- **Data Source:** Calculated from `totalRevenue` and `totalUnits`
- **Calculation:**
  ```javascript
  const avgPrice = totalUnits > 0 ? totalRevenue / totalUnits : 0;
  ```
- **Formula:** `Total Revenue / Total Cases`
- **Columns Used:** `Revenue`, `Units` (aggregated)
- **Format:** Formatted using `formatNumber()` (e.g., €20.0)

---

### Charts and Graphs

#### 5.4 Sales by Year - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `salesByYear`
- **Data Source:** `yearly_performance` array
- **X-Axis:** `Year`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Year` (labels)
  - `Revenue` (data)
- **Calculation:** No calculation, direct mapping
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

#### 5.5 Sales by Business - Bar Chart
- **Chart Type:** Bar Chart
- **Chart Name:** `salesByBusiness`
- **Data Source:** `business_performance` array (filtered: Revenue > 0)
- **X-Axis:** `Business`
- **Y-Axis:** `Revenue`
- **Columns Used:**
  - `Business` (labels)
  - `Revenue` (data)
- **Calculation:**
  ```javascript
  const businessData = (data?.business_performance || []).filter(item => item && item.Business && item.Revenue > 0);
  ```
- **Formatting:** Y-axis uses `formatNumber()` for tooltips

---

## Common Data Structures

### Backend API Response Structure

All screens receive data in a similar structure from their respective endpoints:

```javascript
{
  // Aggregated totals
  total_revenue: number,
  total_profit: number,
  total_units: number,
  
  // Performance arrays
  yearly_performance: [
    { Year: number, Revenue: number, Gross_Profit: number, Units: number }
  ],
  monthly_trend: [
    { Month_Name: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  business_performance: [
    { Business: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  channel_performance: [
    { Channel: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  brand_performance: [
    { Brand: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  category_performance: [
    { Category: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  subcategory_performance: [
    { Sub_Category: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  customer_performance: [
    { Customer: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  top_customers: [
    { Customer: string, Revenue: number, Gross_Profit: number, Units: number }
  ],
  
  // Counts
  active_brands: number,
  active_channels: number,
  active_categories: number
}
```

### Database Column Names

All data originates from MongoDB collection `business_data` with the following columns:

- `Year` - Year (number)
- `Month` - Month (string, e.g., "January", "February")
- `Month_Name` - Month abbreviation (string, e.g., "Jan", "Feb")
- `Business` - Business name (string)
- `Channel` - Sales channel (string)
- `Brand` - Brand name (string)
- `Category` - Product category (string, normalized for case-insensitive matching)
- `Sub_Category` - Product sub-category (string)
- `Customer` - Customer name (string)
- `Revenue` - Total revenue (number)
- `Gross_Profit` - Gross profit (number)
- `Units` - Number of cases/units sold (number)

---

## Common Calculations

### 1. Average Margin
**Formula:** `(Gross Profit / Revenue) × 100`

**Used in:**
- Business Compass (Dashboard)
- Brands Analysis
- Customers Analysis
- Categories Analysis

**Code:**
```javascript
const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
```

### 2. Period Growth (Month-over-Month)
**Formula:** `((Current Period - Previous Period) / Previous Period) × 100`

**Used in:**
- Business Compass (Dashboard) - for Revenue, Profit, and Cases growth

**Code:**
```javascript
const currentPeriod = monthlyData[monthlyData.length - 1];
const previousPeriod = monthlyData[monthlyData.length - 2];
const growth = previousPeriod && previousPeriod.Revenue > 0
  ? ((currentPeriod.Revenue - previousPeriod.Revenue) / previousPeriod.Revenue) * 100
  : 0;
```

### 3. Year-over-Year Growth
**Formula:** `((Latest Year - Previous Year) / Previous Year) × 100`

**Used in:**
- Business Compass (Dashboard) - YoY Growth card (commented out)

**Code:**
```javascript
const sortedYears = [...yearlyData].sort((a, b) => b.Year - a.Year);
const latestYear = sortedYears[0];
const previousYear = sortedYears[1];
const yoyGrowth = previousYear && previousYear.Revenue > 0
  ? ((latestYear.Revenue - previousYear.Revenue) / previousYear.Revenue) * 100
  : 0;
```

### 4. Market Share
**Formula:** `(Business Revenue / Total Market Revenue) × 100`

**Used in:**
- Business Compass (Dashboard) - Market Share card (commented out)

**Code:**
```javascript
const totalMarketRevenue = businessData.reduce((sum, b) => sum + (b.Revenue || 0), 0);
const marketShare = totalMarketRevenue > 0 ? (totalRevenue / totalMarketRevenue) * 100 : 0;
```

### 5. Average Price
**Formula:** `Total Revenue / Total Cases`

**Used in:**
- Sales Analysis

**Code:**
```javascript
const avgPrice = totalUnits > 0 ? totalRevenue / totalUnits : 0;
```

### 6. Expenses Calculation
**Formula:** `Revenue - Gross Profit`

**Used in:**
- Business Compass (Dashboard) - Revenue vs Expenses chart

**Code:**
```javascript
const expenses = item.Revenue - item.Gross_Profit;
```

---

## Formatting Functions

### `formatNumber(value)`
- **Purpose:** Formats large numbers with K, M suffixes
- **Examples:**
  - `117800000` → `€117.8M`
  - `35700000` → `€35.7M`
  - `5900000` → `5.9M`
- **Rules:**
  - Values >= 1,000,000: Shows as `X.XM` (1 decimal place)
  - Values >= 1,000: Shows as `X.XK` (1 decimal place)
  - Values < 1,000: Shows as integer

### `formatUnits(value)`
- **Purpose:** Formats unit/case counts
- **Examples:**
  - `5900000` → `5.9M cases`
  - `1500000` → `1.5M cases`
- **Rules:** Same as `formatNumber()` but with "cases" suffix

### Percentage Formatting
- **Rule:** All percentages use `.toFixed(1)` for 1 decimal place
- **Examples:**
  - `30.303` → `30.3%`
  - `13.517` → `13.5%`
  - `19.237` → `19.2%`

---

## Filter Hierarchy

All screens support:
1. **Global Filters:** Apply to all charts and KPI cards
2. **Individual Chart Filters:** Override global filters for specific charts
3. **Filter Reset:** When global filters change, individual chart filters reset

### Filter Types
- **Year:** Multi-select from available years
- **Month:** Multi-select from available months
- **Business:** Multi-select from available businesses
- **Channel:** Multi-select from available channels
- **Brand:** Multi-select from available brands (Brands, Customers screens)
- **Category:** Multi-select from available categories (Brands, Categories screens)
- **Sub-Category:** Multi-select from available sub-categories (Categories screen)
- **Customer:** Multi-select from available customers (Customers screen)

---

## Data Normalization

### Category Normalization
Categories are normalized to handle case sensitivity issues:

**Function:**
```javascript
function normalize_category_name(category: str) -> str:
    return category.title()  // "Compost Sacks" or "compost sacks" → "Compost Sacks"
```

**Applied in:**
- Categories Analysis screen
- Backend aggregation pipelines
- Filter options

**Purpose:** Ensures "Compost Sacks" and "Compost sacks" are treated as the same category.

---

## Summary

This documentation covers:
- ✅ All KPI card calculations and data sources
- ✅ All chart/graph types, data sources, and column usage
- ✅ All formulas and calculation methods
- ✅ Data structures and API response formats
- ✅ Formatting rules and functions
- ✅ Filter hierarchy and behavior
- ✅ Data normalization logic

**Last Updated:** 2025  
**Status:** ✅ Complete Documentation

