from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    ROOT / "cleaned_food_delivery_dataset.csv",
    ROOT / "food_delivery_dataset.csv",
]


@st.cache_data(show_spinner=False)
def load_dataset() -> pd.DataFrame:
    """Load the cleaned food delivery dataset, or build a fallback demo dataset."""
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            df = pd.read_csv(candidate)
            return prepare_dataframe(df)

    try:
        import kagglehub

        dataset_path = kagglehub.dataset_download("uroojazizkhan/food-delivery")
        dataset_dir = Path(dataset_path)
        csv_files = list(dataset_dir.rglob("*.csv"))
        if csv_files:
            df = pd.read_csv(csv_files[0])
            df = prepare_dataframe(df)
            df.to_csv(ROOT / "cleaned_food_delivery_dataset.csv", index=False)
            return df
    except Exception:
        pass

    return prepare_dataframe(create_demo_dataset())


def create_demo_dataset() -> pd.DataFrame:
    """Create a realistic fallback dataset so the dashboard still runs without the Kaggle CSV."""
    rng = np.random.default_rng(42)
    cities = ["Metropolitian", "Urban", "Semi-Urban", "Rural"]
    traffic = ["Low", "Medium", "High", "Jam"]
    weather = ["Sunny", "Cloudy", "Rainy", "Stormy", "Foggy"]
    vehicle = ["bike", "scooter", "car", "auto"]
    order_types = ["Snack", "Beverage", "Meal", "Dessert", "Groceries"]
    festivals = ["Yes", "No"]

    rows = []
    for i in range(1200):
        city = rng.choice(cities)
        traffic_level = rng.choice(traffic)
        weather_cond = rng.choice(weather)
        vehicle_type = rng.choice(vehicle)
        order_type = rng.choice(order_types)
        festival = rng.choice(festivals)
        age = int(rng.integers(20, 50))
        rating = round(float(rng.normal(4.2, 0.5)), 2)
        rating = max(1.0, min(5.0, rating))
        distance = round(float(rng.lognormal(mean=1.2, sigma=0.6)), 2)
        distance = min(max(distance, 1.0), 25.0)
        base_time = 20 + (distance * 3.5)
        traffic_penalty = {"Low": 0, "Medium": 6, "High": 14, "Jam": 25}[traffic_level]
        weather_penalty = {"Sunny": 0, "Cloudy": 2, "Rainy": 8, "Stormy": 16, "Foggy": 10}[weather_cond]
        vehicle_penalty = {"bike": 0, "scooter": 3, "car": 6, "auto": 10}[vehicle_type]
        festival_penalty = 8 if festival == "Yes" else 0
        time_taken = max(12, round(base_time + traffic_penalty + weather_penalty + vehicle_penalty + festival_penalty + rng.normal(0, 6)))
        rows.append(
            {
                "Delivery_person_Age": age,
                "Delivery_person_Ratings": rating,
                "Restaurant_latitude": round(float(rng.uniform(12.9, 13.2)), 6),
                "Restaurant_longitude": round(float(rng.uniform(77.5, 77.8)), 6),
                "Delivery_location_latitude": round(float(rng.uniform(12.9, 13.2)), 6),
                "Delivery_location_longitude": round(float(rng.uniform(77.5, 77.8)), 6),
                "Time_Orderd": f"{rng.integers(0, 24):02d}:{rng.integers(0, 60):02d}",
                "Order_Date": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 200), unit="D"),
                "City": city,
                "Road_traffic_density": traffic_level,
                "Weather_conditions": weather_cond,
                "Type_of_vehicle": vehicle_type,
                "Vehicle_condition": int(rng.integers(1, 5)),
                "Type_of_order": order_type,
                "Festival": festival,
                "multiple_deliveries": int(rng.integers(0, 3)),
                "distance_km": round(distance, 2),
                "Time_taken (min)": int(time_taken),
                "delivery_speed": "fast" if distance < 5 else "medium" if distance < 10 else "slow",
            }
        )

    return pd.DataFrame(rows)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    if "Delivery_person_Age" in df.columns:
        df["Delivery_person_Age"] = pd.to_numeric(df["Delivery_person_Age"], errors="coerce")
        df["Delivery_person_Age"] = df["Delivery_person_Age"].fillna(df["Delivery_person_Age"].median())

    if "Delivery_person_Ratings" in df.columns:
        df["Delivery_person_Ratings"] = pd.to_numeric(df["Delivery_person_Ratings"], errors="coerce")
        df["Delivery_person_Ratings"] = df["Delivery_person_Ratings"].fillna(df["Delivery_person_Ratings"].median())

    if "distance_km" in df.columns:
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
        df["distance_km"] = df["distance_km"].fillna(df["distance_km"].median())

    if "Time_taken (min)" in df.columns:
        df["Time_taken (min)"] = pd.to_numeric(df["Time_taken (min)"], errors="coerce")
        df["Time_taken (min)"] = df["Time_taken (min)"].fillna(df["Time_taken (min)"].median())

    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    elif "Order_Date" not in df.columns and "Order_Date " in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date "], errors="coerce")

    if "Order_Date" in df.columns:
        df["Order_Day"] = df["Order_Date"].dt.day_name()
        df["Order_Month"] = df["Order_Date"].dt.month_name()

    if "Time_Orderd" in df.columns:
        df["Time_Orderd"] = df["Time_Orderd"].astype(str).str.strip()

    if "delivery_speed" not in df.columns and "distance_km" in df.columns:
        conditions = [
            df["distance_km"] < 5,
            df["distance_km"] < 10,
            df["distance_km"] < 15,
        ]
        choices = ["Fast", "Moderate", "Slow"]
        df["delivery_speed"] = np.select(conditions, choices, default="Very Slow")

    df = df.drop_duplicates().reset_index(drop=True)
    return df


