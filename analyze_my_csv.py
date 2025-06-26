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

def test_shopify_connection(shop_domain, access_token):
    """Test if Shopify API credentials are working"""
    print("🔍 Testing Shopify API connection...")
    
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

def get_shopify_credentials():
    """Get Shopify store credentials from user"""
    print("🔗 Shopify Store Connection:")
    shop_domain = input("Enter your Shopify store domain (e.g., your-store.myshopify.com): ").strip()
    access_token = input("Enter your Shopify access token: ").strip()
    
    if not shop_domain or not access_token:
        print("❌ Both shop domain and access token are required.")
        return None, None
    
    # Clean up shop domain
    if not shop_domain.startswith('https://'):
        shop_domain = f"https://{shop_domain}"
    
    # Test the connection
    if not test_shopify_connection(shop_domain, access_token):
        print("❌ Could not connect to Shopify. Please check your credentials.")
        return None, None
    
    return shop_domain, access_token

def fetch_shopify_orders(shop_domain, access_token, days_back=90):
    """Fetch orders from Shopify API"""
    print(f"📊 Fetching Shopify orders from the last {days_back} days...")
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    # Calculate date range - fix the date calculation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates properly for Shopify API
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    all_orders = []
    
    try:
        # Simplified API call without pagination first
        url = f"{shop_domain}/admin/api/2023-10/orders.json"
        params = {
            'status': 'any',
            'created_at_min': start_date_str,
            'created_at_max': end_date_str,
            'limit': 50  # Start with smaller limit
        }
        
        print(f"   🔗 Making API request to: {url}")
        print(f"   📅 Date range: {start_date_str} to {end_date_str}")
        
        response = requests.get(url, headers=headers, params=params)
        
        # Print response details for debugging
        print(f"   📊 Response status: {response.status_code}")
        print(f"   📊 Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"   ❌ Error response: {response.text}")
            return None
            
        response.raise_for_status()
        
        data = response.json()
        orders = data.get('orders', [])
        
        if orders:
            all_orders.extend(orders)
            print(f"   ✅ Fetched {len(orders)} orders successfully")
        else:
            print("   ⚠️ No orders found in the specified date range")
        
        print(f"✅ Successfully fetched {len(all_orders)} orders from Shopify")
        return all_orders
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching orders: {e}")
        if "400" in str(e):
            print("💡 400 Bad Request - This usually means:")
            print("   • Invalid date format")
            print("   • Missing API permissions")
            print("   • Invalid access token")
            print("   • Incorrect shop domain")
        elif "401" in str(e):
            print("💡 401 Unauthorized - Check your access token")
        elif "403" in str(e):
            print("💡 403 Forbidden - Check your API permissions")
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

def load_shopify_data():
    """Main function to load data from Shopify"""
    print("🛍️ Shopify Data Loading")
    print("=" * 50)
    
    # Get credentials
    shop_domain, access_token = get_shopify_credentials()
    if not shop_domain or not access_token:
        return None
    
    # Get time range
    try:
        days_back = int(input("Enter number of days to analyze (default 90): ").strip() or "90")
        if days_back <= 0:
            print("❌ Days must be positive. Using 90 days.")
            days_back = 90
    except ValueError:
        print("❌ Invalid input. Using 90 days.")
        days_back = 90
    
    # Calculate weeks from days
    sales_period_weeks = days_back / 7.0
    
    # Fetch data
    orders = fetch_shopify_orders(shop_domain, access_token, days_back)
    if not orders:
        return None
    
    products = fetch_shopify_products(shop_domain, access_token)
    
    # Process data
    data = process_shopify_data(orders, products)
    if data is None:
        return None
    
    print(f"\n📋 Shopify Data Overview:")
    print(f"   Columns: {list(data.columns)}")
    print(f"   Total line items: {len(data)}")
    print(f"   Date range: {data['order_date'].min()} to {data['order_date'].max()}")
    print(f"   Analysis period: {days_back} days ({sales_period_weeks:.1f} weeks)")
    print(f"   Sample data:")
    print(data.head(3).to_string())
    
    # Store the calculated weeks in the data for later use
    data.attrs['sales_period_weeks'] = sales_period_weeks
    
    return data

def get_sales_period():
    print("\n📅 Sales Period Information:")
    print("Enter the time period this sales data represents:")
    while True:
        try:
            weeks = float(input("Number of weeks (e.g., 6 for 6 weeks): "))
            if weeks > 0:
                return weeks
            else:
                print("❌ Please enter a positive number.")
        except ValueError:
            print("❌ Please enter a valid number.")

def analyze_sales_data(data, sales_period_weeks):
    print("\n🔍 Analyzing Shopify sales data...")
    
    # Use Shopify data structure
    total_col = 'line_total'  # Total revenue from line items
    total_revenue = data[total_col].sum()
    total_orders = data['order_id'].nunique()  # Count unique orders
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    weekly_revenue = total_revenue / sales_period_weeks
    weekly_orders = total_orders / sales_period_weeks
    
    print(f"📈 Sales Summary:")
    print(f"   Total Revenue: ${total_revenue:,.2f}")
    print(f"   Total Orders: {total_orders:,}")
    print(f"   Average Order Value: ${avg_order_value:.2f}")
    print(f"   Weekly Revenue: ${weekly_revenue:,.2f}")
    print(f"   Weekly Orders: {weekly_orders:.0f}")
    
    # Analyze product types
    product_col = 'product_type'
    if product_col in data.columns:
        top_products = data.groupby(product_col)[total_col].sum().sort_values(ascending=False).head(5)
        print(f"\n🏆 Top Product Categories:")
        for product, revenue in top_products.items():
            print(f"   {product}: ${revenue:,.2f}")
    
    # Analyze vendors
    vendor_col = 'vendor'
    if vendor_col in data.columns:
        top_vendors = data.groupby(vendor_col)[total_col].sum().sort_values(ascending=False).head(5)
        print(f"\n🏢 Top Vendors:")
        for vendor, revenue in top_vendors.items():
            print(f"   {vendor}: ${revenue:,.2f}")
    
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

def predict_sales_trends(sales_analysis):
    print("\n🤖 AI Sales Trend Prediction:")
    weekly_revenue = sales_analysis['weekly_revenue']
    weekly_orders = sales_analysis['weekly_orders']
    weeks = np.arange(1, 53).reshape(-1, 1)  # Next 52 weeks
    revenue_model = LinearRegression()
    revenue_model.fit(weeks[:3], [weekly_revenue * 0.95, weekly_revenue, weekly_revenue * 1.05])
    revenue_prediction = revenue_model.predict(weeks)
    orders_model = LinearRegression()
    orders_model.fit(weeks[:3], [weekly_orders * 0.95, weekly_orders, weekly_orders * 1.05])
    orders_prediction = orders_model.predict(weeks)
    print(f"📊 52-Week Revenue Forecast:")
    print(f"   Current Weekly Revenue: ${weekly_revenue:,.2f}")
    print(f"   Predicted 26-Week Revenue: ${revenue_prediction[25]:,.2f}")
    print(f"   Predicted 52-Week Revenue: ${revenue_prediction[51]:,.2f}")
    print(f"   Projected Annual Growth: {((revenue_prediction[51] - weekly_revenue) / weekly_revenue * 100):.1f}%")
    print(f"\n📊 52-Week Order Forecast:")
    print(f"   Current Weekly Orders: {weekly_orders:.0f}")
    print(f"   Predicted 26-Week Orders: {orders_prediction[25]:.0f}")
    print(f"   Predicted 52-Week Orders: {orders_prediction[51]:.0f}")
    return {
        'revenue_prediction': revenue_prediction,
        'orders_prediction': orders_prediction,
        'projected_annual_growth': ((revenue_prediction[51] - weekly_revenue) / weekly_revenue * 100)
    }

def generate_engraved_decanter_ideas(sales_analysis):
    print("\n🍷 AI-Generated Engraved Decanter Ideas (Data-Driven):")
    
    # Analyze data patterns
    top_products = sales_analysis['top_products']
    top_vendors = sales_analysis['top_vendors']
    avg_order_value = sales_analysis['avg_order_value']
    total_revenue = sales_analysis['total_revenue']
    
    # Extract insights from data
    insights = {
        'top_categories': [],
        'top_vendors': [],
        'price_segment': '',
        'market_size': '',
        'customer_preferences': []
    }
    
    # Analyze top product categories
    if top_products is not None and len(top_products) > 0:
        insights['top_categories'] = list(top_products.index[:3])  # Top 3 categories
        for category in top_products.index:
            category_lower = category.lower()
            if any(word in category_lower for word in ['gift', 'personalized', 'custom']):
                insights['customer_preferences'].append('personalization')
            if any(word in category_lower for word in ['golf', 'sport', 'outdoor', 'fitness']):
                insights['customer_preferences'].append('sports/outdoor')
            if any(word in category_lower for word in ['corporate', 'business', 'office']):
                insights['customer_preferences'].append('corporate')
            if any(word in category_lower for word in ['wedding', 'bridal', 'groomsmen']):
                insights['customer_preferences'].append('wedding')
            if any(word in category_lower for word in ['luxury', 'premium', 'high-end']):
                insights['customer_preferences'].append('luxury')
    
    # Analyze top vendors
    if top_vendors is not None and len(top_vendors) > 0:
        insights['top_vendors'] = list(top_vendors.index[:3])  # Top 3 vendors
        for vendor in top_vendors.index:
            vendor_lower = vendor.lower()
            if any(word in vendor_lower for word in ['groovy', 'modern', 'trendy']):
                insights['customer_preferences'].append('modern/trendy')
            if any(word in vendor_lower for word in ['traditional', 'classic', 'heritage']):
                insights['customer_preferences'].append('traditional')
    
    # Determine price segment based on average order value
    if avg_order_value > 500:
        insights['price_segment'] = 'luxury'
        base_price_range = "$199-399"
    elif avg_order_value > 200:
        insights['price_segment'] = 'premium'
        base_price_range = "$129-249"
    else:
        insights['price_segment'] = 'standard'
        base_price_range = "$79-159"
    
    # Determine market size
    if total_revenue > 100000:
        insights['market_size'] = 'large'
    elif total_revenue > 50000:
        insights['market_size'] = 'medium'
    else:
        insights['market_size'] = 'small'
    
    # Generate data-driven decanter ideas
    decanter_ideas = []
    
    # Idea 1: Based on top performing category
    if insights['top_categories']:
        top_category = insights['top_categories'][0]
        category_lower = top_category.lower()
        
        if 'golf' in category_lower:
            idea = {
                "name": f"Premium {top_category} Commemorative Decanter",
                "description": f"Elegant crystal decanter with customizable {top_category} engraving, perfect for golf tournaments and club events",
                "target_audience": "Golf clubs, tournament organizers, golf enthusiasts",
                "price_point": base_price_range,
                "rationale": f"Based on strong '{top_category}' performance (${top_products[top_category]:,.0f} revenue)"
            }
        elif 'groomsmen' in category_lower or 'wedding' in category_lower:
            idea = {
                "name": f"Wedding Party {top_category} Decanter Collection",
                "description": f"Personalized decanter set with wedding party engraving, building on successful {top_category} sales",
                "target_audience": "Brides and grooms, wedding planners, bridal boutiques",
                "price_point": base_price_range,
                "rationale": f"Leverages top-performing '{top_category}' category (${top_products[top_category]:,.0f} revenue)"
            }
        else:
            idea = {
                "name": f"{top_category} Themed Premium Decanter",
                "description": f"Custom decanter featuring {top_category} design elements, capitalizing on category success",
                "target_audience": f"{top_category} enthusiasts, gift buyers, collectors",
                "price_point": base_price_range,
                "rationale": f"Based on highest-revenue category '{top_category}' (${top_products[top_category]:,.0f})"
            }
        decanter_ideas.append(idea)
    
    # Idea 2: Based on vendor performance
    if insights['top_vendors']:
        top_vendor = insights['top_vendors'][0]
        vendor_lower = top_vendor.lower()
        
        if 'groovy' in vendor_lower:
            idea = {
                "name": f"Modern {top_vendor} Co-Branded Decanter",
                "description": f"Contemporary decanter design featuring {top_vendor} branding and modern aesthetics",
                "target_audience": f"{top_vendor} customers, modern lifestyle enthusiasts",
                "price_point": base_price_range,
                "rationale": f"Partnership opportunity with top vendor '{top_vendor}' (${top_vendors[top_vendor]:,.0f} revenue)"
            }
        else:
            idea = {
                "name": f"{top_vendor} Signature Collection Decanter",
                "description": f"Premium decanter featuring {top_vendor} signature design elements and quality standards",
                "target_audience": f"{top_vendor} loyal customers, premium gift buyers",
                "price_point": base_price_range,
                "rationale": f"Capitalizes on successful vendor partnership '{top_vendor}' (${top_vendors[top_vendor]:,.0f} revenue)"
            }
        decanter_ideas.append(idea)
    
    # Idea 3: Based on price segment analysis
    if insights['price_segment'] == 'luxury':
        idea = {
            "name": "Heritage Crystal Luxury Decanter",
            "description": "Ultra-premium crystal decanter with family crest or corporate logo engraving",
            "target_audience": "High-net-worth individuals, luxury brands, corporate executives",
            "price_point": "$299-599",
            "rationale": f"Targets luxury market based on high average order value (${avg_order_value:.0f})"
        }
    elif insights['price_segment'] == 'premium':
        idea = {
            "name": "Professional Achievement Decanter",
            "description": "Premium decanter for corporate milestones, retirements, and professional achievements",
            "target_audience": "Corporate clients, HR departments, professional services",
            "price_point": "$149-299",
            "rationale": f"Premium positioning based on solid average order value (${avg_order_value:.0f})"
        }
    else:
        idea = {
            "name": "Everyday Elegance Decanter",
            "description": "Accessible premium decanter for daily use and casual gifting",
            "target_audience": "General consumers, gift buyers, everyday luxury seekers",
            "price_point": "$89-179",
            "rationale": f"Accessible pricing based on current average order value (${avg_order_value:.0f})"
        }
    decanter_ideas.append(idea)
    
    # Idea 4: Based on customer preferences
    if 'corporate' in insights['customer_preferences']:
        idea = {
            "name": "Corporate Milestone Commemorative Decanter",
            "description": "Professional decanter for company anniversaries, mergers, and business achievements",
            "target_audience": "Corporate clients, business consultants, event planners",
            "price_point": base_price_range,
            "rationale": "Addresses strong corporate customer base identified in sales data"
        }
    elif 'sports/outdoor' in insights['customer_preferences']:
        idea = {
            "name": "Sports Championship Celebration Decanter",
            "description": "Team-branded decanter for championship celebrations and sports memorabilia",
            "target_audience": "Sports teams, fans, memorabilia collectors, sports bars",
            "price_point": base_price_range,
            "rationale": "Leverages sports/outdoor customer preferences from sales analysis"
        }
    else:
        idea = {
            "name": "Seasonal Celebration Decanter",
            "description": "Themed decanter for holidays, seasons, and special occasions",
            "target_audience": "General consumers, holiday shoppers, occasion gift buyers",
            "price_point": base_price_range,
            "rationale": "Broad appeal based on general customer behavior patterns"
        }
    decanter_ideas.append(idea)
    
    # Idea 5: Based on market size and growth potential
    if insights['market_size'] == 'large':
        idea = {
            "name": "Limited Edition Collector's Decanter",
            "description": "Exclusive numbered decanter series for collectors and enthusiasts",
            "target_audience": "Collectors, enthusiasts, premium market segments",
            "price_point": "$199-399",
            "rationale": f"Large market size (${total_revenue:,.0f} revenue) supports premium collector market"
        }
    else:
        idea = {
            "name": "Customizable Gift Decanter",
            "description": "Versatile decanter with multiple personalization options for various occasions",
            "target_audience": "General gift buyers, personal shoppers, occasion planners",
            "price_point": base_price_range,
            "rationale": f"Scalable product for current market size (${total_revenue:,.0f} revenue)"
        }
    decanter_ideas.append(idea)
    
    # Display the data-driven ideas
    for i, idea in enumerate(decanter_ideas, 1):
        print(f"\n   {i}. {idea['name']}")
        print(f"      💡 {idea['description']}")
        print(f"      🎯 Target: {idea['target_audience']}")
        print(f"      💰 Price: {idea['price_point']}")
        print(f"      📊 {idea['rationale']}")
    
    # Show data insights summary
    print(f"\n📊 Data Insights Used:")
    print(f"   • Top Categories: {', '.join(insights['top_categories']) if insights['top_categories'] else 'None'}")
    print(f"   • Top Vendors: {', '.join(insights['top_vendors']) if insights['top_vendors'] else 'None'}")
    print(f"   • Price Segment: {insights['price_segment'].title()}")
    print(f"   • Market Size: {insights['market_size'].title()}")
    print(f"   • Customer Preferences: {', '.join(set(insights['customer_preferences'])) if insights['customer_preferences'] else 'None'}")
    
    return decanter_ideas

def generate_marketing_strategies(sales_analysis, predictions):
    print("\n🎯 AI Marketing Strategy Recommendations:")
    weekly_revenue = sales_analysis['weekly_revenue']
    avg_order_value = sales_analysis['avg_order_value']
    projected_growth = predictions['projected_annual_growth']
    strategies = []
    if weekly_revenue > 50000:
        strategies.append("🚀 **Scale-Up Strategy**: High revenue indicates market demand. Consider:")
        strategies.append("   • Expand to new product categories (decanter line)")
        strategies.append("   • Increase marketing budget by 20-30%")
        strategies.append("   • Explore international markets")
    if avg_order_value > 400:
        strategies.append("💰 **Premium Positioning**: High AOV suggests luxury market. Focus on:")
        strategies.append("   • Premium product photography and descriptions")
        strategies.append("   • VIP customer programs")
        strategies.append("   • Upselling to higher-value items")
    if projected_growth > 5:
        strategies.append("📈 **Growth Acceleration**: Positive growth trajectory. Implement:")
        strategies.append("   • Customer retention programs")
        strategies.append("   • Referral incentives")
        strategies.append("   • Seasonal marketing campaigns")
    if sales_analysis['top_products'] is not None:
        top_category = sales_analysis['top_products'].index[0]
        if 'groomsmen' in top_category.lower():
            strategies.append("💍 **Wedding Market Focus**: Strong groomsmen performance. Target:")
            strategies.append("   • Wedding expos and bridal shows")
            strategies.append("   • Wedding planner partnerships")
            strategies.append("   • Seasonal wedding marketing (spring/summer)")
    if sales_analysis['top_vendors'] is not None:
        top_vendor = sales_analysis['top_vendors'].index[0]
        if 'groovy' in top_vendor.lower():
            strategies.append("🎨 **Brand Partnership**: Strong Groovy brand performance. Consider:")
            strategies.append("   • Co-branded decanter products")
            strategies.append("   • Cross-promotion opportunities")
            strategies.append("   • Bundle deals with existing products")
    strategies.append("📱 **Digital Marketing**: Based on your data, focus on:")
    strategies.append("   • Social media advertising (Facebook/Instagram)")
    strategies.append("   • Google Shopping campaigns")
    strategies.append("   • Email marketing for repeat customers")
    strategies.append("   • Influencer partnerships in gift/lifestyle niches")
    for strategy in strategies:
        print(f"   {strategy}")

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
    print("🚀 AI-Powered Shopify Sales Analysis Tool")
    print("=" * 50)
    
    # Load Shopify data
    sales_data = load_shopify_data()
    if sales_data is None:
        print("❌ Could not load Shopify data. Exiting.")
        return
    
    # Use the automatically calculated weeks from Shopify data
    sales_period_weeks = sales_data.attrs.get('sales_period_weeks', 12.9)  # Default to ~90 days
    
    sales_analysis = analyze_sales_data(sales_data, sales_period_weeks)
    if sales_analysis is None:
        print("❌ Analysis failed. Exiting.")
        return
    
    predictions = predict_sales_trends(sales_analysis)
    decanter_ideas = generate_engraved_decanter_ideas(sales_analysis)
    generate_marketing_strategies(sales_analysis, predictions)
    create_enhanced_visualization(sales_data, sales_analysis, predictions)
    print("\n✅ AI Analysis complete!")

if __name__ == "__main__":
    main() 