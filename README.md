# 🍔 Food Delivery Analytics Dashboard

A production-ready, interactive Streamlit presentation of the Food Delivery Analytics hackathon project. It loads the supplied raw CSV, applies the original notebook cleaning steps, and calculates every KPI and chart result live.

> Add a dashboard screenshot or GIF here after the first run.

## Features

- Global filters for city, weather, traffic, vehicle, festival, and order date
- Five dashboard pages: Overview, 3 Key Questions, Deep-Dive Analytics, Business Insights, and AI Business Summary
- Thirteen interactive Plotly visuals, including both correlation and weather/traffic heatmaps plus a delivery-density map
- Optional Groq summary generation with a safe fallback narrative when no API key is configured

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. The dashboard expects the dataset at `data/food_delivery_dataset.csv`.

## Optional AI summary

The app works fully without AI. To enable the on-demand Groq summary, set `GROQ_API_KEY` in your environment or create `.streamlit/secrets.toml` locally:

```toml
GROQ_API_KEY = "your-key-here"
```

Never commit that secrets file. For Streamlit Community Cloud, add the key in the app's **Secrets** settings.

## Data credit

Dataset: Kaggle — [uroojazizkhan/food-delivery](https://www.kaggle.com/datasets/uroojazizkhan/food-delivery-dataset). The source CSV is included in `data/` for reproducible local deployment.

## Deploy

Push this repository to GitHub, then create a Streamlit Community Cloud app and select `app.py` as the entry point. Add the optional Groq key through Cloud Secrets.
