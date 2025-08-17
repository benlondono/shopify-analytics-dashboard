# 🚀 Shopify Multi-Store Dashboard Setup Guide

## What We've Built
A private Streamlit dashboard that connects to your two Shopify stores:
- **BatterBox Sports** (batterboxsports.myshopify.com)
- **Groovy Golfer** (groovygolfer.myshopify.com)

## 🔑 Step 1: Get Your Shopify API Keys

1. **Go to your Shopify admin** for each store
2. **Navigate to Apps → App and sales channel settings**
3. **Click "Develop apps"**
4. **Create a new app** or use existing one
5. **Under "Admin API access scopes"** enable:
   - `read_orders`
   - `read_products` 
   - `read_customers`
6. **Install the app** and copy the **Admin API access token**

## 🔧 Step 2: Update the Dashboard

1. **Open `shopify_dashboard.py`**
2. **Replace the placeholder tokens:**
   ```python
   STORES = {
       "BatterBox Sports": {
           "domain": "batterboxsports.myshopify.com",
           "access_token": "YOUR_ACTUAL_BATTERBOX_TOKEN_HERE"
       },
       "Groovy Golfer": {
           "domain": "groovygolfer.myshopify.com", 
           "access_token": "YOUR_ACTUAL_GROOVY_GOLFER_TOKEN_HERE"
       }
   }
   ```

## 🖥️ Step 3: Run the Dashboard

### Option A: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run shopify_dashboard.py
```

### Option B: Internal Server Deployment
1. **Upload to your organization's server/VM**
2. **Install Python and dependencies**
3. **Run with:**
   ```bash
   streamlit run shopify_dashboard.py --server.port 8501 --server.address 0.0.0.0
   ```
4. **Access via: `http://your-server-ip:8501`**

## 🔒 Security Features

✅ **Hardcoded credentials** - No environment variables to manage  
✅ **Internal deployment** - No public internet exposure  
✅ **Private network access** - Only your organization can access  
✅ **No third-party hosting** - Runs on your own infrastructure  

## 📊 Dashboard Features

- **Real-time store connection status**
- **Revenue comparison between stores**
- **Daily/weekly revenue trends**
- **Order analysis and metrics**
- **Customer insights**
- **Interactive charts and tables**

## 🚨 Important Notes

- **Keep your API tokens secure** - Don't share the code publicly
- **Monitor API usage** - Shopify has rate limits
- **Regular updates** - Refresh data as needed
- **Backup your tokens** - Store them securely

## 🆘 Troubleshooting

- **Connection failed?** Check your API token and domain
- **No data showing?** Verify API permissions are correct
- **Dashboard won't start?** Check Python dependencies are installed

## 🎯 Next Steps

1. **Get your API tokens** from Shopify
2. **Update the code** with real tokens
3. **Test locally** first
4. **Deploy to your internal server**
5. **Share with your team** via private network

Your dashboard will be much more reliable than the web app we were trying to build! 🎉 