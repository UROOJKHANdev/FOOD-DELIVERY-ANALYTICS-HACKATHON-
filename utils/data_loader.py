from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "food_delivery_dataset.csv"
REQUIRED_COLUMNS = {
    "Delivery_person_Age", "Delivery_person_Ratings", "Order_Date", "Time_Orderd",
    "Weather_conditions", "Road_traffic_density", "Vehicle_condition", "Type_of_order",
    "Type_of_vehicle", "multiple_deliveries", "Festival", "City", "Time_taken (min)",
    "distance_km",
}


@st.cache_data(show_spinner="Loading and cleaning delivery data…")
def load_data(path: str = str(DATA_PATH)) -> pd.DataFrame:
    """Load the supplied CSV and apply the notebook's cleaning steps exactly."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")

    # Notebook cleaning steps: median age fill, missing Time_Orderd removal, and date parsing.
    df["Delivery_person_Age"] = df["Delivery_person_Age"].fillna(df["Delivery_person_Age"].median())
    df = df.dropna(subset=["Time_Orderd"]).copy()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], format="%d-%m-%Y")
    return df


def apply_filters(df: pd.DataFrame, cities, weather, traffic, vehicles, festival, date_range):
    """Return a filtered view; an empty multi-select intentionally means all values."""
    filtered = df.copy()
    if cities:
        filtered = filtered[filtered["City"].isin(cities)]
    if weather:
        filtered = filtered[filtered["Weather_conditions"].isin(weather)]
    if traffic:
        filtered = filtered[filtered["Road_traffic_density"].isin(traffic)]
    if vehicles:
        filtered = filtered[filtered["Type_of_vehicle"].isin(vehicles)]
    if festival != "All":
        filtered = filtered[filtered["Festival"] == festival]
    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[filtered["Order_Date"].between(start, end)]
    return filtered


def delivery_kpis(df: pd.DataFrame) -> dict:
    return {
        "deliveries": len(df),
        "avg_time": df["Time_taken (min)"].mean(),
        "avg_distance": df["distance_km"].mean(),
        "avg_rating": df["Delivery_person_Ratings"].mean(),
    }
