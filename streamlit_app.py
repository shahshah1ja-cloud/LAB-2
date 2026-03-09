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

file_path = find_file(["point.csv", "POINT.csv", "Point.csv", "data_ukur.csv"])
image_file = find_file(["gmbr_puoR.png", "logo.png"])

# --- FUNGSI TRANSFORMASI (KERTAU 4390 KE WGS84) ---
def convert_coords(df):
    try:
        # Menukar koordinat Johor Grid ke Lat/Lon dunia
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        e_vals = pd.to_numeric(df['E'], errors='coerce').values
        n_vals = pd.to_numeric(df['N'], errors='coerce').values
        lon, lat = transformer.transform(e_vals, n_vals)
        df['lon'] = lon
        df['lat'] = lat
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"Ralat Transformasi: {e}")
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
        df = convert_coords(df)
        
        if not df.empty:
            centroid_lat = df['lat'].mean()
            centroid_lon = df['lon'].mean()
            luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

            fig = go.Figure()

            # A. LUKIS POLYGON LOT (HIJAU TERANG)
            lats = list(df['lat']) + [df['lat'].iloc[0]]
            lons = list(df['lon']) + [df['lon'].iloc[0]]
            
            fig.add_trace(go.Scattermapbox(
                lat=lats, lon=lons,
                mode='lines+markers',
                line=dict(width=4, color='#00FF00'),
                marker=dict(size=10, color='red'),
                fill="toself",
                fillcolor="rgba(0, 255, 0, 0.3)",
                text=list(df['STN']) + [df['STN'].iloc[0]],
                hoverinfo='text'
            ))

            # B. LABEL STESEN
            fig.add_trace(go.Scattermapbox(
                lat=df['lat'], lon=df['lon'],
                mode='text',
                text=df['STN'],
                textposition="top right",
                textfont=dict(size=14, color="white", family="Arial Black"),
                showlegend=False
            ))

            # C. LABEL LUAS DI TENGAH
            fig.add_trace(go.Scattermapbox(
                lat=[centroid_lat], lon=[centroid_lon],
                mode='text',
                text=[f"LUAS: {luas:.2f} m²"],
                textfont=dict(size=18, color="yellow", family="Arial Black"),
                showlegend=False
            ))

            # --- KONFIGURASI GOOGLE SATELLITE (FORCE SATELLITE) ---
            fig.update_layout(
                mapbox=dict(
                    # Menggunakan gaya 'open-street-map' sebagai pelapik bawah
                    style="open-street-map",
                    layers=[{
                        "below": 'traces',
                        "sourcetype": "raster",
                        "source": [
                            # Menggunakan Server Google Satellite (lyrs=s untuk satelit murni)
                            "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                        ]
                    }],
                    center=dict(lat=centroid_lat, lon=centroid_lon),
                    zoom=18
                ),
                margin=dict(l=0, r=0, t=0, b=0),
                height=750,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # 3. METRIK & JADUAL
            st.divider()
            c1, c2, c3 = st.columns(3)
            perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
            
            c1.metric("Bil. Stesen", len(df))
            c2.metric("Perimeter", f"{perimeter:.3f} m")
            c3.metric("Luas Tanah", f"{luas:.2f} m²")

            st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
        else:
            st.error("Data koordinat dalam CSV tidak dapat dibaca.")
    else:
        st.error("Fail 'point.csv' tidak dijumpai.")

except Exception as e:
    st.error(f"Ralat teknikal: {e}")
