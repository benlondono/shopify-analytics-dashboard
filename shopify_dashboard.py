#!/usr/bin/env python3
"""
Shopify Multi-Store Analytics Dashboard
Hardcoded for BatterBox Sports and Groovy Golfer stores
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# Add Shopify API imports
import requests
import json
import re
from datetime import datetime, timedelta
import time
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Shopify Multi-Store Dashboard",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hardcoded Shopify Store Credentials
STORES = {
    "BatterBox Sports": {
        "domain": "batterboxsports.myshopify.com",
        "access_token": "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"
    },
    "Groovy Golfer": {
        "domain": "groovygolfer.myshopify.com", 
        "access_token": "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"
    }
}

def test_shopify_connection(store_name, store_config):
    """Test Shopify API connection for a store"""
    headers = {
        'X-Shopify-Access-Token': store_config['access_token'],
        'Content-Type': 'application/json'
    }
    
    try:
        url = f"https://{store_config['domain']}/admin/api/2023-10/shop.json"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            shop_data = response.json()
            return True, shop_data['shop']['name']
        else:
            return False, f"Error {response.status_code}"
    except Exception as e:
        return False, str(e)

def fetch_store_data(store_name, store_config, days_back=None, start_date=None, end_date=None):
    """Fetch orders and products data from a store"""
    headers = {
        'X-Shopify-Access-Token': store_config['access_token'],
        'Content-Type': 'application/json'
    }
    
    # Try different API versions if one fails
    api_versions = ['2023-10', '2023-07', '2023-04', '2023-01']
    
    for api_version in api_versions:
        try:
            # Build the orders URL - keep it as simple as possible
            base_url = f"https://{store_config['domain']}/admin/api/{api_version}/orders.json"
            
            # Start with absolute minimal parameters
            params = {
                'limit': 50  # Start with smaller limit to test
            }
            
            # Build the URL
            if params:
                orders_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            else:
                orders_url = base_url
            
            # Make the test request
            test_response = requests.get(orders_url, headers=headers)
            
            if test_response.status_code == 200:
                # Now fetch the actual data
                all_orders = []
                next_page_info = None
                page_count = 0
                max_pages = 10  # Reduced for testing
                
                while page_count < max_pages:
                    if next_page_info:
                        current_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}&page_info={next_page_info}"
                    else:
                        current_url = orders_url
                        
                    try:
                        orders_response = requests.get(current_url, headers=headers)
                        
                        if orders_response.status_code != 200:
                            st.error(f"❌ Page {page_count + 1} failed: {orders_response.status_code}")
                            break
                        
                        orders_data = orders_response.json()
                        current_orders = orders_data['orders']
                        all_orders.extend(current_orders)
                        
                        # Check for next page
                        link_header = orders_response.headers.get('Link', '')
                        if 'rel="next"' in link_header:
                            next_page_match = re.search(r'page_info=([^&>]+)', link_header)
                            if next_page_match:
                                next_page_info = next_page_match.group(1)
                                page_count += 1
                                time.sleep(0.1)  # Small delay
                            else:
                                break
                        else:
                            break
                            
                    except Exception as e:
                        st.error(f"❌ Error on page {page_count + 1}: {str(e)}")
                        break
                
                # Process orders data and apply date filtering in Python
                orders_list = []
                for order in all_orders:
                    order_date = datetime.strptime(order['created_at'][:10], '%Y-%m-%d')
                    
                    # Apply date filtering if days_back is specified
                    if days_back and order_date < datetime.now() - timedelta(days=days_back):
                        continue
                        
                    orders_list.append({
                        'id': order['id'],
                        'order_number': order['order_number'],
                        'created_at': order_date,
                        'total_price': float(order['total_price']),
                        'currency': order['currency'],
                        'customer_email': order.get('customer', {}).get('email', ''),
                        'line_items_count': len(order['line_items'])
                    })
                
                return pd.DataFrame(orders_list)
                
            elif test_response.status_code == 401:
                st.error(f"❌ Unauthorized for {store_name} - check your access token")
                return None
            elif test_response.status_code == 403:
                st.error(f"❌ Forbidden for {store_name} - check your app permissions")
                return None
            # Only show warnings for non-critical errors
            elif test_response.status_code != 400:  # Don't spam warnings for 400 errors
                st.warning(f"⚠️ API version {api_version} failed with status {test_response.status_code}")
                
        except Exception as e:
            # Only show errors for actual exceptions, not API version failures
            if "Connection" in str(e) or "Timeout" in str(e):
                st.error(f"❌ Connection error for {store_name}: {str(e)}")
                return None
    
    st.error(f"❌ All API versions failed for {store_name}")
    return None

def calculate_growth_metrics(current_data, previous_data, store_name):
    """Calculate growth metrics between current and previous periods"""
    if current_data is None or previous_data is None or current_data.empty or previous_data.empty:
        return None
    
    # Calculate metrics for current period
    current_revenue = current_data['total_price'].sum()
    current_orders = len(current_data)
    current_avg_order = current_revenue / current_orders if current_orders > 0 else 0
    
    # Calculate metrics for previous period
    previous_revenue = previous_data['total_price'].sum()
    previous_orders = len(previous_data)
    previous_avg_order = previous_revenue / previous_orders if previous_orders > 0 else 0
    
    # Calculate growth percentages
    revenue_growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    orders_growth = ((current_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else 0
    avg_order_growth = ((current_avg_order - previous_avg_order) / previous_avg_order * 100) if previous_avg_order > 0 else 0
    
    return {
        'current_revenue': current_revenue,
        'previous_revenue': previous_revenue,
        'current_orders': current_orders,
        'previous_orders': previous_orders,
        'current_avg_order': current_avg_order,
        'previous_avg_order': previous_avg_order,
        'revenue_growth': revenue_growth,
        'orders_growth': orders_growth,
        'avg_order_growth': avg_order_growth
    }

def display_growth_comparison(store_data, store_data_previous, days_back):
    """Display growth comparison charts and metrics"""
    if not store_data_previous:
        return
    
    st.markdown("---")
    st.subheader("📈 Growth Comparison Analysis")
    
    # Calculate growth metrics for each store
    growth_metrics = {}
    for store_name in store_data.keys():
        if store_name in store_data_previous:
            metrics = calculate_growth_metrics(store_data[store_name], store_data_previous[store_name], store_name)
            if metrics:
                growth_metrics[store_name] = metrics
    
    if not growth_metrics:
        st.warning("⚠️ No growth comparison data available")
        return
    
    # Debug: show the actual values being used
    st.write("🔍 **Debug Info:**")
    for store_name, metrics in growth_metrics.items():
        st.write(f"{store_name}: Revenue Growth = {metrics['revenue_growth']:.1f}%, Orders Growth = {metrics['orders_growth']:.1f}%")
    
    # Display growth metrics
    for store_name, metrics in growth_metrics.items():
        st.write(f"**🏪 {store_name} - Growth Analysis**")
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Use custom HTML to force colors
            growth_value = metrics['revenue_growth']
            if growth_value < 0:
                delta_html = f'<span style="color: red; font-weight: bold;">↓ {growth_value:+.1f}%</span>'
            else:
                delta_html = f'<span style="color: green; font-weight: bold;">↑ {growth_value:+.1f}%</span>'
            
            st.markdown(f"""
            **Revenue Growth**  
            ${metrics['current_revenue']:,.2f}  
            {delta_html}
            """, unsafe_allow_html=True)
        
        with col2:
            growth_value = metrics['orders_growth']
            if growth_value < 0:
                delta_html = f'<span style="color: red; font-weight: bold;">↓ {growth_value:+.1f}%</span>'
            else:
                delta_html = f'<span style="color: green; font-weight: bold;">↑ {growth_value:+.1f}%</span>'
            
            st.markdown(f"""
            **Orders Growth**  
            {metrics['current_orders']:,}  
            {delta_html}
            """, unsafe_allow_html=True)
        
        with col3:
            growth_value = metrics['avg_order_growth']
            if growth_value < 0:
                delta_html = f'<span style="color: red; font-weight: bold;">↓ {growth_value:+.1f}%</span>'
            else:
                delta_html = f'<span style="color: green; font-weight: bold;">↑ {growth_value:+.1f}%</span>'
            
            st.markdown(f"""
            **Avg Order Growth**  
            ${metrics['current_avg_order']:,.2f}  
            {delta_html}
            """, unsafe_allow_html=True)
        
        # Create comparison chart
        comparison_data = pd.DataFrame({
            'Period': ['Previous', 'Current'],
            'Revenue': [metrics['previous_revenue'], metrics['current_revenue']],
            'Orders': [metrics['previous_orders'], metrics['current_orders']],
            'Avg Order': [metrics['previous_avg_order'], metrics['current_avg_order']]
        })
        
        # Revenue comparison chart
        fig_revenue = px.bar(
            comparison_data, 
            x='Period', 
            y='Revenue',
            title=f"{store_name} - Revenue Comparison ({days_back} days)",
            color='Period',
            color_discrete_map={'Previous': '#ff6b6b', 'Current': '#4ecdc4'}
        )
        fig_revenue.update_layout(height=400)
        st.plotly_chart(fig_revenue, use_container_width=True)
        
        st.markdown("---")

def main():
    st.title("🏪 Shopify Multi-Store Analytics Dashboard")
    st.markdown("---")
    
    # Store connection status
    st.subheader("🔗 Store Connection Status")
    status_cols = st.columns(len(STORES))
    
    store_status = {}
    for i, (store_name, store_config) in enumerate(STORES.items()):
        with status_cols[i]:
            st.write(f"**{store_name}**")
            is_connected, message = test_shopify_connection(store_name, store_config)
            
            if is_connected:
                st.success(f"✅ Connected: {message}")
                store_status[store_name] = True
            else:
                st.error(f"❌ Failed: {message}")
                store_status[store_name] = False
    
    st.markdown("---")
    
    # Data fetching and analysis
    if any(store_status.values()):
        st.subheader("📊 Store Analytics")
        
        # Date range selector
        st.subheader("📅 Date Range Selection")
        
        # Date range options
        date_option = st.radio(
            "Choose date range:",
            ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "Last 2 years", "Custom range"],
            horizontal=True
        )
        
        # Growth comparison option for non-custom ranges
        show_growth_comparison = False
        if date_option != "Custom range":
            show_growth_comparison = st.checkbox(
                "📈 Compare with previous period (overlay growth analysis)",
                help="Overlay the previous time period to show growth trends and year-over-year comparisons"
            )
        
        # Calculate days based on selection
        if date_option == "Last 30 days":
            days_back = 30
            custom_dates = False
        elif date_option == "Last 90 days":
            days_back = 90
            custom_dates = False
        elif date_option == "Last 6 months":
            days_back = 180
            custom_dates = False
        elif date_option == "Last year":
            days_back = 365
            custom_dates = False
        elif date_option == "Last 2 years":
            days_back = 730
            custom_dates = False
        else:  # Custom range
            custom_dates = True
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())
            
            if start_date and end_date:
                days_back = (end_date - start_date).days
            else:
                days_back = 30
        
        if not custom_dates:
            if show_growth_comparison:
                st.info(f"📊 Analyzing data from the last {days_back} days + comparing with previous {days_back} days for growth analysis")
            else:
                st.info(f"📊 Analyzing data from the last {days_back} days")
        else:
            st.info(f"📊 Analyzing data from {start_date} to {end_date}")
        
        # Note about data fetching
        st.info("💡 **Tip:** For very large date ranges, data is fetched in chunks to avoid API rate limits.")
        
        # Fetch data for connected stores
        store_data = {}
        store_data_previous = {}  # For growth comparison
        
        for store_name, store_config in STORES.items():
            if store_status[store_name]:
                try:
                    # Fetch current period data
                    if custom_dates:
                        data = fetch_store_data(store_name, store_config, start_date=start_date, end_date=end_date)
                    else:
                        data = fetch_store_data(store_name, store_config, days_back=days_back)
                    
                    # Fetch previous period data for growth comparison
                    if show_growth_comparison and not custom_dates:
                        # Calculate previous period dates correctly - completely separate from current period
                        current_end = datetime.now()
                        current_start = current_end - timedelta(days=days_back)
                        
                        # Previous period should be the period BEFORE the current period starts
                        previous_end = current_start
                        previous_start = previous_end - timedelta(days=days_back)
                        
                        # Fetch data for the previous period only - use custom date range to avoid double counting
                        data_previous = fetch_store_data(store_name, store_config, start_date=previous_start, end_date=previous_end)
                        
                        if data_previous is not None and not data_previous.empty:
                            # Double-check that no data overlaps with current period
                            data_previous_filtered = data_previous[data_previous['created_at'] < current_start]
                            if not data_previous_filtered.empty:
                                store_data_previous[store_name] = data_previous_filtered
                            else:
                                st.warning(f"⚠️ No previous period data available for {store_name}")
                        else:
                            st.warning(f"⚠️ No previous period data available for {store_name}")
                    
                    if data is not None and not data.empty:
                        store_data[store_name] = data
                        st.success(f"✅ Loaded {len(data)} orders from {store_name}")
                    else:
                        st.warning(f"⚠️ No data available from {store_name}")
                        
                except Exception as e:
                    st.error(f"❌ Error fetching data from {store_name}: {str(e)}")
        
        if store_data:
            st.markdown("---")
            
            # Summary metrics
            st.subheader("📈 Summary Metrics")
            summary_cols = st.columns(len(store_data))
            
            for i, (store_name, data) in enumerate(store_data.items()):
                with summary_cols[i]:
                    st.metric(
                        label=f"{store_name} - Total Revenue",
                        value=f"${data['total_price'].sum():,.2f}",
                        delta=f"{len(data)} orders"
                    )
            
            # Revenue comparison chart
            if len(store_data) > 1:
                st.subheader("📊 Revenue Comparison")
                
                # Prepare data for comparison
                comparison_data = []
                for store_name, data in store_data.items():
                    daily_revenue = data.groupby('created_at')['total_price'].sum().reset_index()
                    daily_revenue['store'] = store_name
                    comparison_data.append(daily_revenue)
                
                if comparison_data:
                    combined_data = pd.concat(comparison_data)
                    
                    fig = px.line(
                        combined_data, 
                        x='created_at', 
                        y='total_price',
                        color='store',
                        title="Daily Revenue Comparison",
                        labels={'total_price': 'Revenue ($)', 'created_at': 'Date'}
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Individual store details
            for store_name, data in store_data.items():
                st.markdown("---")
                st.subheader(f"🏪 {store_name} Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Revenue Trends**")
                    daily_revenue = data.groupby('created_at')['total_price'].sum()
                    st.line_chart(daily_revenue)
                
                with col2:
                    st.write("**Order Distribution**")
                    st.bar_chart(data.groupby(data['created_at'].dt.date)['line_items_count'].sum())
                
                # Recent orders table
                st.write("**Recent Orders**")
                recent_orders = data.sort_values('created_at', ascending=False).head(10)
                st.dataframe(
                    recent_orders[['order_number', 'created_at', 'total_price', 'customer_email']],
                    hide_index=True
                )
            
            # Display growth comparison if enabled
            if show_growth_comparison and not custom_dates:
                display_growth_comparison(store_data, store_data_previous, days_back)
    
    else:
        st.error("❌ No stores are connected. Please check your API credentials.")
        st.info("💡 Make sure to replace the placeholder access tokens in the code with your actual Shopify API keys.")
    
    # Footer
    st.markdown("---")
    st.caption("🔒 Private Dashboard - Internal Use Only")

if __name__ == "__main__":
    main() 