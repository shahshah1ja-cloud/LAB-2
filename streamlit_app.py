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

# --- FUNGSI TRANSFORMASI (KERTAU 4390 -> WGS84) ---
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
            
            # CIPTA PETA (Max Zoom 22 supaya imej satelit kekal)
            m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=20, max_zoom=22)

            # GOOGLE HYBRID SATELLITE
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google Satellite',
                name='Google Satellite',
                overlay=False,
                control=True
            ).add_to(m)

            # LUKIS SEMPADAN & TEKS SEJAJAR
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                # Garisan Lot (Kuning)
                locs = [[p1['lat'], p1['lon']], [p2['lat'], p2['lon']]]
                folium.PolyLine(locs, color="yellow", weight=3, opacity=1).add_to(m)
                
                # Kira Bearing & Jarak
                de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = math.sqrt(de**2 + dn**2)
                bearing_rad = math.atan2(de, dn)
                bearing_deg = math.degrees(bearing_rad)
                if bearing_deg < 0: bearing_deg += 360
                
                label_text = f"{int(bearing_deg)}°{int((bearing_deg%1)*60):02d}' | {dist:.3f}m"
                
                # --- FORMULA PUTARAN TEKS SEJAJAR ---
                # Mengubah bearing geomatik kepada sudut putaran CSS
                text_rotation = 90 - bearing_deg 
                
                # Menyelaraskan teks supaya sentiasa boleh dibaca (tidak terbalik)
                if text_rotation > 90: text_rotation -= 180
                elif text_rotation < -90: text_rotation += 180

                # Label di Tengah Garisan
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                
                folium.Marker(
                    [mid_lat, mid_lon],
                    icon=folium.DivIcon(
                        icon_size=(200,40),
                        icon_anchor=(100,20), # Anchor tepat di tengah kotak icon_size
                        html=f"""
                        <div style="
                            width: 200px;
                            height: 40px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            transform: rotate({text_rotation}deg);
                            transform-origin: center center;
                            pointer-events: none;">
                            <span style="
                                font-size: 10pt; 
                                color: #00FF00; 
                                font-weight: bold; 
                                white-space: nowrap;
                                text-shadow: 2px 2px 3px black;">
                                {label_text}
                            </span>
                        </div>
                        """
                    )
                ).add_to(m)

            # MARKER STESEN (MERAH)
            for _, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=5, color='red', fill=True, fill_color='red'
                ).add_to(m)

            folium_static(m, width=1100, height=650)

            # 3. METRIK BAWAH
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Bil. Stesen", len(df))
            c3.metric("Sesi Pengguna", "Khalid")

    else:
        st.error("Fail 'point.csv' tidak dijumpai.")
except Exception as e:
    st.error(f"Ralat: {e}")
