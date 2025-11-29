import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from openai import OpenAI
import numpy as np
from datetime import datetime, timedelta
import io

# Page configuration
st.set_page_config(
    page_title="Shopify AI Analytics Bot Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
    }
    .ai-response {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .success-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-left: 1rem;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ShopifyDataProcessor:
    def __init__(self, file_path):
        # Load data from predefined CSV path
        self.df = pd.read_csv(file_path)
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess the Shopify data"""
        # Convert date column
        self.df['Day'] = pd.to_datetime(self.df['Day'])
        
        # Extract date components
        self.df['Date'] = self.df['Day'].dt.date
        self.df['Month'] = self.df['Day'].dt.month_name()
        self.df['Month_Num'] = self.df['Day'].dt.month
        self.df['Year'] = self.df['Day'].dt.year
        self.df['YearMonth'] = self.df['Day'].dt.to_period('M')
        self.df['DayOfWeek'] = self.df['Day'].dt.day_name()
        self.df['Week'] = self.df['Day'].dt.isocalendar().week
        
        # Calculate additional metrics
        self.df['Conversion_Rate'] = self.df['Orders'] / self.df['Customers']
        self.df['Avg_Order_Value'] = self.df['Total sales'] / self.df['Orders']
        
        # Fill NaN values
        self.df['Conversion_Rate'] = self.df['Conversion_Rate'].fillna(0)
        self.df['Avg_Order_Value'] = self.df['Avg_Order_Value'].fillna(0)
    
    def get_filtered_data(self, start_date=None, end_date=None, channel=None, customer_type=None, month=None, year=None):
        """Filter data based on user selections"""
        filtered_df = self.df.copy()
        
        # Date filter
        if start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) & 
                (filtered_df['Date'] <= end_date)
            ]
        
        # Month filter
        if month and month != 'All':
            filtered_df = filtered_df[filtered_df['Month'] == month]
        
        # Year filter
        if year and year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == year]
        
        # Channel filter
        if channel and channel != 'All':
            filtered_df = filtered_df[filtered_df['Referring channel'] == channel]
        
        # Customer type filter
        if customer_type and customer_type != 'All':
            filtered_df = filtered_df[filtered_df['New or returning customer'] == customer_type]
        
        return filtered_df

    def get_summary_stats(self, filtered_df=None):
        """Get overall summary statistics"""
        if filtered_df is None:
            filtered_df = self.df
        
        total_orders = filtered_df['Orders'].sum()
        total_sales = filtered_df['Total sales'].sum()
        total_customers = filtered_df['Customers'].sum()
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'total_sales': round(total_sales, 2),
            'total_customers': total_customers,
            'avg_order_value': round(avg_order_value, 2),
            'returning_customer_rate': round(filtered_df['Returning customer rate'].mean() * 100, 2),
            'data_points': len(filtered_df)
        }

    # NEW: Month-level analysis methods
    def get_monthly_sales(self, filtered_df=None):
        """Get sales by month"""
        if filtered_df is None:
            filtered_df = self.df
        
        monthly_sales = filtered_df.groupby(['Year', 'Month', 'Month_Num']).agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customers': 'sum',
            'Gross sales': 'sum',
            'Net sales': 'sum'
        }).reset_index().sort_values(['Year', 'Month_Num'])
        
        return monthly_sales

    def get_sales_by_month(self, month_name, year=None):
        """Get sales for specific month"""
        filtered_df = self.df[self.df['Month'] == month_name]
        if year:
            filtered_df = filtered_df[filtered_df['Year'] == year]
        
        return self.get_summary_stats(filtered_df)

    def get_all_months_data(self):
        """Get data for all months available"""
        monthly_data = self.get_monthly_sales()
        return monthly_data

    # 1. ADVANCED ANALYTICS & METRICS
    def get_advanced_metrics(self, filtered_df=None):
        """Calculate advanced business metrics"""
        if filtered_df is None:
            filtered_df = self.df
        
        # Customer Lifetime Value
        customer_sales = filtered_df.groupby('Customer email')['Total sales'].sum()
        clv = customer_sales.mean() if len(customer_sales) > 0 else 0
        
        # Customer Acquisition Cost (simulated)
        total_marketing_spend = filtered_df['Total sales'].sum() * 0.2  # 20% of sales
        cac = total_marketing_spend / filtered_df['Customers'].sum() if filtered_df['Customers'].sum() > 0 else 0
        
        # Retention Rate
        returning_customers = filtered_df[filtered_df['New or returning customer'] == 'Returning']['Customers'].sum()
        retention_rate = (returning_customers / filtered_df['Customers'].sum()) * 100 if filtered_df['Customers'].sum() > 0 else 0
        
        # Churn Rate
        churn_rate = 100 - retention_rate
        
        # Repeat Purchase Rate
        repeat_customers = filtered_df[filtered_df['New or returning customer'] == 'Returning']['Customer email'].nunique()
        total_customers = filtered_df['Customer email'].nunique()
        repeat_rate = (repeat_customers / total_customers) * 100 if total_customers > 0 else 0
        
        return {
            'customer_lifetime_value': round(clv, 2),
            'customer_acquisition_cost': round(cac, 2),
            'retention_rate': round(retention_rate, 2),
            'churn_rate': round(churn_rate, 2),
            'repeat_purchase_rate': round(repeat_rate, 2),
            'clv_to_cac_ratio': round(clv/cac, 2) if cac > 0 else 0
        }

    # 5. CUSTOMER SEGMENTATION
    def get_customer_segments(self, filtered_df=None):
        """Segment customers based on behavior"""
        if filtered_df is None:
            filtered_df = self.df
        
        customer_data = filtered_df.groupby('Customer email').agg({
            'Total sales': 'sum',
            'Orders': 'count',
            'Date': 'max',
            'New or returning customer': 'first',
            'Shipping country': 'first'
        }).reset_index()
        
        # RFM-like Segmentation
        segments = []
        for _, customer in customer_data.iterrows():
            recency = (pd.Timestamp.now().normalize() - pd.to_datetime(customer['Date'])).days
            
            if customer['Total sales'] > 500 and customer['Orders'] > 5 and recency < 30:
                segments.append('VIP')
            elif customer['Total sales'] > 200 and customer['Orders'] > 2 and recency < 60:
                segments.append('Loyal')
            elif customer['New or returning customer'] == 'New':
                segments.append('New')
            elif recency > 90:
                segments.append('At Risk')
            else:
                segments.append('Regular')
        
        customer_data['segment'] = segments
        return customer_data

    def get_segmentation_insights(self, filtered_df=None):
        """Get insights from customer segmentation"""
        segments_df = self.get_customer_segments(filtered_df)
        segment_summary = segments_df['segment'].value_counts()
        
        segment_value = segments_df.groupby('segment')['Total sales'].sum()
        avg_order_by_segment = segments_df.groupby('segment')['Orders'].mean()
        
        return {
            'segment_distribution': segment_summary.to_dict(),
            'segment_value': segment_value.to_dict(),
            'avg_orders_per_segment': avg_order_by_segment.to_dict()
        }

    def get_sales_trend(self, filtered_df=None):
        """Get daily sales trend"""
        if filtered_df is None:
            filtered_df = self.df
        
        daily_sales = filtered_df.groupby('Date').agg({
            'Total sales': 'sum',
            'Orders': 'sum',
            'Customers': 'sum',
            'New customers': 'sum'
        }).reset_index()
        return daily_sales

    def get_channel_performance(self, filtered_df=None):
        """Get performance by referring channel"""
        if filtered_df is None:
            filtered_df = self.df
        
        channel_perf = filtered_df.groupby('Referring channel').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Customers': 'sum'
        }).reset_index()
        channel_perf['Conversion_Rate'] = (channel_perf['Orders'] / channel_perf['Customers']).fillna(0)
        return channel_perf

    def get_product_performance(self, filtered_df=None):
        """Get performance by product variant"""
        if filtered_df is None:
            filtered_df = self.df
        
        product_perf = filtered_df.groupby('Product variant SKU').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Quantity ordered': 'sum'
        }).reset_index()
        return product_perf.sort_values('Total sales', ascending=False).head(10)

    def get_geographic_insights(self, filtered_df=None):
        """Get insights by shipping country and city"""
        if filtered_df is None:
            filtered_df = self.df
        
        geo_insights = filtered_df.groupby('Shipping country').agg({
            'Orders': 'sum',
            'Total sales': 'sum',
            'Customers': 'sum'
        }).reset_index()
        return geo_insights

    def create_sales_dashboard(self, filtered_df=None):
        """Create comprehensive sales dashboard with separate charts"""
        if filtered_df is None:
            filtered_df = self.df
        
        # Create individual charts instead of subplots
        charts = {}
        
        # Daily sales trend
        daily_sales = self.get_sales_trend(filtered_df)
        fig_daily = px.line(daily_sales, x='Date', y='Total sales', 
                           title='Daily Sales Trend', labels={'Total sales': 'Sales ($)'})
        fig_daily.update_traces(line=dict(color='blue', width=3))
        charts['daily_sales'] = fig_daily
        
        # Channel performance
        channel_perf = self.get_channel_performance(filtered_df)
        fig_channel = px.bar(channel_perf, x='Referring channel', y='Total sales',
                            title='Sales by Marketing Channel', color='Conversion_Rate',
                            labels={'Total sales': 'Sales ($)', 'Conversion_Rate': 'Conversion Rate'})
        charts['channel_performance'] = fig_channel
        
        # Monthly sales trend
        monthly_sales = self.get_monthly_sales(filtered_df)
        monthly_sales['YearMonth'] = monthly_sales['Year'].astype(str) + '-' + monthly_sales['Month']
        fig_monthly = px.line(monthly_sales, x='YearMonth', y='Total sales',
                             title='Monthly Sales Trend', labels={'Total sales': 'Sales ($)'})
        fig_monthly.update_traces(line=dict(color='green', width=3))
        charts['monthly_sales'] = fig_monthly
        
        # Customer type distribution
        customer_type = filtered_df['New or returning customer'].value_counts()
        fig_customer = px.pie(values=customer_type.values, names=customer_type.index,
                             title='Customer Type Distribution')
        charts['customer_type'] = fig_customer
        
        return charts

    # 7. EXPORT & REPORTING FEATURES
    def generate_report(self, report_type='executive', filtered_df=None):
        """Generate different types of reports"""
        if filtered_df is None:
            filtered_df = self.df
        
        if report_type == 'executive':
            return self._generate_executive_summary(filtered_df)
        elif report_type == 'detailed':
            return self._generate_detailed_analysis(filtered_df)
        elif report_type == 'marketing':
            return self._generate_marketing_insights(filtered_df)

    def _generate_executive_summary(self, filtered_df):
        """Generate executive summary report"""
        basic_metrics = self.get_summary_stats(filtered_df)
        advanced_metrics = self.get_advanced_metrics(filtered_df)
        segmentation = self.get_segmentation_insights(filtered_df)
        monthly_data = self.get_monthly_sales(filtered_df)
        
        report = f"""
SHOPIFY ANALYTICS EXECUTIVE REPORT
==================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Period: {filtered_df['Date'].min()} to {filtered_df['Date'].max()}
Data Points: {basic_metrics['data_points']:,}

PERFORMANCE OVERVIEW
--------------------
• Total Sales: ${basic_metrics['total_sales']:,.2f}
• Total Orders: {basic_metrics['total_orders']:,}
• Total Customers: {basic_metrics['total_customers']:,}
• Average Order Value: ${basic_metrics['avg_order_value']:,.2f}
• Returning Customer Rate: {basic_metrics['returning_customer_rate']}%

MONTHLY PERFORMANCE
-------------------
{chr(10).join([f"• {row['Year']}-{row['Month']}: ${row['Total sales']:,.2f} ({row['Orders']} orders)" for _, row in monthly_data.iterrows()])}

ADVANCED METRICS
----------------
• Customer Lifetime Value: ${advanced_metrics['customer_lifetime_value']:,.2f}
• Customer Acquisition Cost: ${advanced_metrics['customer_acquisition_cost']:,.2f}
• Retention Rate: {advanced_metrics['retention_rate']}%
• Repeat Purchase Rate: {advanced_metrics['repeat_purchase_rate']}%
• CLV to CAC Ratio: {advanced_metrics['clv_to_cac_ratio']:,.1f}

CUSTOMER SEGMENTATION
---------------------
{chr(10).join([f"• {segment}: {count} customers (${segmentation['segment_value'].get(segment, 0):,.2f} value)" for segment, count in segmentation['segment_distribution'].items()])}

TOP PERFORMING CHANNELS
-----------------------
{chr(10).join([f"• {row['Referring channel']}: ${row['Total sales']:,.2f} ({row['Conversion_Rate']:.1%} conversion)" for _, row in self.get_channel_performance(filtered_df).head(3).iterrows()])}

KEY RECOMMENDATIONS
-------------------
• Focus on retaining {max(segmentation['segment_distribution'], key=segmentation['segment_distribution'].get)} segment
• Optimize {self.get_channel_performance(filtered_df).iloc[0]['Referring channel']} channel performance
• Improve customer retention strategies
• Monitor customer acquisition costs
        """
        return report

    def _generate_detailed_analysis(self, filtered_df):
        """Generate detailed analysis report"""
        basic_metrics = self.get_summary_stats(filtered_df)
        advanced_metrics = self.get_advanced_metrics(filtered_df)
        channels = self.get_channel_performance(filtered_df)
        products = self.get_product_performance(filtered_df)
        geography = self.get_geographic_insights(filtered_df)
        monthly_data = self.get_monthly_sales(filtered_df)
        
        report = f"""
DETAILED SHOPIFY ANALYSIS REPORT
================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Period: {filtered_df['Date'].min()} to {filtered_df['Date'].max()}

BASIC METRICS
-------------
{chr(10).join([f"• {k.replace('_', ' ').title()}: {v}" for k, v in basic_metrics.items()])}

MONTHLY BREAKDOWN
-----------------
{chr(10).join([f"• {row['Year']}-{row['Month']}: ${row['Total sales']:,.2f} | {row['Orders']} orders | {row['Customers']} customers" for _, row in monthly_data.iterrows()])}

ADVANCED METRICS
----------------
{chr(10).join([f"• {k.replace('_', ' ').title()}: {v}" for k, v in advanced_metrics.items()])}

CHANNEL PERFORMANCE
-------------------
{chr(10).join([f"• {row['Referring channel']}: ${row['Total sales']:,.2f} | {row['Orders']} orders | {row['Conversion_Rate']:.1%} conversion" for _, row in channels.iterrows()])}

TOP PRODUCTS
------------
{chr(10).join([f"• SKU {row['Product variant SKU']}: ${row['Total sales']:,.2f} | {row['Orders']} orders | {row['Quantity ordered']} units" for _, row in products.head(5).iterrows()])}

GEOGRAPHIC DISTRIBUTION
-----------------------
{chr(10).join([f"• {row['Shipping country']}: ${row['Total sales']:,.2f} | {row['Orders']} orders" for _, row in geography.iterrows()])}
        """
        return report

    def _generate_marketing_insights(self, filtered_df):
        """Generate marketing insights report"""
        basic_metrics = self.get_summary_stats(filtered_df)
        advanced_metrics = self.get_advanced_metrics(filtered_df)
        channels = self.get_channel_performance(filtered_df)
        segmentation = self.get_segmentation_insights(filtered_df)
        monthly_data = self.get_monthly_sales(filtered_df)
        
        report = f"""
MARKETING INSIGHTS REPORT
=========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

MONTHLY PERFORMANCE TREND
-------------------------
{chr(10).join([f"• {row['Year']}-{row['Month']}: ${row['Total sales']:,.2f} | {row['Customers']} customers" for _, row in monthly_data.iterrows()])}

MARKETING PERFORMANCE
---------------------
• Total Marketing ROI: {advanced_metrics['clv_to_cac_ratio']:,.1f}x
• Customer Acquisition Cost: ${advanced_metrics['customer_acquisition_cost']:,.2f}
• Retention Rate: {advanced_metrics['retention_rate']}%
• Repeat Purchase Rate: {advanced_metrics['repeat_purchase_rate']}%

CHANNEL EFFECTIVENESS
---------------------
{chr(10).join([f"• {row['Referring channel']}: Conversion Rate {row['Conversion_Rate']:.1%} | ${row['Total sales']:,.2f} revenue" for _, row in channels.iterrows()])}

CUSTOMER SEGMENT STRATEGY
-------------------------
{chr(10).join([f"• {segment}: {count} customers | Average {segmentation['avg_orders_per_segment'].get(segment, 0):.1f} orders each" for segment, count in segmentation['segment_distribution'].items()])}

RECOMMENDED ACTIONS
-------------------
1. Focus budget on {channels.iloc[0]['Referring channel']} (highest converting channel)
2. Develop retention campaigns for {max(segmentation['segment_distribution'], key=segmentation['segment_distribution'].get)} segment
3. Optimize acquisition strategy to reduce CAC
4. Implement loyalty program for repeat purchases
        """
        return report

class ShopifyAIBot:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
    
    def query_ai(self, user_question, context_data):
        """Query Perplexity AI with context from Shopify data"""
        
        system_prompt = """You are an expert Shopify data analyst. Use the provided data context to answer questions about sales performance, customer behavior, and business insights. Be precise, data-driven, and provide actionable recommendations when appropriate. Always reference specific numbers from the data when available. When asked about specific months, use the monthly sales data provided."""

        user_prompt = f"""
        Shopify Data Context:
        - Total Records: {context_data['summary']['data_points']:,}
        - Total Sales: ${context_data['summary']['total_sales']:,.2f}
        - Total Orders: {context_data['summary']['total_orders']:,}
        - Total Customers: {context_data['summary']['total_customers']:,}
        - Average Order Value: ${context_data['summary']['avg_order_value']:,.2f}
        - Returning Customer Rate: {context_data['summary']['returning_customer_rate']}%
        
        Advanced Metrics:
        - Customer Lifetime Value: ${context_data['advanced']['customer_lifetime_value']:,.2f}
        - Retention Rate: {context_data['advanced']['retention_rate']}%
        - CLV to CAC Ratio: {context_data['advanced']['clv_to_cac_ratio']:,.1f}
        
        Monthly Sales Data:
        {context_data['monthly_data'].to_string() if not context_data['monthly_data'].empty else 'No monthly data available'}
        
        Customer Segments:
        {context_data['segmentation']}
        
        Top Performing Channels:
        {context_data['channels'].to_string()}
        
        User Question: {user_question}
        
        Please provide a comprehensive answer based on this data. Include specific numbers and insights where available. If the question asks about a specific month, use the monthly sales data provided.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error querying AI: {str(e)}"

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 Shopify AI Analytics Bot Pro</h1>', unsafe_allow_html=True)
    
    # HARDCODED CONFIGURATION - UPDATE THESE VALUES
    # ==============================================
    DATA_FILE_PATH = r"C:\Users\Sumit Mishra\Downloads\shopify_data.csv"  
    PERPLEXITY_API_KEY = "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5"  
    
    # Initialize configuration
    try:
        # Initialize data processor
        processor = ShopifyDataProcessor(DATA_FILE_PATH)
        
        # Initialize AI bot
        ai_bot = ShopifyAIBot(PERPLEXITY_API_KEY)
        
        # Show success status
        st.success("✅ System initialized successfully - AI Bot Pro Ready!")
        
    except FileNotFoundError:
        st.error(f"❌ Data file not found at: {DATA_FILE_PATH}")
        st.info("Please update the DATA_FILE_PATH in the code with your actual CSV file path.")
        return
    except Exception as e:
        st.error(f"❌ Initialization Error: {str(e)}")
        st.info("Please check your file path and API key configuration.")
        return

    # 8. INTERACTIVE FILTERS & DATE RANGE SELECTOR
    st.sidebar.header("🔧 Filters & Controls")
    
    # Date range selector
    st.sidebar.subheader("📅 Date Range Filter")
    min_date = processor.df['Date'].min()
    max_date = processor.df['Date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Month filter
    st.sidebar.subheader("📆 Month Filter")
    all_months = ['All'] + sorted(processor.df['Month'].unique(), key=lambda x: pd.to_datetime(x, format='%B').month)
    selected_month = st.sidebar.selectbox("Select Month", all_months)
    
    # Year filter
    st.sidebar.subheader("📅 Year Filter")
    all_years = ['All'] + sorted(processor.df['Year'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Select Year", all_years)
    
    # Channel filter
    st.sidebar.subheader("📊 Channel Filter")
    all_channels = ['All'] + processor.df['Referring channel'].unique().tolist()
    selected_channel = st.sidebar.selectbox("Select Channel", all_channels)
    
    # Customer type filter
    st.sidebar.subheader("👥 Customer Type")
    customer_types = ['All'] + processor.df['New or returning customer'].unique().tolist()
    selected_customer_type = st.sidebar.selectbox("Filter by Customer Type", customer_types)
    
    # Apply filters
    start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
    filtered_data = processor.get_filtered_data(
        start_date=start_date,
        end_date=end_date,
        channel=selected_channel,
        customer_type=selected_customer_type,
        month=selected_month,
        year=selected_year
    )
    
    # Main dashboard with filtered data
    col1, col2, col3, col4 = st.columns(4)
    
    summary = processor.get_summary_stats(filtered_data)
    
    with col1:
        st.metric("Total Sales", f"${summary['total_sales']:,.2f}")
    with col2:
        st.metric("Total Orders", f"{summary['total_orders']:,}")
    with col3:
        st.metric("Avg Order Value", f"${summary['avg_order_value']:,.2f}")
    with col4:
        st.metric("Returning Customers", f"{summary['returning_customer_rate']}%")
    
    # 1. ADVANCED ANALYTICS & METRICS
    st.subheader("📈 Advanced Business Metrics")
    adv_col1, adv_col2, adv_col3, adv_col4 = st.columns(4)
    
    advanced_metrics = processor.get_advanced_metrics(filtered_data)
    
    with adv_col1:
        st.metric("Customer Lifetime Value", f"${advanced_metrics['customer_lifetime_value']:,.2f}")
    with adv_col2:
        st.metric("Customer Acquisition Cost", f"${advanced_metrics['customer_acquisition_cost']:,.2f}")
    with adv_col3:
        st.metric("Retention Rate", f"{advanced_metrics['retention_rate']}%")
    with adv_col4:
        st.metric("CLV to CAC Ratio", f"{advanced_metrics['clv_to_cac_ratio']:.1f}")
    
    # Display dashboard with filtered data
    st.subheader("📊 Analytics Dashboard")
    
    # Create and display individual charts in a grid layout
    charts = processor.create_sales_dashboard(filtered_data)
    
    # First row: Daily sales and Channel performance
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts['daily_sales'], use_container_width=True)
    with col2:
        st.plotly_chart(charts['channel_performance'], use_container_width=True)
    
    # Second row: Monthly sales and Customer type
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts['monthly_sales'], use_container_width=True)
    with col2:
        st.plotly_chart(charts['customer_type'], use_container_width=True)
    
    # 5. CUSTOMER SEGMENTATION
    st.subheader("👥 Customer Segmentation Analysis")
    
    seg_col1, seg_col2 = st.columns(2)
    
    with seg_col1:
        segmentation = processor.get_segmentation_insights(filtered_data)
        fig_seg = px.pie(
            values=list(segmentation['segment_distribution'].values()),
            names=list(segmentation['segment_distribution'].keys()),
            title='Customer Segment Distribution'
        )
        st.plotly_chart(fig_seg, use_container_width=True)
    
    with seg_col2:
        st.subheader("Segment Value Analysis")
        for segment, value in segmentation['segment_value'].items():
            st.metric(f"{segment} Customers Value", f"${value:,.2f}")
    
    # Additional insights in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Channel Performance", "Product Insights", "Geographic Analysis", "Monthly Analysis"])
    
    with tab1:
        channel_data = processor.get_channel_performance(filtered_data)
        fig_channel = px.bar(channel_data, x='Referring channel', y='Total sales', 
                            title='Sales by Marketing Channel', color='Conversion_Rate')
        st.plotly_chart(fig_channel, use_container_width=True)
    
    with tab2:
        product_data = processor.get_product_performance(filtered_data)
        fig_product = px.bar(product_data, x='Product variant SKU', y='Total sales',
                            title='Top 10 Products by Sales')
        st.plotly_chart(fig_product, use_container_width=True)
    
    with tab3:
        geo_data = processor.get_geographic_insights(filtered_data)
        fig_geo = px.pie(geo_data, values='Total sales', names='Shipping country',
                        title='Sales Distribution by Country')
        st.plotly_chart(fig_geo, use_container_width=True)
    
    with tab4:
        monthly_data = processor.get_monthly_sales(filtered_data)
        fig_monthly_bar = px.bar(monthly_data, x='Month', y='Total sales', 
                                title='Monthly Sales Breakdown', color='Year')
        st.plotly_chart(fig_monthly_bar, use_container_width=True)
        
        # Show monthly data table
        st.subheader("Monthly Sales Data")
        st.dataframe(monthly_data[['Year', 'Month', 'Total sales', 'Orders', 'Customers']])
    
    # 7. EXPORT & REPORTING FEATURES
    st.sidebar.header("📤 Export & Reports")
    
    report_type = st.sidebar.selectbox(
        "Select Report Type",
        ["executive", "detailed", "marketing"]
    )
    
    if st.sidebar.button("📄 Generate Report"):
        with st.spinner("Generating report..."):
            report = processor.generate_report(report_type, filtered_data)
            st.sidebar.download_button(
                "📥 Download Report",
                report,
                file_name=f"shopify_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    # AI Chat Section
    st.subheader("💬 AI Analytics Assistant")
    
    # Prepare context data for AI - NOW INCLUDES MONTHLY DATA
    context_data = {
        'summary': processor.get_summary_stats(filtered_data),
        'advanced': processor.get_advanced_metrics(filtered_data),
        'segmentation': processor.get_segmentation_insights(filtered_data),
        'channels': processor.get_channel_performance(filtered_data),
        'products': processor.get_product_performance(filtered_data),
        'monthly_data': processor.get_monthly_sales(filtered_data),
        'recent_sales': processor.get_sales_trend(filtered_data).tail()
    }
    
    # Chat interface
    user_question = st.text_input(
        "Ask me anything about your Shopify data:",
        placeholder="e.g., What are my total sales for October? Show me monthly performance.",
        key="user_question"
    )
    
    if user_question:
        with st.spinner("🤔 Analyzing your data with AI..."):
            response = ai_bot.query_ai(user_question, context_data)
            
            st.markdown('<div class="ai-response">', unsafe_allow_html=True)
            st.markdown("### 🤖 AI Analysis")
            st.markdown(response)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Suggested questions in columns
    st.subheader("💡 Quick Analysis Questions")
    col1, col2, col3 = st.columns(3)
    
    suggested_questions = {
        "📈 October sales?": "What were the total sales for the month of October? Provide breakdown by weeks if available.",
        "👥 Monthly performance?": "Show me the monthly sales performance for all months in the data. Which month performed best?",
        "💰 Q4 performance?": "Analyze the sales performance for the last quarter of the year (October, November, December).",
        "🕒 Seasonal trends?": "What seasonal trends can you observe in the monthly sales data?",
        "📦 Monthly growth?": "Calculate the month-over-month growth rate in sales and identify trends.",
        "🌍 Monthly by country?": "How do sales vary by month across different shipping countries?"
    }
    
    for i, (btn_text, question) in enumerate(suggested_questions.items()):
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(btn_text, key=f"btn_{i}"):
                with st.spinner("Analyzing..."):
                    response = ai_bot.query_ai(question, context_data)
                    st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                    st.markdown(f"**Question:** {question}")
                    st.markdown("---")
                    st.markdown(response)
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Data preview section
    with st.expander("📋 Data Overview & Statistics"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(filtered_data.head(10))
        
        with col2:
            st.metric("Total Rows", f"{len(filtered_data):,}")
            st.metric("Total Columns", f"{len(filtered_data.columns)}")
            st.metric("Data Period", f"{filtered_data['Date'].min()} to {filtered_data['Date'].max()}")
            
            # Column info
            st.subheader("Data Columns")
            for col in filtered_data.columns[:10]:  # Show first 10 columns
                st.text(f"• {col}")

if __name__ == "__main__":
    main()