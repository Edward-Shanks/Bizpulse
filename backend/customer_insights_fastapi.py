import pandas as pd
import requests
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key from environment
PPLX_API_KEY1 = os.getenv("PPLX_API_KEY1")
if not PPLX_API_KEY1:
    logger.warning("PPLX_API_KEY1 not found in environment. Some features may not work.")

# Path to Shopify CSV file - try multiple possible file names
ROOT_DIR = Path(__file__).resolve().parent
SHOPIFY_CSV_PATH = None
# Try different possible file names
for filename in ['shopify_data.csv', 'Shopify_customer_df.csv', 'customer_shopify.csv']:
    potential_path = ROOT_DIR / filename
    if potential_path.exists():
        SHOPIFY_CSV_PATH = potential_path
        break

if SHOPIFY_CSV_PATH is None:
    # Default to shopify_data.csv
    SHOPIFY_CSV_PATH = ROOT_DIR / 'shopify_data.csv'

# Global variable to store loaded data
df_global = None

def convert_to_native_types(obj):
    """Recursively convert numpy/pandas types to native Python types for JSON serialization"""
    # Handle numpy scalar types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_to_native_types(item) for item in obj.tolist()]
    elif isinstance(obj, pd.Series):
        return [convert_to_native_types(item) for item in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        # Convert DataFrame to records and then convert each record
        records = obj.to_dict('records')
        return [convert_to_native_types(record) for record in records]
    elif isinstance(obj, dict):
        return {str(k): convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_types(item) for item in obj]
    elif pd.isna(obj) or obj is None:
        return None
    elif hasattr(obj, 'item'):  # numpy scalar with item() method
        return obj.item()
    else:
        # For other types, try to convert to string if it's not a basic type
        if isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            return str(obj)

def load_shopify_data():
    """Load Shopify data with caching"""
    global df_global
    if df_global is not None:
        return df_global
    
    try:
        logger.info(f"Loading Shopify data from {SHOPIFY_CSV_PATH}")
        df = pd.read_csv(SHOPIFY_CSV_PATH)
        
        if df.empty:
            raise ValueError("Shopify dataset is empty")
        
        # Normalize column names
        df.columns = df.columns.str.strip()
        
        # Convert date column
        if 'Day' in df.columns:
            df['Day'] = pd.to_datetime(df['Day'], errors='coerce')
            df['Year'] = df['Day'].dt.year
            df['Month'] = df['Day'].dt.month
            df['MonthName'] = df['Day'].dt.strftime('%B')
            df['Date'] = df['Day'].dt.date
            df['DayOfWeek'] = df['Day'].dt.day_name()
        
        # Ensure numeric columns
        numeric_cols = ['Net sales', 'Gross sales', 'Total sales', 'Orders', 
                       'Orders (first-time)', 'Orders (returning)', 
                       'Quantity ordered', 'Quantity returned', 'Customers',
                       'New customers', 'Returning customers', 'Net returns',
                       'Total returns', 'Hour of day']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate additional metrics
        if 'Total sales' in df.columns and 'Orders' in df.columns:
            df['Avg_Order_Value'] = df['Total sales'] / df['Orders'].replace(0, 1)
            df['Avg_Order_Value'] = df['Avg_Order_Value'].fillna(0)
        
        if 'Orders' in df.columns and 'Customers' in df.columns:
            df['Conversion_Rate'] = df['Orders'] / df['Customers'].replace(0, 1)
            df['Conversion_Rate'] = df['Conversion_Rate'].fillna(0)
        
        df_global = df
        logger.info(f"Shopify data loaded successfully: {len(df_global)} rows")
        return df_global
    except Exception as e:
        logger.error(f"Error loading Shopify data: {e}")
        raise

def query_perplexity(prompt, conversation_history=None):
    """Query Perplexity API"""
    if not PPLX_API_KEY1:
        return "API key not configured. Please set PPLX_API_KEY1 environment variable."
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {PPLX_API_KEY1}", "Content-Type": "application/json"}
    
    messages = [{
        "role": "system",
        "content": (
            "You are Vector AI, a friendly customer intelligence analyst for ThriveBrands, "
            "assisting with actionable insights from Shopify customer data. "
            "Analyze the provided data and deliver a detailed, confident answer in a conversational tone. "
            "All monetary values are in Euros (€) or the currency shown in the data. "
            "State results definitively, e.g., 'After analyzing the customer data, [answer].' "
            "Include trends, growth rates (%), and percentages where relevant. "
            "For customer behavior questions, identify patterns with specific numbers. "
            "Always provide 3-5 specific, actionable recommendations with clear 'why' and 'how' for each. "
            "Use conversation history for context in follow-ups. "
            "Keep it engaging and provide comprehensive analysis."
        )
    }]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": prompt})
    payload = {"model": "sonar-pro", "messages": messages, "max_tokens": 2000}
    
    try:
        logger.info("Sending request to Perplexity API")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        logger.info("Received response from Perplexity API")
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Perplexity API error: {e}")
        return f"Error querying AI: {str(e)}"

def parse_query(query):
    """Parse user query to extract filters and columns of interest"""
    query_lower = query.lower()
    filters = {}
    columns = []
    
    # Detect query types
    is_trend_query = "trend" in query_lower or "compare" in query_lower or "over time" in query_lower
    is_customer_query = "customer" in query_lower or "clv" in query_lower or "lifetime" in query_lower
    is_channel_query = "channel" in query_lower or "traffic" in query_lower or "referring" in query_lower
    is_geographic_query = "country" in query_lower or "region" in query_lower or "geographic" in query_lower
    
    # Extract columns of interest
    if "sales" in query_lower or "revenue" in query_lower:
        columns.append("Total sales")
    if "orders" in query_lower:
        columns.append("Orders")
    if "customers" in query_lower:
        columns.append("Customers")
    if "conversion" in query_lower:
        columns.append("Conversion_Rate")
    if "aov" in query_lower or "average order" in query_lower:
        columns.append("Avg_Order_Value")
    
    # Extract filters
    if "year" in query_lower:
        for year in ["2023", "2024", "2025", "2026"]:
            if year in query:
                filters["Year"] = int(year)
                break
    
    if "month" in query_lower:
        month_map = {
            "january": "January", "february": "February", "march": "March",
            "april": "April", "may": "May", "june": "June",
            "july": "July", "august": "August", "september": "September",
            "october": "October", "november": "November", "december": "December"
        }
        for month_key, month_name in month_map.items():
            if month_key in query_lower:
                filters["MonthName"] = month_name
                break
    
    if "new customer" in query_lower or "new" in query_lower:
        filters["New or returning customer"] = "New"
    elif "returning customer" in query_lower or "returning" in query_lower:
        filters["New or returning customer"] = "Returning"
    
    if "channel" in query_lower:
        # Try to extract specific channel
        channels = ["google", "facebook", "instagram", "direct", "unknown"]
        for channel in channels:
            if channel in query_lower:
                filters["Referring channel"] = channel.capitalize() if channel != "unknown" else "unknown"
                break
    
    if "country" in query_lower:
        # Common countries
        countries = ["united kingdom", "uk", "ireland", "usa", "united states"]
        for country in countries:
            if country in query_lower:
                if country in ["uk", "united kingdom"]:
                    filters["Shipping country"] = "United Kingdom"
                elif country == "ireland":
                    filters["Shipping country"] = "Ireland"
                elif country in ["usa", "united states"]:
                    filters["Shipping country"] = "United States"
                break
    
    return columns, filters, is_trend_query, is_customer_query, is_channel_query, is_geographic_query

def pivot_shopify_data(df, columns, filters, is_trend_query, query_lower=""):
    """Pivot and aggregate Shopify data based on query"""
    filtered_df = df.copy()
    
    # Apply filters
    for key, value in filters.items():
        if value is not None and key in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[key] == value]
    
    # Default columns if none specified
    if not columns:
        columns = ["Total sales", "Orders", "Customers"]
    
    # Restrict to columns that exist
    selected_columns = [c for c in columns if c in filtered_df.columns]
    if not selected_columns:
        selected_columns = ["Total sales", "Orders", "Customers"]
    
    # Ensure numeric
    for col in selected_columns:
        if col in filtered_df.columns:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
    
    # Determine pivot columns
    pivot_columns = []
    
    if is_trend_query:
        if "month" in query_lower:
            pivot_columns = ["Year", "MonthName"]
        elif "day" in query_lower or "daily" in query_lower:
            pivot_columns = ["Date"]
        else:
            pivot_columns = ["Year", "MonthName"]
    else:
        # Group by relevant dimensions
        if "channel" in query_lower:
            pivot_columns = ["Referring channel"]
        elif "country" in query_lower or "geographic" in query_lower:
            pivot_columns = ["Shipping country"]
        elif "customer" in query_lower:
            pivot_columns = ["New or returning customer"]
        elif "product" in query_lower:
            pivot_columns = ["Product variant SKU"]
        elif "hour" in query_lower:
            pivot_columns = ["Hour of day"]
        else:
            # Default: aggregate all
            pivot_columns = []
    
    # Create pivot table
    if pivot_columns:
        pivot_table = filtered_df.groupby(pivot_columns)[selected_columns].agg('sum').reset_index()
        pivot_table = pivot_table.sort_values(by=selected_columns[0] if selected_columns else pivot_columns[0], ascending=False)
    else:
        # Overall summary
        pivot_table = pd.DataFrame({
            col: [filtered_df[col].sum()] for col in selected_columns
        })
    
    # Format numeric columns and convert to native Python types
    for col in selected_columns:
        if col in pivot_table.columns:
            pivot_table[col] = pd.to_numeric(pivot_table[col], errors='coerce').fillna(0).round(2)
    
    # Convert all numpy types to native Python types for JSON serialization
    for col in pivot_table.columns:
        if pivot_table[col].dtype == 'int64':
            pivot_table[col] = pivot_table[col].astype('Int64').fillna(0).astype(int)
        elif pivot_table[col].dtype == 'float64':
            pivot_table[col] = pivot_table[col].astype(float)
        # Convert object columns that might contain numpy types
        elif pivot_table[col].dtype == 'object':
            pivot_table[col] = pivot_table[col].astype(str)
    
    return pivot_table, filtered_df

