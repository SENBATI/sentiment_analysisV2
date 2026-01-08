import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cassandra.cluster import Cluster
from datetime import datetime
import time
import logging

# --- 1. SETUP LOGGING ---
# This creates a file 'system_events.log' in your project folder
logging.basicConfig(
    filename='system_events.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# --- CONFIGURATION ---
st.set_page_config(
    page_title="Social Sentinel AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DATABASE CONNECTION (Cached) ---
@st.cache_resource
def get_db_session():
    cluster = Cluster(['localhost'])
    session = cluster.connect('social_media')
    return session

session = get_db_session()

# --- CUSTOM CSS (Dark Mode Tweaks) ---
st.markdown("""
<style>
    .metric-card {background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333;}
    .crisis-banner {background-color: #8B0000; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; animation: blink 1s infinite;}
    @keyframes blink { 50% { opacity: 0.7; } }
</style>
""", unsafe_allow_html=True)

# --- MAIN LOOP ---
st.title("Real-Time Brand Reputation Center")

# Create a placeholder that we will overwrite every few seconds
dashboard_placeholder = st.empty()

def fetch_data():
    query = "SELECT * FROM sentiment_aggregates LIMIT 500"
    rows = session.execute(query)
    df = pd.DataFrame(list(rows))
    if not df.empty:
        df['window_start'] = pd.to_datetime(df['window_start'])
        df = df.sort_values('window_start')
    return df

while True:
    df = fetch_data()
    
    with dashboard_placeholder.container():
        if df.empty:
            st.warning("Waiting for data stream...")
            time.sleep(2)
            continue

        # --- LOGIC: CRISIS DETECTION ---
        # Look at the last 1 minute of data
        latest_time = df['window_start'].max()
        recent_df = df[df['window_start'] >= (latest_time - pd.Timedelta(minutes=1))]
        
        # Crisis Threshold: Score < -0.05
        crisis_brands = recent_df[recent_df['avg_sentiment'] < -0.05]['brand'].unique()
        
        # Crisis Threshold
        crisis_df = recent_df[recent_df['avg_sentiment'] < -0.05]
        crisis_brands = crisis_df['brand'].unique()

        # --- 1. ALERT BANNER ---
        if len(crisis_brands) > 0:
            brand_list = ", ".join(crisis_brands)
            st.markdown(f"""
            <div class="crisis-banner">
                CRITICAL ALERT DETECTED: {brand_list}
            </div>
            """, unsafe_allow_html=True)
            st.error(f"Negative sentiment spike detected for: **{brand_list}**. Immediate action required.")
        # LOGGING TO FILE
            # We log the event so you have proof for the project requirement
            for brand in crisis_brands:
                score = crisis_df[crisis_df['brand'] == brand]['avg_sentiment'].min()
                logging.warning(f"CRISIS DETECTED - Brand: {brand} | Score: {score:.3f}")
               
        else:
            st.success("System Status: NOMINAL Monitoring Active")

        # --- 2. KPI ROW ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # Calculate totals
        total_posts = df['post_count'].sum()
        avg_sentiment = df['avg_sentiment'].mean()
        latest_brand = df.iloc[-1]['brand']
        
        kpi1.metric("Total Posts Analyzed", f"{total_posts:,}")
        kpi2.metric("Global Sentiment", f"{avg_sentiment:.2f}", delta_color="normal")
        kpi3.metric("Most Active Brand", latest_brand)
        kpi4.metric("Active Alerts", len(crisis_brands), delta=len(crisis_brands), delta_color="inverse")

        st.divider()

        # --- 3. CHARTS ROW ---
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Sentiment Evolution Live")
            
            # Line Chart with Plotly
            fig_line = px.line(df, x='window_start', y='avg_sentiment', color='brand', 
                               markers=True, title="Sentiment Score over Time (-1.0 to +1.0)")
            fig_line.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="Neutral")
            fig_line.add_hline(y=-0.05, line_dash="dot", line_color="red", annotation_text="Crisis Threshold")
            fig_line.update_layout(height=400, xaxis_title="Time", yaxis_title="Sentiment Score")
            st.plotly_chart(fig_line, use_container_width=True)

        with col_right:
            st.subheader("📊 Volume Distribution")
            
            # Bar Chart
            vol_per_brand = df.groupby('brand')['post_count'].sum().reset_index()
            fig_bar = px.bar(vol_per_brand, x='brand', y='post_count', color='brand',
                             title="Total Posts per Brand")
            fig_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- 4. RAW DATA TABLE (Collapsible) ---
        with st.expander("🔎 View Raw Data Logs"):
            st.dataframe(df.sort_values('window_start', ascending=False).head(50), use_container_width=True)

    # Refresh rate (2 seconds)
    time.sleep(2)