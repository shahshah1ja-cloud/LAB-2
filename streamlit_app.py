import streamlit as st
import pandas as pd
import numpy as np
import math
import os
from pyproj import Transformer
import folium
from streamlit_folium import folium_static

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

# --- FUNGSI TRANSFORMASI ---
def convert_coords(df):
    try:
        transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        e_vals = pd.to_numeric(df['E'], errors='coerce').values
        n_vals = pd.to_numeric(df['N'], errors='coerce').values
        lon, lat = transformer.transform(e_vals, n_vals)
        df['lat'] = lat
        df['lon'] = lon
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"Ralat Transformasi: {e}")
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
    if file_path:
        df = pd.read_csv(file_path)
        df = convert_coords(df)
        
        if not df.empty:
            centroid_lat = df['lat'].mean()
            centroid_lon = df['lon'].mean()
            
            # PETA (Max Zoom 22 supaya imej satelit tidak hilang)
            m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=20, max_zoom=22)

            # GOOGLE HYBRID SATELLITE
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google Satellite',
                name='Google Satellite',
                overlay=False,
                control=True
            ).add_to(m)

            # LUKIS SEMPADAN & TEKS SEJAJAR (RUJUKAN LOGIK PLOTLY ANDA)
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                # Garisan Lot (Kuning)
                locs = [[p1['lat'], p1['lon']], [p2['lat'], p2['lon']]]
                folium.PolyLine(locs, color="yellow", weight=3, opacity=1).add_to(m)
                
                # --- PENGIRAAN JARAK & BEARING (GEOMATIK) ---
                de = p2['E'] - p1['E']
                dn = p2['N'] - p1['N']
                dist = math.sqrt(de**2 + dn**2)
                
                angle_rad = math.atan2(de, dn)
                angle_deg = math.degrees(angle_rad)
                bearing_val = angle_deg if angle_deg >= 0 else angle_deg + 360
                brng_str = f"{int(bearing_val)}°{int((bearing_val%1)*60)}'"

                # --- LOGIK ROTASI TEKS (MENGIKUT CODING RUJUKAN ANDA) ---
                # Menggunakan atan2(dn, de) untuk sudut kecerunan relatif terhadap paksi-X
                line_angle_rad = math.atan2(dn, de)
                line_angle_deg = math.degrees(line_angle_rad)
                
                # Laraskan supaya tulisan sentiasa boleh dibaca (tidak terbalik)
                if line_angle_deg > 90:
                    line_angle_deg -= 180
                elif line_angle_deg < -90:
                    line_angle_deg += 180
                
                # Dalam CSS/Folium, putaran adalah mengikut arah jam
                txt_rot = -line_angle_deg

                # Posisi Tengah
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                
                folium.Marker(
                    [mid_lat, mid_lon],
                    icon=folium.DivIcon(
                        icon_size=(250,40),
                        icon_anchor=(125,20),
                        html=f"""
                        <div style="
                            width: 250px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            transform: rotate({txt_rot}deg);
                            transform-origin: center center;">
                            <span style="
                                font-size: 10pt; 
                                color: #00FF00; 
                                font-weight: bold; 
                                white-space: nowrap;
                                text-shadow: 2px 2px 3px black;">
                                {brng_str} | {dist:.3f}m
                            </span>
                        </div>
                        """
                    )
                ).add_to(m)

            # MARKER STESEN
            for _, row in df.iterrows():
                folium.CircleMarker(location=[row['lat'], row['lon']], radius=5, color='red', fill=True, fill_color='red').add_to(m)

            folium_static(m, width=1100, height=650)

            # METRIK
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Bil. Stesen", len(df))
            c3.metric("Sesi Pengguna", "Khalid")

    else:
        st.error("Fail data tidak dijumpai.")
except Exception as e:
    st.error(f"Ralat: {e}")
