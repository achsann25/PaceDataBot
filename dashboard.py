import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import json

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

# --- LOAD DATA DARI GOOGLE SHEETS ---
def load_data():
    try:
        # 1. Ambil string JSON mentah dari Secrets (Nama variabel: json_creds)
        creds_raw = st.secrets["json_creds"]
        
        # 2. Ubah teks menjadi dictionary agar bisa dibaca library Google
        creds_dict = json.loads(creds_raw)
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 3. Login menggunakan dictionary
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 4. Buka spreadsheet (Pastikan nama file sama persis)
        sheet = client.open("PaceDataBot").sheet1 
        
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Konversi kolom Tanggal
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        # Fungsi bantu konversi pace (MM:SS) ke total detik untuk grafik
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

# --- EKSEKUSI DASHBOARD ---
df = load_data()

if not df.empty:
    st.title("🏃‍♂️ Running Performance Analytics")
    st.markdown(f"**User:** achsan | **Database:** Google Sheets Live")
    st.markdown("---")

    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_dist = df['Jarak (KM)'].sum()
        st.metric("Total Jarak", f"{total_dist:.2f} KM")
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
        name='Pace (Detik)',
        line=dict(color='#00FFFF', width=4), 
        marker=dict(size=10),
        hovertemplate='Tanggal: %{x}<br>Pace: %{y}s/km<extra></extra>'
    ))

    # Garis Heart Rate (Orange) - Y-Axis Kanan
    fig.add_trace(go.Scatter(
        x=df['Tanggal'], 
        y=df['HR'], 
        name='Heart Rate',
        line=dict(color='#FF4500', width=2, dash='dot'), 
        yaxis='y2',
        hovertemplate='Tanggal: %{x}<br>HR: %{y} BPM<extra></extra>'
    ))

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
