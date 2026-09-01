import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


ORANGE = "#FF6B35"
NAVY = "#1B1B2F"
GOLD = "#F7B801"
TEAL = "#2A9D8F"
RED = "#D1495B"
PALETTE = [ORANGE, TEAL, GOLD, "#6C63FF", RED, "#4C78A8"]


def _style(fig, title, x=None, y="Average delivery time (minutes)"):
    fig.update_layout(
        title=title, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=12, r=12, t=58, b=12),
        font=dict(color="#E8EDF4"), legend_title_text="",
    )
    if x:
        fig.update_xaxes(title=x, showgrid=False)
    if y:
        fig.update_yaxes(title=y, gridcolor="#283441")
    return fig


def average_bar(df, column, title, label, color=ORANGE):
    data = (df.groupby(column, dropna=False)["Time_taken (min)"].mean().reset_index()
            .sort_values("Time_taken (min)", ascending=False))
    fig = px.bar(data, x=column, y="Time_taken (min)", color=column,
                 color_discrete_sequence=PALETTE, text_auto=".2f")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _style(fig, title, label)


def multiple_deliveries_chart(df):
    data = (df.groupby("multiple_deliveries")["Time_taken (min)"].mean().reset_index()
            .sort_values("multiple_deliveries"))
    fig = px.line(data, x="multiple_deliveries", y="Time_taken (min)", markers=True)
    fig.update_traces(line_color=ORANGE, marker_color=ORANGE, line_width=3)
    return _style(fig, "Average Delivery Time by Bundled Deliveries", "Number of additional deliveries")


def scatter_with_trendline(df, x, title, x_label):
    data = df[[x, "Time_taken (min)"]].dropna()
    fig = px.scatter(data, x=x, y="Time_taken (min)", opacity=0.35,
                     color_discrete_sequence=[ORANGE])
    if len(data) >= 2 and data[x].nunique() > 1:
        slope, intercept = np.polyfit(data[x], data["Time_taken (min)"], 1)
        line_x = np.linspace(data[x].min(), data[x].max(), 100)
        fig.add_trace(go.Scatter(x=line_x, y=slope * line_x + intercept, mode="lines",
                                 name="Linear trend", line=dict(color=NAVY, width=3)))
    corr = data[x].corr(data["Time_taken (min)"])
    fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.98, showarrow=False,
                       text=f"Correlation: {corr:.2f}", bgcolor="#FFF3EE", font=dict(color=NAVY))
    return _style(fig, title, x_label), corr


def weather_traffic_heatmap(df):
    matrix = df.pivot_table(index="Weather_conditions", columns="Road_traffic_density",
                            values="Time_taken (min)", aggfunc="mean")
    preferred_weather = [x for x in ["Fog", "Cloudy", "Windy", "Sandstorms", "Stormy", "Sunny"] if x in matrix.index]
    preferred_traffic = [x for x in ["Low", "Medium", "High", "Jam"] if x in matrix.columns]
    matrix = matrix.reindex(index=preferred_weather, columns=preferred_traffic)
    fig = px.imshow(matrix, text_auto=".2f", color_continuous_scale="YlOrRd", aspect="auto",
                    labels=dict(x="Traffic density", y="Weather condition", color="Minutes"))
    return _style(fig, "Weather × Traffic: Average Delivery Time", y=None)


def correlation_heatmap(df):
    columns = ["Delivery_person_Age", "Delivery_person_Ratings", "Vehicle_condition",
               "multiple_deliveries", "Time_taken (min)", "distance_km"]
    corr = df[columns].corr()
    labels = ["Rider age", "Rider rating", "Vehicle condition", "Multiple deliveries", "Delivery time", "Distance (km)"]
    fig = px.imshow(corr, x=labels, y=labels, text_auto=".2f", zmin=-1, zmax=1,
                    color_continuous_scale="RdBu_r", aspect="auto")
    return _style(fig, "Correlation Across Numeric Delivery Factors", y=None)


def delivery_map(df):
    points = df.dropna(subset=["Restaurant_latitude", "Restaurant_longitude"])
    if len(points) > 8000:
        points = points.sample(8000, random_state=42)
    fig = px.scatter_map(points, lat="Restaurant_latitude", lon="Restaurant_longitude",
                         color="Time_taken (min)", hover_data=["City", "Weather_conditions", "Road_traffic_density"],
                         color_continuous_scale="YlOrRd", zoom=3, height=500)
    fig.update_layout(map_style="carto-darkmatter", margin=dict(l=0, r=0, t=45, b=0),
                      title="Restaurant Order Density and Delivery Time")
    return fig
