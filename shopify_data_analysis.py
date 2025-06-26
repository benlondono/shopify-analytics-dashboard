#!/usr/bin/env python3
"""
AI-Powered Shopify Sales Analysis Tool
Analyzes live Shopify store data and provides AI-driven insights and predictions
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
from datetime import datetime, timedelta
import time
import streamlit as st

def test_shopify_connection(shop_domain, access_token):
    """Test if Shopify API credentials are working"""
    print("🔍 Testing Shopify API connection...")
    
    # Clean up shop domain
    shop_domain = clean_shop_domain(shop_domain)
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test with a simple API call to get shop info
        url = f"{shop_domain}/admin/api/2023-10/shop.json"
        response = requests.get(url, headers=headers)
        
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            shop_data = response.json()
            shop_name = shop_data.get('shop', {}).get('name', 'Unknown')
            print(f"   ✅ Connected successfully to: {shop_name}")
            return True
        else:
            print(f"   ❌ Connection failed: {response.status_code}")
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def clean_shop_domain(shop_domain):
    """Clean and format shop domain"""
    # Remove any existing protocol
    if shop_domain.startswith('https://'):
        shop_domain = shop_domain[8:]
    elif shop_domain.startswith('http://'):
        shop_domain = shop_domain[7:]
    
    # Remove any trailing slashes
    shop_domain = shop_domain.rstrip('/')
    
    # Add .myshopify.com if not present
    if not shop_domain.endswith('.myshopify.com'):
        shop_domain = f"{shop_domain}.myshopify.com"
    
    # Add https:// protocol
    shop_domain = f"https://{shop_domain}"
    
    return shop_domain

def get_shopify_credentials():
    """Get Shopify store credentials from user"""
    print("🔗 Shopify Store Connection:")
    shop_domain = input("Enter your Shopify store domain (e.g., your-store): ").strip()
    access_token = input("Enter your Shopify access token: ").strip()
    
    if not shop_domain or not access_token:
        print("❌ Both shop domain and access token are required.")
        return None, None
    
    # Clean up shop domain
    shop_domain = clean_shop_domain(shop_domain)
    
    # Test the connection
    if not test_shopify_connection(shop_domain, access_token):
        print("❌ Could not connect to Shopify. Please check your credentials.")
        return None, None
    
    return shop_domain, access_token

def fetch_shopify_orders(shop_domain, access_token, days_back=None):
    """Fetch all orders from Shopify API using cursor-based pagination"""
    if days_back:
        print(f"📊 Fetching Shopify orders from the last {days_back} days...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        params = {
            'status': 'any',
            'created_at_min': start_date_str,
            'created_at_max': end_date_str,
            'limit': 50,
            'order': 'created_at asc'
        }
    else:
        print("📊 Fetching ALL historical Shopify orders...")
        params = {
            'status': 'any',
            'limit': 50,
            'order': 'created_at asc'
        }
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    all_orders = []
    next_page_url = None
    base_url = f"{shop_domain}/admin/api/2023-10/orders.json"
    
    try:
        while True:
            if next_page_url:
                url = next_page_url
                req_params = None
            else:
                url = base_url
                req_params = params
            response = requests.get(url, headers=headers, params=req_params)
            print(f"   🔗 Requesting: {response.url}")
            response.raise_for_status()
            data = response.json()
            orders = data.get('orders', [])
            all_orders.extend(orders)
            print(f"   ✅ Fetched {len(orders)} orders (total so far: {len(all_orders)})")
            # Pagination: look for 'Link' header with rel="next"
            link_header = response.headers.get('Link', '')
            next_page_url = None
            if 'rel="next"' in link_header:
                # Extract next page URL
                parts = link_header.split(',')
                for part in parts:
                    if 'rel="next"' in part:
                        next_url = part.split(';')[0].strip().strip('<>')
                        next_page_url = next_url
                        break
            if not next_page_url:
                break
        print(f"✅ Successfully fetched {len(all_orders)} orders from Shopify")
        return all_orders
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching orders: {e}")
        return None

def fetch_shopify_products(shop_domain, access_token):
    """Fetch products from Shopify API"""
    print("📦 Fetching Shopify products...")
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    all_products = []
    page_info = None
    
    try:
        while True:
            url = f"{shop_domain}/admin/api/2023-10/products.json"
            params = {'limit': 250}
            
            if page_info:
                params['page_info'] = page_info
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('products', [])
            
            if not products:
                break
                
            all_products.extend(products)
            print(f"   ✅ Fetched {len(products)} products...")
            
            # Check for pagination
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break
                
            next_link = [link for link in link_header.split(', ') if 'rel="next"' in link]
            if next_link:
                page_info = next_link[0].split('page_info=')[1].split('>')[0]
            else:
                break
            
            time.sleep(0.5)
        
        print(f"✅ Successfully fetched {len(all_products)} products from Shopify")
        return all_products
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching products: {e}")
        return None

def process_shopify_data(orders, products):
    """Convert Shopify API data to pandas DataFrame"""
    print("🔄 Processing Shopify data...")
    
    if not orders:
        print("❌ No orders to process")
        return None
    
    # Create product lookup dictionary
    product_lookup = {}
    if products:
        for product in products:
            for variant in product.get('variants', []):
                product_lookup[variant['id']] = {
                    'product_id': str(product['id']),
                    'product_title': product['title'],
                    'product_type': product.get('product_type', 'Unknown'),
                    'vendor': product.get('vendor', 'Unknown'),
                    'variant_title': variant.get('title', ''),
                    'sku': variant.get('sku', ''),
                    'price': float(variant.get('price', 0))
                }
    
    # Process orders into DataFrame
    processed_data = []
    
    for order in orders:
        order_id = order['id']
        order_date = order['created_at']
        order_total = float(order.get('total_price', 0))
        order_subtotal = float(order.get('subtotal_price', 0))
        order_tax = float(order.get('total_tax', 0))
        order_shipping = float(order.get('total_shipping_price_set', {}).get('shop_money', {}).get('amount', 0))
        
        # Process line items
        for item in order.get('line_items', []):
            variant_id = item.get('variant_id')
            product_info = product_lookup.get(variant_id, {})
            
            processed_data.append({
                'order_id': order_id,
                'order_date': order_date,
                'order_total': order_total,
                'order_subtotal': order_subtotal,
                'order_tax': order_tax,
                'order_shipping': order_shipping,
                'line_item_id': item['id'],
                'product_id': product_info.get('product_id', ''),
                'product_title': product_info.get('product_title', item.get('title', 'Unknown')),
                'product_type': product_info.get('product_type', 'Unknown'),
                'vendor': product_info.get('vendor', 'Unknown'),
                'variant_title': product_info.get('variant_title', ''),
                'sku': product_info.get('sku', ''),
                'quantity': item.get('quantity', 0),
                'price': float(item.get('price', 0)),
                'line_total': float(item.get('price', 0)) * item.get('quantity', 0),
                'currency': order.get('currency', 'USD')
            })
    
    df = pd.DataFrame(processed_data)
    
    if df.empty:
        print("❌ No data to process")
        return None
    
    print(f"✅ Processed {len(df)} line items from {len(orders)} orders")
    return df

@st.cache_data(show_spinner=True)
def load_shopify_data_cached(shop_domain, access_token, days_back):
    """Main function to load data from Shopify"""
    st.info("🛍️ Loading Shopify data...")
    
    # Test connection first
    if not test_shopify_connection(shop_domain, access_token):
        st.error("Could not connect to Shopify. Please check your credentials.")
        return None
    
    # Fetch data
    with st.spinner("Fetching orders from Shopify..."):
        orders = fetch_shopify_orders(shop_domain, access_token, days_back)
    if not orders:
        st.error("Could not fetch orders from Shopify.")
        return None
    
    with st.spinner("Fetching products from Shopify..."):
        products = fetch_shopify_products(shop_domain, access_token)
    
    # Process data
    with st.spinner("Processing data..."):
        data = process_shopify_data(orders, products)
    if data is None:
        st.error("Could not process Shopify data.")
        return None
    
    st.success(f"✅ Successfully loaded {len(data)} line items from {data['order_id'].nunique()} orders")
    
    # Calculate weeks from days (only if days_back is provided)
    if days_back is not None:
        sales_period_weeks = days_back / 7.0
        data.attrs['sales_period_weeks'] = sales_period_weeks
    else:
        # For full history, we'll calculate this later based on actual data
        data.attrs['sales_period_weeks'] = None
    
    # Convert order_date to datetime, force errors to NaT, and handle timezone-aware datetimes
    data['order_date'] = pd.to_datetime(data['order_date'], errors='coerce', utc=True)
    # Drop rows where order_date could not be converted
    data = data.dropna(subset=['order_date'])
    
    return data

def get_sales_period():
    # This function is no longer needed since we calculate weeks from days_back
    return 12.0  # Default fallback

def analyze_sales_data(data, sales_period_weeks):
    # Use Shopify data structure
    total_col = 'line_total'  # Total revenue from line items
    total_revenue = data[total_col].sum()
    total_orders = data['order_id'].nunique()  # Count unique orders
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    weekly_revenue = total_revenue / sales_period_weeks
    weekly_orders = total_orders / sales_period_weeks
    
    # Analyze product types with better handling of empty values
    product_col = 'product_type'
    if product_col in data.columns:
        # Clean up product types - replace empty/null values
        data_clean = data.copy()
        data_clean[product_col] = data_clean[product_col].fillna('Uncategorized')
        data_clean[product_col] = data_clean[product_col].replace('', 'Uncategorized')
        data_clean[product_col] = data_clean[product_col].replace('Unknown', 'Uncategorized')
        
        # Group by cleaned product types
        top_products = data_clean.groupby(product_col)[total_col].sum().sort_values(ascending=False).head(10)
    
    # Analyze vendors with better handling of empty values
    vendor_col = 'vendor'
    if vendor_col in data.columns:
        # Clean up vendors - replace empty/null values
        data_clean = data.copy()
        data_clean[vendor_col] = data_clean[vendor_col].fillna('Unknown Vendor')
        data_clean[vendor_col] = data_clean[vendor_col].replace('', 'Unknown Vendor')
        data_clean[vendor_col] = data_clean[vendor_col].replace('Unknown', 'Unknown Vendor')
        
        # Group by cleaned vendors
        top_vendors = data_clean.groupby(vendor_col)[total_col].sum().sort_values(ascending=False).head(10)
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'weekly_revenue': weekly_revenue,
        'weekly_orders': weekly_orders,
        'sales_period_weeks': sales_period_weeks,
        'total_col': total_col,
        'product_col': product_col,
        'vendor_col': vendor_col,
        'top_products': top_products if product_col in data.columns else None,
        'top_vendors': top_vendors if vendor_col in data.columns else None
    }

def create_enhanced_visualization(data, sales_analysis, predictions):
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        if sales_analysis['product_col']:
            product_revenue = data.groupby(sales_analysis['product_col'])[sales_analysis['total_col']].sum().sort_values(ascending=False).head(8)
            ax1.bar(range(len(product_revenue)), product_revenue.values, color='skyblue')
            ax1.set_title('Revenue by Product Type')
            ax1.set_xticks(range(len(product_revenue)))
            ax1.set_xticklabels(product_revenue.index, rotation=45, ha='right')
            ax1.set_ylabel('Revenue ($)')
        if sales_analysis['vendor_col']:
            vendor_revenue = data.groupby(sales_analysis['vendor_col'])[sales_analysis['total_col']].sum().sort_values(ascending=False).head(8)
            ax2.bar(range(len(vendor_revenue)), vendor_revenue.values, color='orange')
            ax2.set_title('Revenue by Vendor')
            ax2.set_xticks(range(len(vendor_revenue)))
            ax2.set_xticklabels(vendor_revenue.index, rotation=45, ha='right')
            ax2.set_ylabel('Revenue ($)')
        weeks = np.arange(1, 53)
        ax3.plot(weeks, predictions['revenue_prediction'], 'b-', linewidth=2, label='Predicted Revenue')
        ax3.axhline(y=sales_analysis['weekly_revenue'], color='r', linestyle='--', label='Current Weekly Revenue')
        ax3.set_title('52-Week Revenue Forecast')
        ax3.set_xlabel('Week')
        ax3.set_ylabel('Revenue ($)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax4.axis('off')
        summary_text = f"""
