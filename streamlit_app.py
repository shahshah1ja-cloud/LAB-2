import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
from pyproj import Transformer

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

# --- MASUKKAN URL RAW GITHUB ANDA DI SINI ---
GITHUB_CSV_URL = "https://raw.githubusercontent.com/username/repo/main/point.csv"

# --- FUNGSI PENGIRAAN BEARING & JARAK ---
def calculate_bearing_distance(p1, p2):
    dx = p2['E'] - p1['E']
    dy = p2['N'] - p1['N']
    dist = math.sqrt(dx**2 + dy**2)
    
    # Pengiraan Azimuth
    brg_rad = math.atan2(dx, dy)
    brg_deg = math.degrees(brg_rad)
    if brg_deg < 0: brg_deg += 360
    
    # Tukar ke format DMS
    d = int(brg_deg)
    m = int((brg_deg - d) * 60)
    s = round((((brg_deg - d) * 60) - m) * 60)
    
    # Gunakan simbol darjah yang bersih
    return f"{d}°{m:02d}'{s:02d}\"\n{dist:.2f}m"

# --- FUNGSI AUTO-CONVERT (EPSG:4390 -> EPSG:4326) ---
def convert_to_wgs84(df):
    try:
        # Inisialisasi transformer: Kertau/Johor Grid ke WGS84
        # always_xy=True supaya input (E, N) dan output (Lon, Lat)
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        
        # Ambil nilai E dan N
        e_vals = df['E'].astype(float).values
        n_vals = df['N'].astype(float).values
        
        # Proses transformasi
        lon, lat = transformer.transform(e_vals, n_vals)
        
        # Simpan semula dalam dataframe
        df['lon'] = lon
        df['lat'] = lat
        return df
    except Exception as e:
        st.error(f"Gagal menukar koordinat: {e}")
        return df

# --- UI HEADER ---
st.markdown("<h1 style='text-align: center; color: white;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #00FF00;'>Unit Geomatik: Plotting Lot Satelit (Johor Grid)</h3>", unsafe_allow_html=True)
st.divider()

# 2. PROSES DATA & PLOTTING
try:
    # Membaca data CSV dari GitHub
    df = pd.read_csv(GITHUB_CSV_URL)
    df = df.dropna(subset=['E', 'N'])
    
    # AUTO CONVERT: Kertau/Johor ke WGS84
    df = convert_to_wgs84(df)
    
    # Cari titik tengah untuk fokus peta
    centroid_lat = df['lat'].mean()
    centroid_lon = df['lon'].mean()
    
    # Pengiraan Luas (Formula Shoelace)
    luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

    fig = go.Figure()

    # A. LUKIS SEMPADAN LOT (POLYGON)
    lats = list(df['lat']) + [df['lat'].iloc[0]]
    lons = list(df['lon']) + [df['lon'].iloc[0]]
    
    fig.add_trace(go.Scattermapbox(
        lat=lats, lon=lons,
        mode='lines+markers',
        line=dict(width=3, color='#00FF00'), # Warna Hijau terang (Glow)
        marker=dict(size=12, color='red', symbol='circle'),
        fill="toself",
        fillcolor="rgba(0, 255, 0, 0.15)",
        hoverinfo='none'
    ))

    # B. LABEL BEARING & JARAK (Diletakkan di tengah-tengah garisan)
    for i in range(len(df)):
        p1 = df.iloc[i]
        p2 = df.iloc[(i + 1) % len(df)]
        
        mid_lat = (p1['lat'] + p2['lat']) / 2
        mid_lon = (p1['lon'] + p2['lon']) / 2
        
        label_text = calculate_bearing_distance(p1, p2)
        
        fig.add_trace(go.Scattermapbox(
            lat=[mid_lat], lon=[mid_lon],
            mode='text',
            text=[label_text],
            textfont=dict(size=11, color="#00FF00", family="Arial Black"),
            showlegend=False
        ))

    # C. LABEL NAMA STESEN (STN)
    fig.add_trace(go.Scattermapbox(
        lat=df['lat'], lon=df['lon'],
        mode='text',
        text=df['STN'],
        textposition="top center",
        textfont=dict(size=13, color="white", family="Arial Black"),
        showlegend=False
    ))

    # --- KONFIGURASI MAPBOX (Google Satellite Look-alike) ---
    fig.update_layout(
        mapbox=dict(
            style="white-bg",
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [
                    # Menggunakan server Esri sebagai alternatif Google Satellite yang percuma & stabil
                    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                ]
            }],
            center=dict(lat=centroid_lat, lon=centroid_lon),
            zoom=19 # Zoom lebih dekat untuk lot bangunan
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=800,
        paper_bgcolor="#0E1117"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 3. PAPARAN DATA METRIK
    st.divider()
    c1, c2, c3 = st.columns(3)
    perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
    
    c1.metric("Bilangan Stesen", len(df))
    c2.metric("Perimeter Lot", f"{perimeter:.3f} m")
    c3.metric("Luas Tanah", f"{luas:.2f} m²")

except Exception as e:
    st.error(f"Sistem tidak dapat memproses CSV. Pastikan URL GitHub betul dan format E,N tersedia. Ralat: {e}")
