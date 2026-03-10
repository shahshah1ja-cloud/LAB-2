import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
from pyproj import Transformer

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

# --- URL GITHUB (GANTIKAN DENGAN URL RAW ANDA) ---
# Contoh: https://raw.githubusercontent.com/username/repo/main/point.csv
GITHUB_CSV_URL = "https://raw.githubusercontent.com/your-username/your-repo/main/point.csv"

# --- FUNGSI PENGIRAAN BEARING & JARAK ---
def calculate_bearing_distance(p1, p2):
    dx = p2['E'] - p1['E']
    dy = p2['N'] - p1['N']
    dist = math.sqrt(dx**2 + dy**2)
    brg = math.degrees(math.atan2(dx, dy))
    if brg < 0: brg += 360
    
    # Format Bearing (DMS ringkas)
    d = int(brg)
    m = int((brg - d) * 60)
    s = int((brg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\"\n{dist:.3f}m"

# --- FUNGSI TRANSFORMASI KOORDINAT ---
def convert_coords(df):
    try:
        # EPSG:4390 (Kertau/Johor Grid) ke EPSG:4326 (WGS84)
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        e_vals = df['E'].astype(float).values
        n_vals = df['N'].astype(float).values
        lon, lat = transformer.transform(e_vals, n_vals)
        df['lon'] = lon
        df['lat'] = lat
        return df
    except Exception as e:
        st.error(f"Ralat Transformasi: {e}")
        return df

# --- BAHAGIAN TAJUK ---
st.markdown("<h1 style='text-align: center; color: white;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #00FF00;'>Unit Geomatik - Paparan Lot Satelit</h3>", unsafe_allow_html=True)
st.divider()

# 2. PROSES DATA
try:
    # Membaca data dari GitHub
    df = pd.read_csv(GITHUB_CSV_URL)
    df = df.dropna(subset=['E', 'N'])
    df = convert_coords(df)
    
    centroid_lat = df['lat'].mean()
    centroid_lon = df['lon'].mean()
    
    # Kira Luas
    luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

    fig = go.Figure()

    # A. LUKIS POLYGON (Sempadan)
    lats = list(df['lat']) + [df['lat'].iloc[0]]
    lons = list(df['lon']) + [df['lon'].iloc[0]]
    
    fig.add_trace(go.Scattermapbox(
        lat=lats, lon=lons,
        mode='lines+markers',
        line=dict(width=3, color='#00FF00'),
        marker=dict(size=10, color='red'),
        fill="toself",
        fillcolor="rgba(0, 255, 0, 0.1)",
        hoverinfo='none'
    ))

    # B. TAMBAH LABEL BEARING & JARAK (Pada setiap garisan)
    for i in range(len(df)):
        p1 = df.iloc[i]
        p2 = df.iloc[(i + 1) % len(df)]
        
        # Cari titik tengah antara dua stesen untuk letak label
        mid_lat = (p1['lat'] + p2['lat']) / 2
        mid_lon = (p1['lon'] + p2['lon']) / 2
        
        label_text = calculate_bearing_distance(p1, p2)
        
        fig.add_trace(go.Scattermapbox(
            lat=[mid_lat], lon=[mid_lon],
            mode='text',
            text=[label_text],
            textfont=dict(size=11, color="#00FF00", family="Arial Bold"),
            showlegend=False
        ))

    # C. LABEL STESEN (STN)
    fig.add_trace(go.Scattermapbox(
        lat=df['lat'], lon=df['lon'],
        mode='text',
        text=df['STN'],
        textposition="top right",
        textfont=dict(size=12, color="white", family="Arial Black"),
        showlegend=False
    ))

    # --- KONFIGURASI MAPBOX (SATELLITE IMAGE) ---
    fig.update_layout(
        mapbox=dict(
            style="white-bg", # Mesti white-bg jika guna custom raster
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [
                    # Menggunakan Esri World Imagery (High Resolution Satellite)
                    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                ]
            }],
            center=dict(lat=centroid_lat, lon=centroid_lon),
            zoom=18
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=700,
        paper_bgcolor="#0E1117"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 3. INFO PANEL
    c1, c2, c3 = st.columns(3)
    perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
    
    c1.metric("Bil. Stesen", len(df))
    c2.metric("Perimeter", f"{perimeter:.3f} m")
    c3.metric("Luas Tanah", f"{luas:.2f} m²")

except Exception as e:
    st.error(f"Sila pastikan URL GitHub betul dan fail boleh diakses. Ralat: {e}")