AI Analysis Summary:\n• Current Weekly Revenue: ${sales_analysis['weekly_revenue']:,.2f}\n• Average Order Value: ${sales_analysis['avg_order_value']:.2f}\n• Projected Annual Growth: {predictions['projected_annual_growth']:.1f}%\n• Total Products Analyzed: {sales_analysis['total_orders']:,}\n• Top Category: {sales_analysis['top_products'].index[0] if sales_analysis['top_products'] is not None else 'N/A'}\n        """
        ax4.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center')
        plt.tight_layout()
        plt.savefig('ai_sales_analysis_results.png', dpi=300, bbox_inches='tight')
        print("📊 AI-enhanced visualization saved as 'ai_sales_analysis_results.png'")
    except Exception as e:
        print(f"⚠️ Could not create visualization: {e}")

def main():
    st.set_page_config(page_title="Shopify Sales Dashboard", layout="wide")
    st.title("📊 Shopify Sales Dashboard")
    st.write("Analyze your Shopify store performance with live data.")

    # Streamlit widgets for credentials and days input
    shop_domain = st.text_input("Shopify store domain (e.g., your-store): ")
    access_token = st.text_input("Shopify access token", type="password")
    
    # Data range selection
    data_range_option = st.radio(
        "Select data range:",
        ["Recent Period", "Full History"],
        horizontal=True
    )
    
    if data_range_option == "Recent Period":
        days_back = st.number_input("Enter number of days to analyze", min_value=1, max_value=365, value=90)
        use_full_history = False
    else:
        days_back = None
        use_full_history = True
        st.info("⚠️ Loading full historical data may take longer and use more API calls.")

    if shop_domain and access_token:
        # Clean up the shop domain
        shop_domain = clean_shop_domain(shop_domain)
        
        sales_data = load_shopify_data_cached(shop_domain, access_token, days_back)
        if sales_data is None or sales_data.empty:
            st.error("Could not load Shopify data. Check your credentials or data availability.")
            return
        
        # Calculate sales period weeks based on actual data range
        if use_full_history:
            date_range = sales_data['order_date'].max() - sales_data['order_date'].min()
            sales_period_weeks = date_range.days / 7.0
        else:
            sales_period_weeks = sales_data.attrs.get('sales_period_weeks', 12.9)
        
        # Date range selection for filtering (only if not using full history)
        if not use_full_history:
            min_date = sales_data['order_date'].min().date()
            max_date = sales_data['order_date'].max().date()
            date_range = st.date_input(
                "Select date range to filter:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Fix date range unpacking
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
                
            mask = (sales_data['order_date'].dt.date >= start_date) & (sales_data['order_date'].dt.date <= end_date)
            filtered_data = sales_data.loc[mask]
        else:
            # Use all data for full history
            filtered_data = sales_data
            start_date = sales_data['order_date'].min().date()
            end_date = sales_data['order_date'].max().date()
        
        # Calculate metrics
        total_sales = filtered_data['line_total'].sum()
        total_orders = filtered_data['order_id'].nunique()
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Layout for summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total sales", f"${total_sales:,.2f}")
        with col2:
            st.metric("Total orders", f"{total_orders}")
        with col3:
            st.metric("Average order value", f"${avg_order_value:,.2f}")
        
        # Prepare daily data for charts
        daily = filtered_data.groupby(filtered_data['order_date'].dt.date).agg({
            'line_total': 'sum',
            'order_id': pd.Series.nunique
        }).rename(columns={'line_total': 'Total Sales', 'order_id': 'Total Orders'})
        daily['Average Order Value'] = daily['Total Sales'] / daily['Total Orders']
        
        # Charts
        st.subheader("📈 Sales Trends")
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        with chart_col1:
            st.line_chart(daily['Total Sales'], height=250)
            st.caption("Daily Sales")
        with chart_col2:
            st.line_chart(daily['Total Orders'], height=250)
            st.caption("Daily Orders")
        with chart_col3:
            st.line_chart(daily['Average Order Value'], height=250)
            st.caption("Average Order Value")
        
        # Run analysis
        sales_analysis = analyze_sales_data(filtered_data, sales_period_weeks)
        
        # Interactive Bar Charts Section
        st.subheader("📊 Sales by Category and Vendor")
        
        # Category Analysis
        if sales_analysis['top_products'] is not None:
            st.write("**Sales by Product Category**")
            category_data = sales_analysis['top_products'].reset_index()
            category_data.columns = ['Category', 'Revenue']
            category_data['Revenue_Formatted'] = category_data['Revenue'].apply(lambda x: f"${x:,.0f}")
            
            # Create professional bar chart
            fig_category, ax_category = plt.subplots(figsize=(12, 6))
            
            # Use a professional color palette
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            bars = ax_category.bar(range(len(category_data)), category_data['Revenue'], 
                                 color=colors[:len(category_data)], alpha=0.8, edgecolor='white', linewidth=1)
            
            # Professional styling
            ax_category.set_title('Revenue by Product Category', fontsize=16, fontweight='bold', pad=20, color='#262730')
            ax_category.set_xlabel('Product Category', fontsize=12, color='#262730')
            ax_category.set_ylabel('Revenue ($)', fontsize=12, color='#262730')
            
            # Clean x-axis labels
            ax_category.set_xticks(range(len(category_data)))
            ax_category.set_xticklabels(category_data['Category'], rotation=45, ha='right', fontsize=10)
            
            # Remove spines for cleaner look
            ax_category.spines['top'].set_visible(False)
            ax_category.spines['right'].set_visible(False)
            ax_category.spines['left'].set_color('#e0e0e0')
            ax_category.spines['bottom'].set_color('#e0e0e0')
            
            # Add subtle grid
            ax_category.grid(axis='y', alpha=0.3, color='#e0e0e0', linestyle='-', linewidth=0.5)
            ax_category.set_axisbelow(True)
            
            # Add value labels on bars with professional styling
            for i, (bar, revenue) in enumerate(zip(bars, category_data['Revenue'])):
                height = bar.get_height()
                ax_category.text(bar.get_x() + bar.get_width()/2, height + max(category_data['Revenue'])*0.01, 
                               f"${revenue:,.0f}", ha='center', va='bottom', fontsize=10, 
                               fontweight='bold', color='#262730')
            
            # Set background color to match Streamlit
            ax_category.set_facecolor('#f0f2f6')
            fig_category.patch.set_facecolor('#f0f2f6')
            
            plt.tight_layout()
            st.pyplot(fig_category)
            
            # Display category table with better styling
            st.dataframe(category_data[['Category', 'Revenue_Formatted']], 
                        hide_index=True, 
                        column_config={
                            "Category": st.column_config.TextColumn("Category", width="medium"),
                            "Revenue_Formatted": st.column_config.TextColumn("Revenue", width="medium")
                        })
        
        # Vendor Analysis
        if sales_analysis['top_vendors'] is not None:
            st.write("**Sales by Vendor**")
            vendor_data = sales_analysis['top_vendors'].reset_index()
            vendor_data.columns = ['Vendor', 'Revenue']
            vendor_data['Revenue_Formatted'] = vendor_data['Revenue'].apply(lambda x: f"${x:,.0f}")
            
            # Create professional bar chart
            fig_vendor, ax_vendor = plt.subplots(figsize=(12, 6))
            
            # Use a different professional color palette for vendors
            vendor_colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43']
            
            bars = ax_vendor.bar(range(len(vendor_data)), vendor_data['Revenue'], 
                               color=vendor_colors[:len(vendor_data)], alpha=0.8, edgecolor='white', linewidth=1)
            
            # Professional styling
            ax_vendor.set_title('Revenue by Vendor', fontsize=16, fontweight='bold', pad=20, color='#262730')
            ax_vendor.set_xlabel('Vendor', fontsize=12, color='#262730')
            ax_vendor.set_ylabel('Revenue ($)', fontsize=12, color='#262730')
            
            # Clean x-axis labels
            ax_vendor.set_xticks(range(len(vendor_data)))
            ax_vendor.set_xticklabels(vendor_data['Vendor'], rotation=45, ha='right', fontsize=10)
            
            # Remove spines for cleaner look
            ax_vendor.spines['top'].set_visible(False)
            ax_vendor.spines['right'].set_visible(False)
            ax_vendor.spines['left'].set_color('#e0e0e0')
            ax_vendor.spines['bottom'].set_color('#e0e0e0')
            
            # Add subtle grid
            ax_vendor.grid(axis='y', alpha=0.3, color='#e0e0e0', linestyle='-', linewidth=0.5)
            ax_vendor.set_axisbelow(True)
            
            # Add value labels on bars with professional styling
            for i, (bar, revenue) in enumerate(zip(bars, vendor_data['Revenue'])):
                height = bar.get_height()
                ax_vendor.text(bar.get_x() + bar.get_width()/2, height + max(vendor_data['Revenue'])*0.01, 
                             f"${revenue:,.0f}", ha='center', va='bottom', fontsize=10, 
                             fontweight='bold', color='#262730')
            
            # Set background color to match Streamlit
            ax_vendor.set_facecolor('#f0f2f6')
            fig_vendor.patch.set_facecolor('#f0f2f6')
            
            plt.tight_layout()
            st.pyplot(fig_vendor)
            
            # Display vendor table with better styling
            st.dataframe(vendor_data[['Vendor', 'Revenue_Formatted']], 
                        hide_index=True,
                        column_config={
                            "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
                            "Revenue_Formatted": st.column_config.TextColumn("Revenue", width="medium")
                        })
        
        # Sales Analysis Summary
        st.subheader("📋 Sales Analysis Summary")
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.write("**Key Metrics:**")
            st.write(f"• Weekly Revenue: ${sales_analysis['weekly_revenue']:,.2f}")
            st.write(f"• Weekly Orders: {sales_analysis['weekly_orders']:.0f}")
            st.write(f"• Analysis Period: {sales_period_weeks:.1f} weeks")
            
        with summary_col2:
            st.write("**Data Overview:**")
            st.write(f"• Total Line Items: {len(filtered_data):,}")
            st.write(f"• Date Range: {start_date} to {end_date}")
            st.write(f"• Categories: {len(sales_analysis['top_products']) if sales_analysis['top_products'] is not None else 0}")
            st.write(f"• Vendors: {len(sales_analysis['top_vendors']) if sales_analysis['top_vendors'] is not None else 0}")
        
        st.caption("Dashboard powered by Shopify data analysis.")
    else:
        st.info("Enter your Shopify domain and access token to begin analysis.")

if __name__ == "__main__":
    main() 