def safe_summary(df: pd.DataFrame) -> dict:
    return {
        "orders": int(len(df)),
        "avg_delivery_time": round(float(df["Time_taken (min)"].mean()), 2) if "Time_taken (min)" in df else 0,
        "avg_distance": round(float(df["distance_km"].mean()), 2) if "distance_km" in df else 0,
        "avg_rating": round(float(df["Delivery_person_Ratings"].mean()), 2) if "Delivery_person_Ratings" in df else 0,
        "top_traffic": df.groupby("Road_traffic_density")["Time_taken (min)"].mean().idxmax() if "Road_traffic_density" in df and "Time_taken (min)" in df else "N/A",
    }


def build_business_recommendations(df: pd.DataFrame) -> list[str]:
    recommendations = []

    if {"Road_traffic_density", "Time_taken (min)"}.issubset(df.columns):
        traffic = df.groupby("Road_traffic_density")["Time_taken (min)"].mean().sort_values(ascending=False)
        worst_traffic = traffic.index[0]
        recommendations.append(f"Prioritize dispatch planning for {worst_traffic} traffic conditions; they add the highest delays to orders.")

    if {"Weather_conditions", "Time_taken (min)"}.issubset(df.columns):
        weather = df.groupby("Weather_conditions")["Time_taken (min)"].mean().sort_values(ascending=False)
        worst_weather = weather.index[0]
        recommendations.append(f"Prepare extra rider allocation during {worst_weather} weather, as it increases delivery time the most.")

    if {"City", "Time_taken (min)"}.issubset(df.columns):
        city = df.groupby("City")["Time_taken (min)"].mean().sort_values(ascending=False)
        slow_city = city.index[0]
        recommendations.append(f"Focus service recovery in {slow_city} with demand balancing and rider staging to reduce delay hotspots.")

    if {"Type_of_vehicle", "Time_taken (min)"}.issubset(df.columns):
        vehicle = df.groupby("Type_of_vehicle")["Time_taken (min)"].mean().sort_values()
        fastest = vehicle.index[0]
        recommendations.append(f"Use {fastest} vehicles more aggressively for short-distance and time-sensitive orders to improve SLA performance.")

    if {"distance_km", "Time_taken (min)"}.issubset(df.columns):
        corr = df["distance_km"].corr(df["Time_taken (min)"])
        if pd.notna(corr):
            recommendations.append(f"Distance stays strongly correlated with time (corr = {corr:.2f}); revise route optimization and ETA estimation by service area.")

    if "Festival" in df.columns and "Time_taken (min)" in df.columns:
        festival = df.groupby("Festival")["Time_taken (min)"].mean()
        if len(festival) > 1:
            diff = festival.iloc[0] - festival.iloc[1] if festival.iloc[0] > festival.iloc[1] else festival.iloc[1] - festival.iloc[0]
            recommendations.append(f"Plan extra rider coverage during festival peaks; average delay gaps can reach around {diff:.1f} minutes.")

    return recommendations[:5]


