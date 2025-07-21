# 🎯 CPI Explorer – Silver Tier

## Overview
The Silver-tier CPI Explorer builds upon the Bronze version by adding advanced correlation analysis between food CPI and key benchmark indices. It's designed to help users identify how changes in benchmarks relate to CPI movements over time.

### Key Enhancements
- **Auto-download** of ECB, FAO, FRED-backed data when possible  
- **EMA smoothing** (3- and 6-month spans) to reduce noise  
- **Pearson & Spearman correlations** between CPI and benchmarks (raw & EMA)  
- **Rolling correlation** plots to track evolving relationships  
- **KPI cards** highlighting strongest/weakest relationships  
- Tabbed layout: **CPI Trends** and **Correlation Analysis**

---

## 📊 Features

### 1. CPI Trends (Tab 1)
- Time-series plots of selected CPI types (Index / MoM % / YoY %)  
- Emphasis on food-related indices for chosen country  
- EMA smoothing applied for cleaner visualization

### 2. Correlation Analysis (Tab 2)
- Bar charts grouped by correlation type (Pearson / Spearman / EMA variants)  
- Tabular KPIs showing highest and lowest correlated benchmarks  
- Rolling-correlation heatmaps revealing temporal dynamics  
- Correlation type and strength controls to toggle views

---

## ⚙️ How It Works

1. **Data Loading**  
   - CSV files & API downloads are loaded via `data_loader`, preprocessed into Polars DataFrames, and merged  
   - AUTO‑download removes manual steps where possible

2. **EMA Smoothing**  
   - Smoothed series (3- & 6-month) are created using Polars’ `ewm_mean`

3. **Correlation Computation**  
   - For each CPI/benchmark pair:  
     - Pearson & Spearman correlations on: raw, EMA3, EMA6  
   - KPIs: identify strongest/weakest benchmarks per correlation type  
   - Summary stats: average absolute correlation + count of “strong” correlations (>|0.7|)

4. **Rolling-Correlation**  
   - Calculates 12-month rolling Pearson correlation  
   - Ideal for spotting shifts in benchmark–CPI relationship over time

5. **Dashboard UI (Panel)**  
   - **Controls**: country, CPI types, benchmarks, date range, correlation mode & strength  
   - **Plot Area**: Two tabs  
     - **Tab 1**: CPI time-series plots  
     - **Tab 2**: Correlation insights—bar charts, heatmaps & KPI cards

---

## 🚀 Setup

```bash
# 1. Clone the repo & navigate
git clone https://github.com/python-dev-bg/freelance-portfolio.git
cd freelance-portfolio/CPI-Explorer/silver-tier

# 2. Install dependencies
python -m venv venv
source venv/bin/activate      # macOS/Linux
# .\venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 3. Launch dashboard
python main.py

# 4. Stop with:
Ctrl+C
```
The app should automatically open in your browser.  
If not, visit: http://localhost:5007
