# Shopify_customer_df.csv - Columns Used in Backend API and Chatbot

## Complete List of Columns Used

### 1. Date/Time Columns
- **Day** - Primary date column (used to derive Year, Month, MonthName)
- **Hour of day** - Used for hourly shopping pattern analysis
- **Month** - Derived from Day column

### 2. Sales & Financial Columns
- **Net sales** - Net sales amount
- **Gross sales** - Gross sales amount  
- **Total sales** - Total sales amount (most frequently used)
- **Total sales (previous_month)** - Previous month sales comparison (if available)
- **Orders (previous_month)** - Previous month orders (if available)
- **Orders first time (previous_month)** - Previous month first-time orders (if available)
- **Orders returning (previous_month)** - Previous month returning orders (if available)

### 3. Order Columns
- **Orders** - Total number of orders
- **Orders (first-time)** - First-time customer orders
- **Orders (returning)** - Returning customer orders
- **Order or return** - Distinguishes between orders and returns

### 4. Customer Columns
- **Customer email** - Unique customer identifier (used for counting unique customers)
- **Customer name** - Customer name
- **Customer number of orders** - Lifetime order count per customer (used for CLV analysis)
- **New or returning customer** - Customer type classification
- **Customers** - Customer count
- **New customers** - New customer count
- **Returning customers** - Returning customer count
- **Returning customer rate** - Percentage of returning customers

### 5. Channel & Traffic Columns
- **Referring channel** - Traffic source channel (e.g., google, direct, social)
- **Referring platform** - Specific platform (e.g., alphabet for Google)
- **Referring medium** - Traffic medium
- **Traffic type** - Type of traffic (e.g., paid, organic)

### 6. Geographic Columns
- **Shipping country** - Customer country
- **Shipping region** - Customer region/state
- **Shipping postal code** - Postal/ZIP code
- **Shipping city** - Customer city

### 7. Subscription Columns
- **Customer email subscription status** - Email subscription status (SUBSCRIBED/UNSUBSCRIBED/NOT_SUBSCRIBED)
- **Customer SMS subscription status** - SMS subscription status (SUBSCRIBED/UNSUBSCRIBED/NOT_SUBSCRIBED)

### 8. Product Columns
- **Product variant SKU** - Product SKU identifier

### 9. Quantity Columns
- **Quantity ordered** - Number of items ordered
- **Quantity returned** - Number of items returned

### 10. Returns Columns
- **Net returns** - Net return amount
- **Total returns** - Total return amount

## Columns Used in Chatbot Context (customer_insights_chat endpoint)

The chatbot uses these columns to build comprehensive context for AI responses:

1. **Day** - For date processing and trend analysis
2. **Customer email** - For unique customer counting
3. **Orders** - For order statistics
4. **Total sales** - For sales calculations
5. **New or returning customer** - For customer segmentation
6. **Referring channel** - For channel performance analysis
7. **Referring platform** - For platform analysis
8. **Traffic type** - For traffic source analysis
9. **Shipping country** - For geographic distribution
10. **Shipping region** - For regional analysis
11. **Customer email subscription status** - For subscription metrics
12. **Customer SMS subscription status** - For SMS subscription metrics
13. **Hour of day** - For hourly pattern analysis
14. **Orders (first-time)** - For new customer analysis
15. **Orders (returning)** - For returning customer analysis
16. **Customer number of orders** - For customer lifetime value

## Columns Used in GET Endpoint (get_customer_insights)

The GET endpoint uses additional columns for data visualization:

1. All columns listed above
2. **Order or return** - For channel performance visualization
3. **Product variant SKU** - For product analysis (if needed)
4. **Quantity ordered** - For quantity metrics
5. **Quantity returned** - For return analysis
6. **Net returns** - For return value analysis
7. **Total returns** - For total return metrics
8. **Gross sales** - For gross sales calculations
9. **Net sales** - For net sales calculations

## Derived Columns (Created in Code)

These columns are created from existing columns during processing:

- **Year** - Derived from Day
- **Month** - Derived from Day  
- **MonthName** - Derived from Day (e.g., "January", "February")
- **month_label** - Formatted month label (e.g., "January 2025")
- **day_label** - Formatted day label (e.g., "Jan 01, 2025")

## Summary

**Total columns directly used from CSV: ~25-30 columns**
**Derived columns created: 5-6 columns**

The backend processes these columns to provide:
- Customer analytics and insights
- Sales performance metrics
- Geographic distribution analysis
- Channel and traffic source analysis
- Time-based pattern analysis (hourly, daily, monthly)
- Customer segmentation (new vs returning)
- Subscription status tracking
- Customer lifetime value analysis

