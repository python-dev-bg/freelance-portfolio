# 📈 CPI Explorer Dashboard

A high-performance, interactive dashboard to explore **Consumer Price Index (CPI)** trends across Denmark and the Netherlands, with contextual benchmarks like oil, gold, treasury yields, exchange rates, and food price indices.

Built with **Polars**, **Panel**, and **HoloViews**, this tool showcases modern Python dashboard engineering — ideal for analysts, researchers, and economists.

---

## 🎯 Features

- 🗂 Country and CPI type selection (Total, Food)
- 📅 Date range filtering
- 🔁 Change mode:
  - `Index` (2015 = 100)
  - `MoM %` – Month-over-Month % change
  - `YoY %` – Year-over-Year % change
- 📌 KPI cards for latest values
- 📊 Interactive line chart with hover
- 📥 Export filtered data as CSV
- ⚡ Fast Polars backend
- 🌐 Includes global benchmarks:
  - Oil (Brent)
  - USD/EUR Exchange Rate
  - US 10-Year Treasury Yield
  - FAO Food Price Index
  - ECB Food Commodity Index
---

## 🗂 Project Structure

This repository hosts multiple tiers of CPI analysis dashboards:

- [`bronze-tier`](CPI%20Explorer/bronze-tier) – Basic CPI Explorer (✅ complete)
- `silver-tier` *(coming soon)* – Prediction models with benchmark correlation
- `gold-tier` *(planned)* – Advanced forecasting and anomaly detection

Each tier has its own README with installation and usage instructions.

#### There is a dedicated README file for each sub project with great explanations and installation instructions
---