def make_metric_card(title: str, value: str, delta: str = ""):
    st.markdown(
        f"""
        <div style="padding: 1.2rem; border-radius: 0.9rem; background: linear-gradient(135deg, #111827, #1F2937); border: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.8rem;">
            <div style="font-size: 0.8rem; color: #9CA3AF;">{title}</div>
            <div style="font-size: 2rem; font-weight: 700; margin-top: 0.4rem;">{value}</div>
            <div style="font-size: 0.8rem; color: #34D399; margin-top: 0.2rem;">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters(df: pd.DataFrame):
    st.sidebar.header("Filters")

    city_options = sorted(df["City"].dropna().unique().tolist()) if "City" in df else []
    traffic_options = sorted(df["Road_traffic_density"].dropna().unique().tolist()) if "Road_traffic_density" in df else []
    weather_options = sorted(df["Weather_conditions"].dropna().unique().tolist()) if "Weather_conditions" in df else []
    vehicle_options = sorted(df["Type_of_vehicle"].dropna().unique().tolist()) if "Type_of_vehicle" in df else []

    selected_city = st.sidebar.multiselect("City", city_options, default=city_options)
    selected_traffic = st.sidebar.multiselect("Traffic density", traffic_options, default=traffic_options)
    selected_weather = st.sidebar.multiselect("Weather", weather_options, default=weather_options)
    selected_vehicle = st.sidebar.multiselect("Vehicle type", vehicle_options, default=vehicle_options)

    if "Order_Date" in df.columns:
        min_date = df["Order_Date"].min().date()
        max_date = df["Order_Date"].max().date()
        start_date, end_date = st.sidebar.date_input("Date range", [min_date, max_date])
    else:
        start_date, end_date = None, None

    mask = pd.Series(True, index=df.index)
    if selected_city:
        mask &= df["City"].isin(selected_city) if "City" in df else True
    if selected_traffic:
        mask &= df["Road_traffic_density"].isin(selected_traffic) if "Road_traffic_density" in df else True
    if selected_weather:
        mask &= df["Weather_conditions"].isin(selected_weather) if "Weather_conditions" in df else True
    if selected_vehicle:
        mask &= df["Type_of_vehicle"].isin(selected_vehicle) if "Type_of_vehicle" in df else True
    if start_date is not None and end_date is not None and "Order_Date" in df.columns:
        mask &= df["Order_Date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))

    return df[mask].copy()


def main() -> None:
    st.set_page_config(page_title="Food Delivery Analytics", page_icon="🍔", layout="wide")
    st.title("🍔 Food Delivery Analytics Dashboard")

    df = load_dataset()
    filtered_df = render_sidebar_filters(df)

    if filtered_df.empty:
        st.warning("No rows match the selected filters. Please widen the filter range.")
        return

    summary = safe_summary(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        make_metric_card("Total Orders", f"{summary['orders']:,}", "All selected orders")
    with col2:
        make_metric_card("Avg Delivery Time", f"{summary['avg_delivery_time']} min", "Operational benchmark")
    with col3:
        make_metric_card("Avg Distance", f"{summary['avg_distance']} km", "Per delivery")
    with col4:
        make_metric_card("Avg Rating", f"{summary['avg_rating']}/5", "Customer satisfaction")

    st.subheader("Executive summary")
    st.markdown(
        f"The selected segment includes {summary['orders']:,} food deliveries with an average completion time of {summary['avg_delivery_time']} minutes. "
        f"The highest delay pressure is seen in **{summary['top_traffic']}** traffic conditions, which is the best trigger for tactical rider deployment and dynamic dispatching."
    )

    tab1, tab2, tab3 = st.tabs(["Overview", "Operational Insights", "Recommendations"])

    with tab1:
        colA, colB = st.columns(2)
        with colA:
            if {"Road_traffic_density", "Time_taken (min)"}.issubset(filtered_df.columns):
                traffic_summary = filtered_df.groupby("Road_traffic_density")["Time_taken (min)"].mean().reset_index()
                fig = px.bar(
                    traffic_summary,
                    x="Road_traffic_density",
                    y="Time_taken (min)",
                    color="Road_traffic_density",
                    title="Average Delivery Time by Traffic Density",
                    labels={"Road_traffic_density": "Traffic Density", "Time_taken (min)": "Avg Time (min)"},
                )
                st.plotly_chart(fig, use_container_width=True)

        with colB:
            if {"Weather_conditions", "Time_taken (min)"}.issubset(filtered_df.columns):
                weather_summary = filtered_df.groupby("Weather_conditions")["Time_taken (min)"].mean().reset_index()
                fig = px.bar(
                    weather_summary,
                    x="Weather_conditions",
                    y="Time_taken (min)",
                    color="Weather_conditions",
                    title="Average Delivery Time by Weather",
                    labels={"Weather_conditions": "Weather", "Time_taken (min)": "Avg Time (min)"},
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        colC, colD = st.columns(2)
        with colC:
            if {"City", "Time_taken (min)"}.issubset(filtered_df.columns):
                city_summary = filtered_df.groupby("City")["Time_taken (min)"].mean().reset_index()
                fig = px.bar(
                    city_summary,
                    x="City",
                    y="Time_taken (min)",
                    color="City",
                    title="Average Delivery Time by City",
                    labels={"City": "City", "Time_taken (min)": "Avg Time (min)"},
                )
                st.plotly_chart(fig, use_container_width=True)

        with colD:
            if {"Type_of_vehicle", "Time_taken (min)"}.issubset(filtered_df.columns):
                vehicle_summary = filtered_df.groupby("Type_of_vehicle")["Time_taken (min)"].mean().reset_index()
                fig = px.bar(
                    vehicle_summary,
                    x="Type_of_vehicle",
                    y="Time_taken (min)",
                    color="Type_of_vehicle",
                    title="Average Delivery Time by Vehicle Type",
                    labels={"Type_of_vehicle": "Vehicle Type", "Time_taken (min)": "Avg Time (min)"},
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        if {"distance_km", "Time_taken (min)"}.issubset(filtered_df.columns):
            fig = px.scatter(
                filtered_df.sample(min(4000, len(filtered_df)), random_state=1),
                x="distance_km",
                y="Time_taken (min)",
                color="Road_traffic_density",
                opacity=0.65,
                title="Distance vs Delivery Time",
                labels={"distance_km": "Distance (km)", "Time_taken (min)": "Time Taken (min)"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if {"Festival", "Time_taken (min)"}.issubset(filtered_df.columns):
            festival_summary = filtered_df.groupby("Festival")["Time_taken (min)"].mean().reset_index()
            festival_fig = px.bar(
                festival_summary,
                x="Festival",
                y="Time_taken (min)",
                color="Festival",
                title="Festival vs Normal Day Performance",
                labels={"Festival": "Festival", "Time_taken (min)": "Avg Time (min)"},
            )
            st.plotly_chart(festival_fig, use_container_width=True)

        if {"multiple_deliveries", "Time_taken (min)"}.issubset(filtered_df.columns):
            multi_summary = filtered_df.groupby("multiple_deliveries")["Time_taken (min)"].mean().reset_index()
            multi_fig = px.line(
                multi_summary,
                x="multiple_deliveries",
                y="Time_taken (min)",
                markers=True,
                title="Multiple Deliveries vs Delivery Time",
                labels={"multiple_deliveries": "Number of Multiple Deliveries", "Time_taken (min)": "Avg Time (min)"},
            )
            st.plotly_chart(multi_fig, use_container_width=True)

        if {"Delivery_person_Ratings", "Time_taken (min)"}.issubset(filtered_df.columns):
            rating_corr = filtered_df["Delivery_person_Ratings"].corr(filtered_df["Time_taken (min)"])
            st.metric("Rating-to-Time Correlation", f"{rating_corr:.2f}")

    with tab3:
        recommendations = build_business_recommendations(filtered_df)
        for idx, rec in enumerate(recommendations, start=1):
            st.markdown(f"{idx}. {rec}")

        st.markdown("---")
        st.caption("AI-style business logic generated from observed averages, trends, and correlations in the filtered delivery data.")

        report_text = "\n".join(f"{i}. {rec}" for i, rec in enumerate(recommendations, start=1))
        st.download_button(
            label="Download recommendations report",
            data=report_text,
            file_name="food_delivery_recommendations.txt",
            mime="text/plain",
        )

    st.markdown("---")
    st.subheader("Filtered dataset")
    st.dataframe(filtered_df.head(200), use_container_width=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        csv_data,
        file_name="filtered_food_delivery_data.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