def generate_shopify_data_context(df, query, prev_messages=None, preset_filters: Optional[Dict[str, Any]] = None):
    """Generate data context for AI based on Shopify data"""
    columns, filters, is_trend_query, is_customer_query, is_channel_query, is_geographic_query = parse_query(query)
    
    # Merge preset filters
    if preset_filters:
        for k, v in preset_filters.items():
            if v is not None:
                # Map preset filter keys to Shopify column names
                if k == 'year':
                    filters['Year'] = int(v)
                elif k == 'month':
                    filters['MonthName'] = str(v)
                elif k == 'channel':
                    filters['Referring channel'] = str(v)
                elif k == 'customer_type':
                    filters['New or returning customer'] = str(v)
                elif k == 'country':
                    filters['Shipping country'] = str(v)
                else:
                    filters[k] = v
    
    query_lower = query.lower()
    pivot_table, filtered_df = pivot_shopify_data(df, columns, filters, is_trend_query, query_lower)
    
    # Build context string
    context = f"Shopify Customer Data Analysis for '{query}':\n\n"
    
    # Add summary statistics
    if not filtered_df.empty:
        total_sales = float(filtered_df['Total sales'].sum()) if 'Total sales' in filtered_df.columns else 0.0
        total_orders = int(filtered_df['Orders'].sum()) if 'Orders' in filtered_df.columns else 0
        total_customers = int(filtered_df['Customer email'].nunique()) if 'Customer email' in filtered_df.columns else 0
        
        context += f"Summary Statistics:\n"
        context += f"- Total Sales: €{total_sales:,.2f}\n"
        context += f"- Total Orders: {total_orders:,}\n"
        context += f"- Unique Customers: {total_customers:,}\n"
        if total_orders > 0:
            avg_order_value = float(total_sales / total_orders)
            context += f"- Average Order Value: €{avg_order_value:,.2f}\n"
        context += "\n"
    
    # Add pivot table data
    if not pivot_table.empty:
        context += "Detailed Data:\n"
        # Format pivot table for readability
        pivot_str = pivot_table.to_string(index=False)
        context += pivot_str
        context += "\n\n"
    
    # Add additional insights based on query type
    if is_customer_query and 'Customer email' in filtered_df.columns:
        customer_segments = filtered_df['New or returning customer'].value_counts().to_dict()
        customer_segments = convert_to_native_types(customer_segments)
        context += f"Customer Segments: {customer_segments}\n"
    
    if is_channel_query and 'Referring channel' in filtered_df.columns:
        top_channels = filtered_df.groupby('Referring channel')['Total sales'].sum().nlargest(5).to_dict()
        top_channels = convert_to_native_types(top_channels)
        context += f"Top Channels by Sales: {top_channels}\n"
    
    if is_geographic_query and 'Shipping country' in filtered_df.columns:
        top_countries = filtered_df.groupby('Shipping country')['Total sales'].sum().nlargest(5).to_dict()
        top_countries = convert_to_native_types(top_countries)
        context += f"Top Countries by Sales: {top_countries}\n"
    
    # Add conversation history if follow-up
    if prev_messages and len(prev_messages) > 0:
        context += "\nPrevious conversation context:\n"
        for msg in prev_messages[-3:]:  # Last 3 messages
            role = msg.get("role", "user") if isinstance(msg, dict) else getattr(msg, "role", "user")
            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
            context += f"{role.capitalize()}: {content}\n"
    
    return context, columns, filters, pivot_table, filtered_df, is_trend_query

