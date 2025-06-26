# How to Use Your CSV Files with Market Analysis

## Quick Start

1. **Run the CSV analysis script:**
   ```bash
   python3 run_market_analysis_with_csv.py
   ```

2. **When prompted, enter the path to your CSV files**
   - Example: `C:\Users\YourName\Desktop\sales_data.csv`
   - Or relative path: `./data/sales.csv`

## CSV File Formats

### 1. Sales Data CSV
**Required columns:**
- `date` - Date of sale (YYYY-MM-DD format)
- `product_id` - Product identifier
- `quantity` - Number of units sold
- `price` - Price per unit

**Optional columns:**
- `season` - Season (1-4)
- `marketing_spend` - Marketing budget
- `competitor_price` - Competitor's price

**Example sales.csv:**
```csv
date,product_id,quantity,price,season,marketing_spend,competitor_price
2023-01-01,PROD001,50,25.99,1,2000,24.50
2023-01-02,PROD002,30,45.00,1,2500,42.00
2023-01-03,PROD001,75,25.99,1,1800,26.00
```

### 2. Search Data CSV
**Required columns:**
- `keyword` - Search term
- `search_volume` - Number of searches
- `conversion_rate` - Conversion rate (0-1)

**Example search.csv:**
```csv
keyword,search_volume,conversion_rate
"buy shoes",1200,0.045
"running shoes",850,0.067
"athletic footwear",650,0.052
"comfortable shoes",920,0.038
```

### 3. Customer Feedback CSV
**Required columns:**
- `feedback_text` - Customer review text

**Optional columns:**
- `rating` - Rating (1-5)

**Example feedback.csv:**
```csv
feedback_text,rating
"Great product, very satisfied with the quality",5
"Shipping was slow but product is good",4
"Customer service needs improvement",2
"Amazing features, worth the price",5
```

## Step-by-Step Instructions

### Step 1: Prepare Your CSV Files
1. **Export your data** from your system (Excel, database, etc.)
2. **Save as CSV** format
3. **Ensure column names match** the expected format above
4. **Place files** in a folder you can easily access

### Step 2: Run the Analysis
```bash
python3 run_market_analysis_with_csv.py
```

### Step 3: Enter File Paths
When prompted, enter the full path to your CSV files:

**For Windows:**
```
C:\Users\YourName\Documents\sales_data.csv
```

**For Mac/Linux:**
```
/Users/YourName/Documents/sales_data.csv
```

**Relative paths (if files are in same folder):**
```
./sales_data.csv
```

### Step 4: Review Results
The script will show:
- ✅ Data loading confirmation
- 📊 Sales analysis with AI predictions
- 🔍 Search keyword clustering
- 💬 Customer feedback analysis
- 🎯 AI-generated marketing insights

## Example Output

```
🚀 CSV Market Analysis
==================================================

📊 Sales Data Analysis:
Enter path to sales CSV file: ./sales_data.csv
✅ Loaded sales data: 365 records
   Date range: 2023-01-01 to 2023-12-31
   Products: 15
   Total Revenue: $1,234,567.89
   Average Daily Sales: $3,382.38
   AI Model R² Score: 0.847

🔍 Feature Importance:
   price: 0.342
   marketing_spend: 0.298
   competitor_price: 0.187
   season: 0.173

🔍 Search Data Analysis:
Enter path to search CSV file: ./search_data.csv
✅ Loaded search data: 50 keywords
   Average search volume: 750
   Average conversion rate: 0.055
   Total Keywords: 50
   High Potential Keywords: 12

🎯 Top 5 High-Potential Keywords:
   "buy shoes": 1200 searches, 0.045 conversion
   "running shoes": 850 searches, 0.067 conversion
   "athletic footwear": 650 searches, 0.052 conversion

==================================================
🎯 AI-Generated Insights:
==================================================
📈 Sales: 'price' is the most important factor affecting sales
🔍 SEO: Focus on 'buy shoes' - high volume with good conversion
⭐ Customer: Strong satisfaction (avg rating: 4.2/5)

✅ Analysis complete!
```

## Troubleshooting

### Common Issues:

1. **"File not found" error:**
   - Check the file path is correct
   - Use forward slashes (/) or double backslashes (\\\\) in Windows paths

2. **"No module named 'pandas'" error:**
   - Install required packages: `python3 -m pip install pandas numpy scikit-learn matplotlib seaborn`

3. **Column name errors:**
   - Ensure your CSV has the exact column names shown above
   - Check for extra spaces or special characters

4. **Date format errors:**
   - Use YYYY-MM-DD format for dates
   - Example: `2023-01-15` not `01/15/2023`

### Data Requirements:

- **Minimum data:** At least 10 records for meaningful analysis
- **Date format:** YYYY-MM-DD
- **Numeric columns:** Should contain only numbers
- **Text columns:** Should contain only text

## Customization

You can modify the script to:
- Add more analysis types
- Change the AI models used
- Customize the output format
- Add data validation rules

## Next Steps

After running the analysis:
1. **Review the insights** for actionable recommendations
2. **Export results** to Excel or other formats
3. **Create visualizations** for presentations
4. **Set up regular analysis** by automating the script

Need help? Check the error messages and ensure your CSV files match the expected format! 