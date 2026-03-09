import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import os
from pyproj import Transformer

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

# --- SIDEBAR (PENENTUKURAN OFFSET) ---
with st.sidebar:
    st.title("Sesi: :green[Adam]")
    if st.button("Log Keluar"):
        st.stop()
    
    st.divider()
    st.subheader("🎯 Penantukur (Offset)")
    offset_n = st.slider("Utara/Selatan (m)", -10.0, 10.0, 0.0, step=0.01)
    offset_e = st.slider("Timur/Barat (m)", -10.0, 10.0, 0.0, step=0.01)
    
    epsg_code = st.text_input("Kod EPSG", "4390")
    
    st.subheader("Muat naik CSV")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["csv"])

# --- FUNGSI CARI FAIL (BACKUP JIKA TIADA UPLOAD) ---
def find_file(name_variants):
    for variant in name_variants:
        if os.path.exists(variant): return variant
    return None

# --- FUNGSI TRANSFORMASI & OFFSET ---
def process_data(df, epsg, off_e, off_n):
    try:
        # Tambah offset pada koordinat asal
        df['E_adj'] = df['E'] + off_e
        df['N_adj'] = df['N'] + off_n
        
        # Tukar ke Lat/Lon (WGS84)
        transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E_adj'].values, df['N_adj'].values)
        df['lat'], df['lon'] = lat, lon
        return df
    except Exception as e:
        st.error(f"Ralat Koordinat: {e}")
        return df

# --- FUNGSI KIRA BEARING & JARAK ---
def get_label(p1, p2):
    de = p2['E'] - p1['E']
    dn = p2['N'] - p1['N']
    dist = math.sqrt(de**2 + dn**2)
    brng = math.degrees(math.atan2(de, dn))
    if brng < 0: brng += 360
    d = int(brng)
    m = int((brng % 1) * 60)
    return f"{d}°{m}'\n{dist:.3f}m", (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2

# --- MAIN LOGIC ---
target_file = uploaded_file if uploaded_file else find_file(["point.csv", "data_ukur.csv"])

if target_file:
    df = pd.read_csv(target_file)
    df = process_data(df, epsg_code, offset_e, offset_n)
    
    centroid_lat, centroid_lon = df['lat'].mean(), df['lon'].mean()
    luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

    fig = go.Figure()

    # 1. LUKIS POLYGON (Kekal Hijau/Kuning seperti gambar)
    lats = list(df['lat']) + [df['lat'].iloc[0]]
    lons = list(df['lon']) + [df['lon'].iloc[0]]
    
    fig.add_trace(go.Scattermapbox(
        lat=lats, lon=lons,
        mode='lines+markers',
        line=dict(width=3, color='yellow'),
        marker=dict(size=8, color='red'),
        fill="toself",
        fillcolor="rgba(0, 255, 0, 0.2)",
        hoverinfo='none'
    ))

    # 2. TAMBAH LABEL BEARING & JARAK PADA GARISAN
    for i in range(len(df)):
        p1 = df.iloc[i]
        p2 = df.iloc[(i + 1) % len(df)]
        txt, m_lat, m_lon = get_label(p1, p2)
        fig.add_trace(go.Scattermapbox(
            lat=[m_lat], lon=[m_lon],
            mode='text',
            text=[txt],
            textfont=dict(size=10, color="#00FF00", family="Arial Black"),
            showlegend=False
        ))

    # --- KONFIGURASI PETA (GOOGLE SATELLITE FIX) ---
    fig.update_layout(
        mapbox=dict(
            style="white-bg",
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": ["https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"]
            }],
            center=dict(lat=centroid_lat, lon=centroid_lon),
            zoom=19 # Zoom lebih dekat seperti dalam gambar
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=700,
        paper_bgcolor="#1E1E1E"
    )

    st.plotly_chart(fig, use_container_width=True)

    # METRIK BAWAH
    c1, c2, c3 = st.columns(3)
    c1.metric("Luas Tanah", f"{luas:.3f} m²")
    c2.metric("Pusat Lat", f"{centroid_lat:.6f}")
    c3.metric("Pusat Lon", f"{centroid_lon:.6f}")
    
else:
    st.info("Sila muat naik fail CSV atau pastikan 'point.csv' ada dalam GitHub.")

# Header Logo & Tajuk (Kekalkan di bawah jika perlu)
st.markdown("<h3 style='text-align: center; color: #00FF00;'>Unit Geomatik - PUO</h3>", unsafe_allow_html=True)
