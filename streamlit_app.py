import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import os

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

# --- FUNGSI TUKAR KOORDINAT (METER KE LAT/LON) ---
# Menggunakan anggaran titik rujukan untuk kawasan Perak/Malaysia
def meter_to_latlon(easting, northing):
    # Titik rujukan anggaran (Base point)
    base_lat = 4.591 # Anggaran Latitud PUO
    base_lon = 101.072 # Anggaran Longitud PUO
    
    # 1 darjah latitud lebih kurang 111,000 meter
    # 1 darjah longitud lebih kurang 111,000 * cos(lat) meter
    lat = base_lat + (northing - 0) / 111111
    lon = base_lon + (easting - 0) / (111111 * math.cos(math.radians(base_lat)))
    return lat, lon

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
        df = pd.read_csv(file_ukur)
        
        # Tambah kolum Lat/Lon untuk Mapbox
        df['lat'], df['lon'] = zip(*df.apply(lambda row: meter_to_latlon(row['E'], row['N']), axis=1))
        
        centroid_lat, centroid_lon = df['lat'].mean(), df['lon'].mean()
        luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))

        # Guna Mapbox untuk Satellite yang Jelas
        fig = go.Figure()

        # 1. Garisan Sempadan (Kekal Hijau)
        # Kita perlu loop untuk setiap segmen garisan
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            
            fig.add_trace(go.Scattermapbox(
                lat=[p1['lat'], p2['lat']],
                lon=[p1['lon'], p2['lon']],
                mode='lines',
                line=dict(width=4, color='#00FF00'),
                hoverinfo='none'
            ))

        # 2. Titik Stesen & Nama Stesen
        fig.add_trace(go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='markers+text',
            marker=dict(size=12, color='red', opacity=1),
            text=df['STN'],
            textposition="top right",
            textfont=dict(size=14, color="white"),
            hoverinfo='text'
        ))

        # 3. Label Luas di Tengah
        fig.add_trace(go.Scattermapbox(
            lat=[centroid_lat],
            lon=[centroid_lon],
            mode='text',
            text=[f"LUAS: {luas:.2f} m²"],
            textfont=dict(size=18, color="yellow", family="Arial Black"),
            showlegend=False
        ))

        # --- KONFIGURASI MAPBOX (SATELLITE) ---
        fig.update_layout(
            mapbox=dict(
                style="white-bg", # Base
                layers=[{
                    "below": 'traces',
                    "sourcetype": "raster",
                    "source": [
                        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ]
                }],
                center=dict(lat=centroid_lat, lon=centroid_lon),
                zoom=18 # Tahap zoom yang tinggi untuk kejelasan
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=700,
            showlegend=False,
            paper_bgcolor="#0E1117"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Metrik
        st.divider()
        c1, c2, c3 = st.columns(3)
        perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
        c1.metric("Bil. Stesen", len(df))
        c2.metric("Perimeter", f"{perimeter:.3f} m")
        c3.metric("Luas Tanah", f"{luas:.2f} m²")

    else:
        st.error("Fail data_ukur.csv tidak dijumpai.")

    # Jadual Point
    if file_point:
        st.subheader("Data Koordinat (Point)")
        st.dataframe(pd.read_csv(file_point), use_container_width=True)

except Exception as e:
    st.error(f"Ralat: {e}")
