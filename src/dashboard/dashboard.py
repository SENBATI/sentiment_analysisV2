import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cassandra.cluster import Cluster
from matplotlib.animation import FuncAnimation
import datetime

# --- CONFIGURATION ---
CASSANDRA_HOST = ['localhost']
KEYSPACE = "social_media"

# Setup Cassandra Connection
cluster = Cluster(CASSANDRA_HOST)
session = cluster.connect(KEYSPACE)

# Setup Plotsb
plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(2, 2)

ax1 = fig.add_subplot(gs[0, 0]) # Sentiment Over Time
ax2 = fig.add_subplot(gs[0, 1]) # Volume per Brand
ax3 = fig.add_subplot(gs[1, 0]) # Sentiment Distribution
ax4 = fig.add_subplot(gs[1, 1]) # Alerts / Raw Text

def fetch_data():
    # Fetch last 1 hour of data
    query = "SELECT * FROM sentiment_aggregates LIMIT 1000"
    rows = session.execute(query)
    df = pd.DataFrame(list(rows))
    return df

def update(frame):
    df = fetch_data()
    
    if df.empty:
        print("Waiting for data...")
        return

    # Convert timestamps
    df['window_start'] = pd.to_datetime(df['window_start'])
    df = df.sort_values('window_start')

    # Clear axes
    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()

    # --- CHART 1: Sentiment Evolution (Line Chart) ---
    for brand in df['brand'].unique():
        subset = df[df['brand'] == brand]
        ax1.plot(subset['window_start'], subset['avg_sentiment'], label=brand, marker='o')
    
    ax1.set_title("Evolution du Sentiment (Temps Réel)")
    ax1.set_ylabel("Score (-1 à +1)")
    ax1.legend(loc='upper left', fontsize='small')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(0, color='white', linewidth=0.5)

    # --- CHART 2: Volume of Posts (Bar Chart) ---
    # Sum post counts per brand
    volume = df.groupby('brand')['post_count'].sum()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    ax2.bar(volume.index, volume.values, color=colors[:len(volume)])
    ax2.set_title("Volume Total des Posts par Brand")
    
    # --- CHART 3: Sentiment Distribution (Stacked Bar) ---
    # Sum pos/neu/neg per brand
    dist = df.groupby('brand')[['positive_count', 'neutral_count', 'negative_count']].sum()
    dist.plot(kind='bar', stacked=True, ax=ax3, color=['green', 'grey', 'red'])
    ax3.set_title("Distribution: Positif vs Neutre vs Négatif")
    ax3.legend(fontsize='small')

# --- CHART 4: Alert Monitor (Text) ---
    # REVISED LOGIC: Higher Sensitivity
    
    # 1. Get the last 5 minutes of data (not just the last split second)
    recent_df = df.tail(30) 
    
    # 2. Threshold raised to -0.05 (Any negative trend triggers it)
    # Since normal is +0.1 to +0.3, a score of -0.05 is definitely a crisis.
    CRISIS_THRESHOLD = -0.05
    
    active_crises = recent_df[recent_df['avg_sentiment'] < CRISIS_THRESHOLD]
    
    # Deduplicate: If "Attijariwafa" appears 3 times, just show the latest one
    if not active_crises.empty:
        active_crises = active_crises.sort_values('window_start', ascending=False).drop_duplicates('brand')

    ax4.clear()
    ax4.axis('off')
    
    if not active_crises.empty:
        # --- CRISIS DETECTED VISUAL ---
        ax4.set_facecolor('#330000') # Dark Red Background
        ax4.text(0.5, 0.85, "ALERTE CRISE", 
                color='red', fontsize=22, fontweight='bold', 
                ha='center', va='center')
        
        y_pos = 0.6
        for idx, row in active_crises.iterrows():
            # Show the brand and the time it happened
            time_str = row['window_start'].strftime('%H:%M:%S')
            msg = f"{row['brand']}\nScore: {row['avg_sentiment']:.2f}\n({time_str})"
            
            ax4.text(0.5, y_pos, msg, 
                    color='white', fontsize=14, fontweight='bold', ha='center', va='center')
            y_pos -= 0.25
    else:
        # --- NORMAL STATE ---
        ax4.set_title("Status du Système", color='white')
        ax4.text(0.5, 0.5, "Système Nominal\nAucune alerte détectée", 
                color='#00ff00', fontsize=14, ha='center', va='center')
        ax4.text(0.5, 0.3, f"(Seuil d'alerte: {CRISIS_THRESHOLD})", 
                color='gray', fontsize=10, ha='center', va='center')

# Run Animation (Updates every 5000ms = 5 seconds)
ani = FuncAnimation(fig, update, interval=5000)
plt.show()