import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import json

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="Running Performance Analytics", layout="wide")

# Gaya Dark Dashboard
st.markdown("""
    <style>
    .main { background-color: #0D1117; }
    .stMetric { 
        background-color: #161B22; 
        border: 1px solid #30363D; 
        padding: 15px; 
        border-radius: 10px; 
    }
    [data-testid="stMetricValue"] { color: #00FFFF; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
def load_data():
    try:
        # Mengambil dari Streamlit Secrets
        creds_raw = st.secrets["json_creds"]
        creds_dict = json.loads(creds_raw)
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("PaceDataBot").sheet1 
        data = sheet.get_all_records()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        # Fungsi konversi pace ke detik (untuk perhitungan grafik)
        def p2s(p):
            try:
                p_str = str(p).replace("'", ":")
                parts = p_str.split(":")
                return int(parts[0]) * 60 + int(parts[1])
            except: 
                return 0
        
        df['pace_sec'] = df['Pace'].apply(p2s)
        return df
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.title("🏃‍♂️ Running Performance Analytics")
    st.markdown(f"**User:** achsan | **Database:** Google Sheets Live")
    st.markdown("---")

    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jarak", f"{df['Jarak (KM)'].sum():.2f} KM")
    with col2:
        valid_pace = df[df['pace_sec'] > 0]
        if not valid_pace.empty:
            best_p = valid_pace.iloc[valid_pace['pace_sec'].idxmin()]['Pace']
            st.metric("Best Pace", f"{best_p} /km")
        else:
            st.metric("Best Pace", "-")
    with col3:
        st.metric("Avg HR", f"{int(df['HR'].mean())} BPM")
    with col4:
        st.metric("Total Sesi", f"{len(df)} Kali")

    # --- ROW 2: CHART ---
    st.subheader("Pace & Heart Rate Trendline")
    
    fig = go.Figure()

    # Garis Pace (Cyan)
    fig.add_trace(go.Scatter(
        x=df['Tanggal'], 
        y=df['pace_sec'], 
        name='Pace (min/km)',
        line=dict(color='#00FFFF', width=4, shape='spline'), 
        marker=dict(size=10),
        hovertemplate='Tanggal: %{x}<br>Pace: %{text} /km<extra></extra>',
        text=df['Pace'] # Menampilkan format MM:SS asli saat hover
    ))

    # Garis Heart Rate (Orange)
    fig.add_trace(go.Scatter(
        x=df['Tanggal'], 
        y=df['HR'], 
        name='Heart Rate (BPM)',
        line=dict(color='#FF4500', width=2, dash='dot'), 
        yaxis='y2',
        hovertemplate='Tanggal: %{x}<br>HR: %{y} BPM<extra></extra>'
    ))

    # Pengaturan Sumbu Y agar menampilkan format Waktu (min:sec)
    min_pace = int(df['pace_sec'].min() // 60)
    max_pace = int(df['pace_sec'].max() // 60)
    tick_vals = [i * 60 for i in range(min_pace, max_pace + 2)]
    tick_text = [f"{i}:00" for i in range(min_pace, max_pace + 2)]

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title="Pace (min/km)", 
            showgrid=False,
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_text,
            autorange="reversed" # Membalik sumbu: Pace kecil (cepat) di atas
        ),
        yaxis2=dict(
            title="Heart Rate (BPM)", 
            overlaying='y', 
            side='right', 
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- ROW 3: DATA TABLE ---
    with st.expander("📂 Lihat Detail Data Mentah"):
        st.dataframe(df.sort_values(by='Tanggal', ascending=False), use_container_width=True)

else:
    st.warning("Data belum tersedia. Silakan input lari pertama Anda melalui Bot Telegram!")
