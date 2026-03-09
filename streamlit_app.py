import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import os
from pyproj import Transformer

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

# --- FUNGSI CARI FAIL ---
def find_file(name_variants):
    for variant in name_variants:
        if os.path.exists(variant):
            return variant
    return None

# Mencari fail data ukur atau point
file_path = find_file(["point.csv", "POINT.csv", "Point.csv", "data ukur.csv", "data_ukur.csv"])
image_file = find_file(["gmbr_puoR.png", "logo.png"])

# --- FUNGSI TRANSFORMASI KOORDINAT ---
def convert_coords(df):
    try:
        # Transformasi dari Kertau/Johor Grid (4390) ke WGS84 (4326)
        # Sila pastikan library 'pyproj' ada dalam requirements.txt
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        
        # Ekstrak E dan N, pastikan ia adalah float
        e_vals = df['E'].astype(float).values
        n_vals = df['N'].astype(float).values
        
        lon, lat = transformer.transform(e_vals, n_vals)
        df['lon'] = lon
        df['lat'] = lat
        return df
    except Exception as e:
        st.error(f"Ralat Transformasi Koordinat: {e}")
        return df

# --- BAHAGIAN TAJUK ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if image_file: st.image(image_file, width=180)

with col_text:
    st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

st.divider()

# 2. PROSES DATA & PLOTTING
try:
    if file_path:
        df = pd.read_csv(file_path)
        
        # Pembersihan data (buang baris kosong jika ada)
        df = df.dropna(subset=['E', 'N'])
        
        # Transformasi
        df = convert_coords(df)
        
        centroid_lat = df['lat'].mean()
        centroid_lon = df['lon'].mean()
        
        # Pengiraan Luas (Formula Surveyor)
        luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

        fig = go.Figure()

        # A. LUKIS POLYGON & SEMPADAN
        lats = list(df['lat']) + [df['lat'].iloc[0]]
        lons = list(df['lon']) + [df['lon'].iloc[0]]
        
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='lines+markers',
            line=dict(width=4, color='#00FF00'),
            marker=dict(size=12, color='red'),
            fill="toself",
            fillcolor="rgba(0, 255, 0, 0.2)",
            text=list(df['STN']) + [df['STN'].iloc[0]],
            hoverinfo='text'
        ))

        # B. LABEL STESEN
        fig.add_trace(go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='text',
            text=df['STN'],
            textposition="top right",
            textfont=dict(size=14, color="white", family="Arial Black"),
            showlegend=False
        ))

        # C. LABEL LUAS
        fig.add_trace(go.Scattermapbox(
            lat=[centroid_lat],
            lon=[centroid_lon],
            mode='text',
            text=[f"LUAS: {luas:.2f} m²"],
            textfont=dict(size=22, color="yellow", family="Arial Black"),
            showlegend=False
        ))

        # --- KONFIGURASI MAPBOX (SATELLITE ALTERNATIF) ---
        fig.update_layout(
            mapbox=dict(
                # Menggunakan style Esri World Imagery (Lebih stabil untuk Plotly)
                style="white-bg",
                layers=[{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": [
                        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ]
                }],
                center=dict(lat=centroid_lat, lon=centroid_lon),
                zoom=17
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=750,
            showlegend=False,
            paper_bgcolor="#0E1117"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 3. METRIK & JADUAL
        st.divider()
        c1, c2, c3 = st.columns(3)
        perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
        
        c1.metric("Bil. Stesen", len(df))
        c2.metric("Perimeter", f"{perimeter:.3f} m")
        c3.metric("Luas Tanah", f"{luas:.2f} m²")

        st.subheader("Data Koordinat")
        st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)

    else:
        st.error("Fail data (point.csv) tidak dijumpai dalam folder.")

except Exception as e:
    st.error(f"Berlaku ralat sistem: {e}")
