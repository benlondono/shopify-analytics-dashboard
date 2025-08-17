# 🚀 Shopify Analytics Dashboard - Streamlit Cloud Deployment

## 📊 What This Is
A professional Shopify analytics dashboard that connects to multiple stores and provides:
- **Multi-store analytics** (BatterBox Sports + Groovy Golfer)
- **Growth comparison** between time periods
- **Revenue tracking** and trend analysis
- **Order analytics** and customer insights
- **Secure authentication** system

## ☁️ Streamlit Cloud Deployment

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Step 1: Push to GitHub
```bash
# Add your files
git add .

# Commit changes
git commit -m "Add Shopify analytics dashboard with authentication"

# Push to GitHub
git push origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `shopify_dashboard.py`
6. Click "Deploy!"

### Step 3: Configure Environment Variables
In Streamlit Cloud, add these environment variables:
- `SHOPIFY_BATTERBOX_TOKEN` = Your BatterBox Sports API token
- `SHOPIFY_GROOVY_GOLFER_TOKEN` = Your Groovy Golfer API token

## 🔐 Security Features
- **Authentication required** before accessing data
- **Hardcoded API keys** (no environment variable exposure)
- **Private dashboard** for internal use only

## 📱 Access
Once deployed, you'll get a URL like:
`https://your-app-name-xyz123.streamlit.app`

## 🔄 Updates
- Push changes to GitHub
- Streamlit Cloud automatically redeploys
- No manual deployment needed

## 🛠️ Customization
Edit these lines in `shopify_dashboard.py`:
```python
correct_username = "your_username"
correct_password = "your_password"
```

## 📞 Support
This dashboard is designed for internal business use with secure Shopify API integration. 