def process_customer_insights_chat(message: str, context: Optional[Dict] = None, 
                                   conversation_history: Optional[List] = None,
                                   chart_title: Optional[str] = None):
    """Main function to process customer insights chat requests"""
    try:
        df = load_shopify_data()
        if df is None or df.empty:
            return {
                "response": "Sorry, I couldn't load the customer data. Please try again later.",
                "timestamp": datetime.now().strftime("%I:%M %p IST on %B %d, %Y"),
                "context": "",
                "data": {}
            }
        
        # Extract preset filters from context
        preset_filters = {}
        if context:
            if 'year' in context or 'selectedYears' in context:
                year_val = context.get('year') or (context.get('selectedYears') or [None])[0]
                if year_val:
                    preset_filters['year'] = int(year_val)
            
            if 'month' in context or 'selectedMonths' in context:
                month_val = context.get('month') or (context.get('selectedMonths') or [None])[0]
                if month_val:
                    preset_filters['month'] = str(month_val)
            
            if 'channel' in context or 'selectedChannels' in context:
                channel_val = context.get('channel') or (context.get('selectedChannels') or [None])[0]
                if channel_val:
                    preset_filters['channel'] = str(channel_val)
        
        # Convert conversation history to list of dicts
        conv_history = []
        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict):
                    conv_history.append(msg)
                elif hasattr(msg, 'dict'):
                    conv_history.append(msg.dict())
                else:
                    conv_history.append({
                        "role": getattr(msg, 'role', 'user'),
                        "content": getattr(msg, 'content', '')
                    })
        
        # Generate data context
        data_context, columns, filters, pivot_table, filtered_df, is_trend = generate_shopify_data_context(
            df, message, conv_history, preset_filters
        )
        
        # Add chart title context if provided
        chart_context = ""
        if chart_title:
            chart_context = f"\n\nCurrent Chart Context: {chart_title}"
        
        # Format pivot table for prompt
        pivot_data_str = ""
        if not pivot_table.empty:
            top_rows = pivot_table.head(10)
            pivot_data_str = f"\n\nKey Data Summary:\n{top_rows.to_string(index=False)}\n"
            if len(pivot_table) > 10:
                pivot_data_str += f"\n(Showing top 10 of {len(pivot_table)} rows)\n"
        
        # Build full prompt
        full_prompt = f"Based on the following Shopify customer data, answer the question: {message}\n\n{data_context}{chart_context}{pivot_data_str}"
        
        # Query AI
        response_text = query_perplexity(full_prompt, conv_history if conv_history else None)
        
        # Prepare response - convert numpy types to native Python types
        timestamp = datetime.now().strftime("%I:%M %p IST on %B %d, %Y")
        
        # Convert pivot_table to dict and ensure all values are JSON serializable
        pivot_records = []
        if not pivot_table.empty:
            # Convert DataFrame to dict records, then convert numpy types
            pivot_dict = pivot_table.to_dict('records')
            pivot_records = convert_to_native_types(pivot_dict)
        
        # Convert filters to ensure JSON serializable
        serializable_filters = convert_to_native_types(filters)
        
        return {
            "response": response_text,
            "timestamp": timestamp,
            "context": data_context[:500] + "..." if len(data_context) > 500 else data_context,
            "data": {
                "pivot_table": pivot_records,
                "columns": columns,
                "filters": serializable_filters,
                "is_trend_query": bool(is_trend),
                "total_rows": int(len(filtered_df)),
                "chart_title": chart_title
            }
        }
    except Exception as e:
        logger.error(f"Error processing customer insights chat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "response": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
            "timestamp": datetime.now().strftime("%I:%M %p IST on %B %d, %Y"),
            "context": "",
            "data": {}
        }

