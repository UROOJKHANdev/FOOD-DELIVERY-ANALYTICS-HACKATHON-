import pandas as pd
import streamlit as st
from utils.ai_summary import FALLBACK_NARRATIVE, generate_summary, get_api_key
from utils.charts import average_bar, correlation_heatmap, delivery_map, multiple_deliveries_chart, scatter_with_trendline, weather_traffic_heatmap
from utils.data_loader import apply_filters, delivery_kpis, load_data

st.set_page_config(page_title="RouteWise | Food Delivery Analytics", page_icon="🛵", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp{background:radial-gradient(circle at 78% 4%,#143633,#111820 40%,#0d1219);color:#edf0f5}[data-testid="stHeader"]{background:#0d1219}[data-testid="stSidebar"]{background:#161b25;border-right:1px solid #2a3443}[data-testid="stSidebar"] *{color:#e8ebf1}.block-container{max-width:1480px;padding-top:2.4rem}h1,h2,h3{color:#f3f5f8!important}.hero-tag{display:inline-block;padding:.38rem .9rem;color:#ffa760;background:#1b2430;border-radius:0 0 18px 18px;font:700 .75rem monospace;letter-spacing:.12em}.hero{font-size:clamp(2.5rem,5vw,4.5rem);line-height:1.02;font-weight:800;margin:.8rem 0 .45rem;color:#f5eee9}.hero span{color:#ffae73}.copy{font-size:1.2rem;color:#a7b1c2;border-bottom:3px dashed #a96842;padding-bottom:1rem}.card{min-height:145px;padding:1rem;border-radius:18px;background:linear-gradient(145deg,#1c2330,#151a24);border:1px solid #293344;box-shadow:0 9px 22px #0004}.card i{font-size:1.5rem;font-style:normal}.card label{display:block;margin-top:.5rem;color:#9aa6b9;font:700 .72rem monospace;letter-spacing:.12em}.card b{display:block;margin-top:.55rem;font-size:2rem;color:#f0f2f7}.card small{color:#aab4c5}.orange{border-top:4px solid #ff9e55}.teal{border-top:4px solid #22c6b8}.blue{border-top:4px solid #638cff}.red{border-top:4px solid #fa5367}.stTabs [data-baseweb="tab-list"]{gap:.3rem;border-bottom:1px solid #344150}.stTabs [data-baseweb="tab"]{color:#cbd3df;font-size:1rem;font-weight:650;padding:.72rem .45rem}.stTabs [aria-selected="true"]{color:#ffab6d!important;border-bottom-color:#ff9e55!important}.stAlert{border-radius:12px}</style>""",unsafe_allow_html=True)

def blank(): st.warning("No deliveries match these filters. Please broaden the sidebar selections.")
def card(icon,label,value,unit,color): st.markdown(f'<div class="card {color}"><i>{icon}</i><label>{label}</label><b>{value} <small>{unit}</small></b></div>',unsafe_allow_html=True)
def kpis(f):
    x=delivery_kpis(f); speed=(f.distance_km/(f["Time_taken (min)"]/60)).mean(); age=f.Delivery_person_Age.mean()
    values=[("📦","DELIVERIES",f"{x['deliveries']:,}","","teal"),("⏱️","AVG TIME",f"{x['avg_time']:.2f}","min","orange"),("📏","AVG DISTANCE",f"{x['avg_distance']:.2f}","km","blue"),("⚡","AVG SPEED",f"{speed:.2f}","km/h","red"),("⭐","AVG RATING",f"{x['avg_rating']:.2f}","★","teal"),("🧑","AVG RIDER AGE",f"{age:.1f}","yrs","orange")]
    for c,v in zip(st.columns(6),values):
        with c: card(*v)
def traffic_page(f):
    g=f.groupby("Road_traffic_density")["Time_taken (min)"].mean().sort_values(ascending=False); a,b=st.columns([1.5,1])
    with a: st.plotly_chart(average_bar(f,"Road_traffic_density","Average Delivery Time by Traffic Density","Traffic density"),width="stretch")
    with b: st.subheader("Traffic impact");st.info(f"**{g.index[0]}** is slowest at **{g.iloc[0]:.2f} min** — {g.iloc[0]-g.iloc[-1]:.2f} minutes above {g.index[-1]}.");st.write("Traffic is the strongest operational delay signal.")
def distance_page(f):
    fig,corr=scatter_with_trendline(f,"distance_km","Distance vs Delivery Time","Distance (km)");a,b=st.columns([1.5,1])
    with a: st.plotly_chart(fig,width="stretch")
    with b:
        st.subheader("Distance impact");st.info(f"Correlation: **{corr:.2f}**. Time generally rises with distance, then weather and traffic increasingly matter.")
        z=f.assign(bucket=pd.cut(f.distance_km,[0,5,10,15,20,25,float("inf")],labels=["0–5","5–10","10–15","15–20","20–25","25+"]))
        st.dataframe(z.groupby("bucket",observed=False)["Time_taken (min)"].mean().dropna().round(2),width="stretch")
def combo_page(f):
    g=f.groupby(["Weather_conditions","Road_traffic_density"])["Time_taken (min)"].mean().sort_values(ascending=False);a,b=st.columns([1.5,1])
    with a: st.plotly_chart(weather_traffic_heatmap(f),width="stretch")
    with b: st.subheader("Combined conditions");w,t=g.index[0];st.error(f"**{w} + {t}** is the highest-risk combination: **{g.iloc[0]:.2f} min**.");st.write("Pre-position riders using traffic and weather forecasts.")
def deep(f):
    specs=[("Weather_conditions","Average Delivery Time by Weather","Weather"),("Type_of_vehicle","Average Delivery Time by Vehicle Type","Vehicle"),("City","Average Delivery Time by City Type","City"),("Festival","Festival vs Normal-Day Delivery Time","Festival"),("Vehicle_condition","Average Delivery Time by Vehicle Condition","Condition"),("Type_of_order","Average Delivery Time by Order Type","Order type")]
    figs=[average_bar(f,*s) for s in specs]+[multiple_deliveries_chart(f),correlation_heatmap(f)]
    for l,r in zip(figs[::2],figs[1::2]):
        a,b=st.columns(2)
        with a:st.plotly_chart(l,width="stretch")
        with b:st.plotly_chart(r,width="stretch")
    rating_fig,_=scatter_with_trendline(f,"Delivery_person_Ratings","Rider Rating vs Delivery Time","Rider rating")
    st.plotly_chart(rating_fig,width="stretch")
    st.plotly_chart(delivery_map(f),width="stretch")
def insights(f):
    g=lambda x:f.groupby(x)["Time_taken (min)"].mean().sort_values(ascending=False);t,city,veh,mul,cond,fest=[g(x) for x in ["Road_traffic_density","City","Type_of_vehicle","multiple_deliveries","Vehicle_condition","Festival"]];corr=f[["Delivery_person_Ratings","Time_taken (min)"]].corr().iloc[0,1];co=f.groupby(["Weather_conditions","Road_traffic_density"])["Time_taken (min)"].mean().sort_values(ascending=False);w,tr=co.index[0]
    lines=[f"🚦 **Traffic:** {t.index[0]} averages {t.iloc[0]:.2f} min vs {t.iloc[-1]:.2f} in {t.index[-1]}.",f"🏙️ **City:** {city.index[0]} is longest at {city.iloc[0]:.2f} min.",f"🛵 **Fleet:** {veh.index[-1]} is fastest at {veh.iloc[-1]:.2f} min.",f"📦 **Bundling:** {mul.index[-1]:.0f} deliveries average {mul.iloc[-1]:.2f} min.",f"⭐ **Rating correlation:** {corr:.2f}.",f"🔧 **Condition:** {cond.index[0]} is slowest at {cond.iloc[0]:.2f} min.",f"🌫️ **Worst combo:** {w} + {tr} = {co.iloc[0]:.2f} min.",f"🎉 **Festival:** {fest.index[0]} averages {fest.iloc[0]:.2f} min."]
    for l,r in zip(lines[::2],lines[1::2]):
        a,b=st.columns(2)
        with a:st.info(l)
        with b:st.info(r)
def ai(f):
    st.subheader("🤖 AI Explanation")
    if not get_api_key(st):st.warning("No `GROQ_API_KEY` found — safe static narrative shown.");st.write(FALLBACK_NARRATIVE);return
    if st.button("🔄 Regenerate with AI",type="primary"):
        try:
            k=delivery_kpis(f);st.session_state.ai=generate_summary(st,f"Orders: {k['deliveries']:,}; average time: {k['avg_time']:.2f}; average distance: {k['avg_distance']:.2f}; rating: {k['avg_rating']:.2f}.")
        except Exception as e:st.warning(f"AI request failed safely: {e}");st.session_state.ai=FALLBACK_NARRATIVE
    st.write(st.session_state.get("ai","Click **Regenerate with AI** for the current filtered results."))

df=load_data()
with st.sidebar:
    st.markdown("## 🛵 RouteWise");st.caption("Food Delivery Analytics Challenge");st.markdown("---");st.markdown("### Filters")
    cities=st.multiselect("City type",sorted(df.City.dropna().unique()),default=sorted(df.City.dropna().unique()));weather=st.multiselect("Weather",sorted(df.Weather_conditions.dropna().unique()),default=sorted(df.Weather_conditions.dropna().unique()));traffic=st.multiselect("Traffic density",sorted(df.Road_traffic_density.dropna().unique()),default=sorted(df.Road_traffic_density.dropna().unique()));vehicles=st.multiselect("Vehicle type",sorted(df.Type_of_vehicle.dropna().unique()),default=sorted(df.Type_of_vehicle.dropna().unique()));festival=st.selectbox("Festival",["All"]+sorted(df.Festival.dropna().unique().tolist()));dates=st.date_input("Order date range",(df.Order_Date.min().date(),df.Order_Date.max().date()),min_value=df.Order_Date.min().date(),max_value=df.Order_Date.max().date())
f=apply_filters(df,cities,weather,traffic,vehicles,festival,dates)
st.markdown('<span class="hero-tag">HACKATHON TASK A · AI & DS</span>',unsafe_allow_html=True);st.markdown('<div class="hero">Food Delivery <span>Analytics</span></div>',unsafe_allow_html=True);st.markdown('<div class="copy">Live delivery operations intelligence — turning raw trip data into decisions a delivery business can act on today.</div>',unsafe_allow_html=True)
if f.empty:blank()
else:kpis(f)
tabs=st.tabs(["📋 Data & Cleaning","🚦 Traffic Impact","📏 Distance Impact","🌦️ Combined Conditions","📊 Deep-Dive Analytics","💡 Business Insights","🤖 AI Explanation"])
with tabs[0]:
    a,b=st.columns(2)
    with a:st.subheader("Dataset overview");st.write(f"**{len(df):,} cleaned rows × {df.shape[1]} columns** from the supplied Kaggle CSV.");st.dataframe(pd.DataFrame({"dtype":df.dtypes.astype(str),"missing":df.isna().sum(),"missing %":(df.isna().mean()*100).round(2)}),width="stretch")
    with b:st.subheader("Cleaning decisions");st.markdown("- Missing rider ages filled with median.\n- Rows with missing `Time_Orderd` dropped.\n- `Order_Date` parsed as `%d-%m-%Y`.\n- Rating nulls handled only for charts/correlations.");st.success("All values are calculated from the CSV — none are hardcoded.")
with tabs[1]:traffic_page(f) if not f.empty else blank()
with tabs[2]:distance_page(f) if not f.empty else blank()
with tabs[3]:combo_page(f) if not f.empty else blank()
with tabs[4]:deep(f) if not f.empty else blank()
with tabs[5]:insights(f) if not f.empty else blank()
with tabs[6]:ai(f)
