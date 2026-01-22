import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="Running Analytics", layout="wide")

# Custom CSS untuk gaya Dark Dashboard
st.markdown("""
    <style>
    .main { background-color: #0D1117; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA DARI GOOGLE SHEETS ---
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("PaceDataBot").sheet1 # Pastikan nama file sama
    
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Konversi data
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    # Fungsi bantu untuk konversi pace ke detik
    def p2s(p):
        try:
            p = str(p).replace("''", "").split("'")
            return int(p[0]) * 60 + int(p[1])
        except: return 0
    
    df['pace_sec'] = df['Pace'].apply(p2s)
    return df

try:
    df = load_data()

    st.title("🏃‍♂️ Running Performance Analytics")
    st.markdown("---")

    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jarak", f"{df['Jarak (KM)'].sum()} KM")
    with col2:
        best_p = df.iloc[df['pace_sec'].idxmin()]['Pace']
        st.metric("Personal Best Pace", best_p)
    with col3:
        st.metric("Avg HR", f"{int(df['HR'].mean())} BPM")
    with col4:
        st.metric("Sesi Lari", f"{len(df)} Kali")

    # --- ROW 2: CHART ---
    st.subheader("Pace & Heart Rate Trendline")
    
    fig = go.Figure()

    # Garis Pace (Cyan)
    fig.add_trace(go.Scatter(x=df['Tanggal'], y=df['pace_sec'], name='Pace',
                             line=dict(color='#00FFFF', width=4), marker=dict(size=10)))

    # Garis Heart Rate (Orange)
    fig.add_trace(go.Scatter(x=df['Tanggal'], y=df['HR'], name='Heart Rate',
                             line=dict(color='#FF4500', width=2, dash='dot'), yaxis='y2'))

    # Layout Dashboard
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title="Pace (Seconds)", showgrid=False),
        yaxis2=dict(title="Heart Rate (BPM)", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- ROW 3: DATA TABLE ---
    with st.expander("Lihat Detail Data Mentah"):
        st.dataframe(df.sort_values(by='Tanggal', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.info("Pastikan spreadsheet tidak kosong dan nama kolom sesuai (Tanggal, Jarak (KM), Waktu, Pace, HR)")