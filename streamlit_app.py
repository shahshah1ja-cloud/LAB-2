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

file_ukur = find_file(["data ukur.csv", "data_ukur.csv", "DATA UKUR.csv"])
file_point = find_file(["point.csv", "POINT.csv", "Point.csv"])
image_file = find_file(["gmbr_puoR.png", "logo.png"])

# --- FUNGSI AUTO CONVERT (EPSG:4390 KE EPSG:4326) ---
def convert_coords(df):
    try:
        # EPSG:4390 adalah Kertau (RSO) / Johor Grid
        # EPSG:4326 adalah WGS84 (Lat/Lon) yang digunakan oleh Google/Mapbox
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        
        # Prosedur XY (Easting, Northing) ke (Lon, Lat)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        df['lon'] = lon
        df['lat'] = lat
        return df
    except Exception as e:
        st.error(f"Ralat Transformasi Koordinat: {e}")
        return df

# --- TAJUK ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if image_file: st.image(image_file, width=180)

with col_text:
    st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

st.divider()

# 2. PROSES DATA & PLOTTING
try:
    if file_ukur:
        # Membaca fail CSV
        df = pd.read_csv(file_ukur)
        
        # Auto Convert Kertau ke WGS84
        df = convert_coords(df)
        
        centroid_lat, centroid_lon = df['lat'].mean(), df['lon'].mean()
        luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

        # Plotly Mapbox untuk Satellite yang Jelas
        fig = go.Figure()

        # 1. Garisan Sempadan Lot (Warna Hijau Terang)
        # Menghubungkan titik-titik stesen
        lats = list(df['lat']) + [df['lat'].iloc[0]]
        lons = list(df['lon']) + [df['lon'].iloc[0]]
        
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='lines+markers',
            line=dict(width=4, color='#00FF00'),
            marker=dict(size=10, color='red'),
            fill="toself",
            fillcolor="rgba(0, 255, 0, 0.2)", # Warna hijau lutsinar di dalam lot
            hoverinfo='text',
            text=df['STN'].tolist() + [df['STN'].iloc[0]]
        ))

        # 2. Label Nama Stesen
        fig.add_trace(go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='text',
            text=df['STN'],
            textposition="top right",
            textfont=dict(size=14, color="white", family="Arial Black"),
            showlegend=False
        ))

        # 3. Label Luas di Tengah Lot
        fig.add_trace(go.Scattermapbox(
            lat=[centroid_lat],
            lon=[centroid_lon],
            mode='text',
            text=[f"LUAS: {luas:.2f} m²"],
            textfont=dict(size=20, color="yellow", family="Arial Black"),
            showlegend=False
        ))

        # --- KONFIGURASI MAPBOX (GOOGLE/ESRI SATELLITE STYLE) ---
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": [
                        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ]
                }],
                center=dict(lat=centroid_lat, lon=centroid_lon),
                zoom=18 # Zoom tinggi untuk kejelasan
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=750,
            showlegend=False,
            paper_bgcolor="#0E1117"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 3. METRIK & DATA
        st.divider()
        c1, c2, c3 = st.columns(3)
        perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
        
        c1.metric("Bil. Stesen", len(df))
        c2.metric("Perimeter", f"{perimeter:.3f} m")
        c3.metric("Luas Tanah", f"{luas:.2f} m²")

        if file_point:
            st.subheader("Data Koordinat Asal (Kertau/Johor Grid)")
            st.dataframe(pd.read_csv(file_point), use_container_width=True)

    else:
        st.error("Ralat: Fail 'data ukur.csv' tidak dijumpai. Pastikan fail ada di GitHub.")

except Exception as e:
    st.error(f"Berlaku ralat sistem: {e}")
