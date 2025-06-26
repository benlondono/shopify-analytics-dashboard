# Shopify Sales Analytics Dashboard

A powerful Streamlit dashboard for analyzing Shopify store performance with live data and interactive visualizations.

## Features

- 📊 **Real-time Shopify Data**: Connect directly to your Shopify store via API
- 📈 **Interactive Charts**: Professional bar charts for categories and vendors
- 📅 **Flexible Date Ranges**: Analyze recent periods or full historical data
- 🎨 **Professional UI**: Clean, modern design that matches Streamlit's aesthetic
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Quick Start

1. **Enter your Shopify credentials:**
   - Store domain (e.g., `your-store` - no need for full URL)
   - Access token from Shopify admin

2. **Choose data range:**
   - Recent Period: Analyze last X days
   - Full History: Analyze entire store history

3. **View your analytics:**
   - Sales trends and metrics
   - Revenue by product category
   - Revenue by vendor
   - Interactive charts and tables

## Setup Instructions

### For Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run shopify_data_analysis.py
   ```

### For Deployment

This app is ready to deploy to Streamlit Cloud:

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy and share the URL

## Shopify API Setup

To get your access token:

1. Go to your Shopify admin
2. Navigate to Apps > Develop apps
3. Create a new app or use existing
4. Configure Admin API access
5. Generate access token with required scopes:
   - `read_orders`
   - `read_products`

## Data Privacy

- All data is processed locally
- No data is stored permanently
- Credentials are not saved
- Uses Shopify's secure API

## Support

For issues or questions, please check the Shopify API documentation or contact your Shopify administrator. 
