# Customer Deep Intelligence - Column Usage by Graph and Purpose

## Column to Graph/Purpose Mapping

### 1. **New vs Returning Customers** (Donut/Bar Chart)
**Columns Used:**
- `New or returning customer` - Primary grouping column
- `Orders` - Sum of orders by customer type
- `Total sales` - Sum of sales by customer type
- `Customer email` - Count of unique customers by type

**Purpose:** Shows customer acquisition vs retention metrics

---

### 2. **Sales Channel Performance** (Bar Chart)
**Columns Used:**
- `Order or return` - Groups orders vs returns
- `Total sales` - Sales amount by channel
- `Orders` - Order count by channel
- `Customer email` - Unique customer count by channel

**Purpose:** Displays performance of different order types (order vs return)

---

### 3. **Geographic Distribution - Regions** (Bar/Donut Chart)
**Columns Used:**
- `Shipping region` - Primary grouping (e.g., England, Scotland)
- `Total sales` - Sales by region
- `Orders` - Orders by region
- `Customer email` - Unique customers by region

**Purpose:** Shows sales performance by geographic regions

---

### 4. **Traffic Source Analysis** (Bar/Donut Chart)
**Columns Used:**
- `Referring channel` - Traffic source (e.g., google, direct, social)
- `Total sales` - Sales by traffic source
- `Orders` - Orders by traffic source
- `Customer email` - Unique customers by traffic source

**Purpose:** Analyzes which marketing channels drive the most sales

---

### 5. **Customer Lifetime Value (CLV)** (Bar Chart)
**Columns Used:**
- `Customer number of orders` - Bucketed into ranges (1, 2-3, 4-5, 6-10, 11-20, 20+)
- `Total sales` - Total sales per order bucket
- `Customer email` - Unique customers per bucket
- `Orders` - Total orders per bucket

**Purpose:** Shows customer value based on order frequency

---

### 6. **Monthly/Daily Sales Trend** (Line Chart)
**Columns Used:**
- `Day` - Date column (converted to Year, Month, MonthName)
- `Total sales` - Sales aggregated by day/month
- `Orders` - Orders aggregated by day/month
- `Customer email` - Unique customers by time period
- `Orders (first-time)` - First-time orders by time period
- `Orders (returning)` - Returning orders by time period
- `Total sales (previous_month)` - Previous month comparison (if available)
- `Orders (previous_month)` - Previous month orders (if available)
- `Orders first time (previous_month)` - Previous month first-time orders (if available)
- `Orders returning (previous_month)` - Previous month returning orders (if available)

**Purpose:** Shows sales trends over time (daily or monthly view)

---

### 7. **Email Subscription Status** (Donut/Pie Chart)
**Columns Used:**
- `Customer email subscription status` - Groups by SUBSCRIBED/UNSUBSCRIBED/NOT_SUBSCRIBED
- `Customer email` - Unique customer count by status
- `Total sales` - Sales by subscription status
- `Orders` - Orders by subscription status

**Purpose:** Shows email marketing subscription rates and performance

---

### 8. **Top Customers Table** (Data Table)
**Columns Used:**
- `Customer email` - Customer identifier
- `Customer name` - Customer name
- `Total sales` - Total sales per customer
- `Orders` - Total orders per customer
- `Customer number of orders` - Lifetime order count

**Purpose:** Lists top 20 customers by sales performance

---

### 9. **Platform Analysis** (Bar/Donut Chart)
**Columns Used:**
- `Referring platform` - Platform name (e.g., alphabet for Google, facebook)
- `Total sales` - Sales by platform
- `Orders` - Orders by platform
- `Customer email` - Unique customers by platform

**Purpose:** Shows which platforms drive the most traffic and sales

---

### 10. **Traffic Type Performance** (Bar/Donut Chart)
**Columns Used:**
- `Traffic type` - Traffic classification (e.g., paid, organic, direct)
- `Total sales` - Sales by traffic type
- `Orders` - Orders by traffic type
- `Customer email` - Unique customers by traffic type

**Purpose:** Analyzes paid vs organic vs direct traffic performance

---

### 11. **Hour of Day Shopping Patterns** (Line Chart)
**Columns Used:**
- `Hour of day` - Hour (0-23)
- `Total sales` - Sales aggregated by hour
- `Orders` - Orders aggregated by hour
- `Customer email` - Unique customers by hour

**Purpose:** Shows peak shopping hours throughout the day

