import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="Running Analytics", layout="wide")

# Custom CSS untuk gaya Dark Dashboard (Tech Look)
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

# --- LOAD DATA DARI GOOGLE SHEETS (CLOUD VERSION) ---
def load_data():
    try:
        # 1. Ambil dictionary dari Secrets Streamlit (GCP Service Account)
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 2. Login menggunakan dictionary, bukan file fisik
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 3. Buka spreadsheet
        sheet = client.open("PaceDataBot").sheet1 
        
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Konversi kolom Tanggal
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        # Fungsi bantu untuk konversi pace (MM:SS) ke total detik agar bisa diplot ke grafik
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
        st.error(f"Koneksi Google Sheets Gagal: {e}")
        return pd.DataFrame()

# --- MAIN DASHBOARD LOGIC ---
df = load_data()

if not df.empty:
    st.title("🏃‍♂️ Running Performance Analytics")
    st.markdown(f"**User:** achsan | **Status:** Live Database Connected")
    st.markdown("---")

    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_dist = df['Jarak (KM)'].sum()
        st.metric("Total Jarak", f"{total_dist:.2f} KM")
    with col2:
        # Cari pace terkecil (tercepat)
        valid_pace = df[df['pace_sec'] > 0]
        if not valid_pace.empty:
            best_p = valid_pace.iloc[valid_pace['pace_sec'].idxmin()]['Pace']
            st.metric("Personal Best Pace", f"{best_p} /km")
        else:
            st.metric("Personal Best Pace", "-")
    with col3:
        st.metric("Avg HR", f"{int(df['HR'].mean())} BPM")
    with col4:
        st.metric("Sesi Lari", f"{len(df)} Kali")

    # --- ROW 2: CHART ---
    st.subheader("Pace & Heart Rate Trendline")
    
    fig = go.Figure()

    # Garis Pace (Cyan) - Semakin kecil detiknya, semakin tinggi grafiknya (di-invert)
    fig.add_trace(go.Scatter(
        x=df['Tanggal'], 
        y=df['pace_sec'], 
        name='Pace (Detik)',
        line=dict(color='#00FFFF', width=4), 
        marker=dict(size=10),
        hovertemplate='Tanggal: %{x}<br>Pace: %{y} detik<extra></extra>'
    ))

    # Garis Heart Rate (Orange) - Y-Axis sebelah kanan
    fig.add_trace(go.Scatter(
        x=df['Tanggal'], 
        y=df['HR'], 
        name='Heart Rate',
        line=dict(color='#FF4500', width=2, dash='dot'), 
        yaxis='y2',
        hovertemplate='Tanggal: %{x}<br>HR: %{y} BPM<extra></extra>'
    ))

    # Layout Dashboard Styling
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title="Pace (Seconds/KM)", showgrid=False),
        yaxis2=dict(title="Heart Rate (BPM)", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- ROW 3: DATA TABLE ---
    with st.expander("📂 Lihat Detail Data Mentah"):
        st.dataframe(df.sort_values(by='Tanggal', ascending=False), use_container_width=True)

else:
    st.warning("Data belum tersedia. Silakan input lari pertama Anda melalui Bot Telegram!")