---

### 12. **Country Distribution** (Donut/Pie Chart)
**Columns Used:**
- `Shipping country` - Country name
- `Total sales` - Sales by country
- `Orders` - Orders by country
- `Customer email` - Unique customers by country

**Purpose:** Shows geographic distribution of customers and sales by country

---

### 13. **SMS Subscription Status** (Donut/Pie Chart)
**Columns Used:**
- `Customer SMS subscription status` - Groups by SUBSCRIBED/UNSUBSCRIBED/NOT_SUBSCRIBED
- `Customer email` - Unique customer count by status
- `Total sales` - Sales by SMS subscription status
- `Orders` - Orders by SMS subscription status

**Purpose:** Shows SMS marketing subscription rates and performance

---

### 14. **Order vs Return Analysis** (Bar Chart)
**Columns Used:**
- `Order or return` - Groups orders vs returns
- `Total sales` - Sales by type
- `Orders` - Order count by type
- `Net returns` - Net return amount
- `Total returns` - Total return amount

**Purpose:** Compares order volume vs return volume

---

### 15. **Referring Medium Analysis** (Bar/Donut Chart)
**Columns Used:**
- `Referring medium` - Traffic medium (e.g., search, referral, email)
- `Total sales` - Sales by medium
- `Orders` - Orders by medium
- `Customer email` - Unique customers by medium

**Purpose:** Analyzes which traffic mediums perform best

---

### 16. **Top Products by Sales** (Bar Chart)
**Columns Used:**
- `Product variant SKU` - Product SKU identifier
- `Total sales` - Sales per product
- `Orders` - Orders per product
- `Quantity ordered` - Total quantity sold per product

**Purpose:** Shows top 15 best-selling products

---

### 17. **Day of Week Analysis** (Bar Chart)
**Columns Used:**
- `Day` - Date column (derived to DayOfWeek: Monday-Sunday)
- `Total sales` - Sales by day of week
- `Orders` - Orders by day of week
- `Customer email` - Unique customers by day of week

**Purpose:** Shows which days of the week have highest sales

---

### 18. **Return Rate Trend** (Line Chart)
**Columns Used:**
- `Day` - Date column (converted to Year, Month)
- `Order or return` - Filters for 'return' records
- `Total returns` - Return amount by month
- `Orders` - Return order count by month
- `Total sales` - Used to calculate return rate percentage

**Purpose:** Shows return rate trends over time

---

### 19. **Daily Sales & Customer Trends** (Mixed Line/Bar Chart)
**Columns Used:**
- `Day` - Date column
- `Total sales` - Sales line
- `Orders (first-time)` - New customer orders (bar)
- `Orders (returning)` - Returning customer orders (bar)

**Purpose:** Combined view of sales trends with new vs returning customer orders

---

## Summary Statistics (Used in KPI Cards and Chatbot)

**Columns Used:**
- `Customer email` - Total unique customers (nunique)
- `Orders` - Total orders (sum)
- `Total sales` - Total sales (sum)
- `New or returning customer` - Count of new vs returning customers

**Calculated Metrics:**
- Average Order Value = Total sales / Total orders
- Returning Customer Rate = Returning customers / Total customers * 100

---

## Chatbot Context (AI Assistant)

**All columns listed above are used** to build comprehensive context for the AI chatbot, including:
- Data overview (totals, averages)
- Customer segmentation metrics
- Channel performance summaries
- Geographic distribution summaries
- Subscription status summaries
- Time-based pattern summaries (hourly, monthly)
- Peak hours and top performing periods

The chatbot can answer questions about any of these metrics and provide insights based on the data.

---

## Column Usage Summary

**Most Frequently Used Columns:**
1. `Customer email` - Used in 18+ analyses (unique customer counting)
2. `Total sales` - Used in 18+ analyses (primary sales metric)
3. `Orders` - Used in 18+ analyses (primary order metric)
4. `Day` - Used in 6+ time-based analyses
5. `New or returning customer` - Used in 3+ customer segmentation analyses
6. `Orders (first-time)` - Used in 3+ trend analyses
7. `Orders (returning)` - Used in 3+ trend analyses

**Special Purpose Columns:**
- `Hour of day` - Only for hourly pattern analysis
- `Customer number of orders` - Only for CLV analysis
- `Product variant SKU` - Only for product analysis
- `Order or return` - Only for order/return comparison
- `Net returns` / `Total returns` - Only for return analysis

