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

# --- SIDEBAR (SESI: KHALID) ---
with st.sidebar:
    st.markdown(f"**Sesi:** <span style='color: #00FF00;'>Khalid</span>", unsafe_allow_html=True)
    st.divider()
    st.subheader("🎯 Penentukan (Offset)")
    off_n = st.slider("Utara/Selatan (m)", -20.0, 20.0, 0.0)
    off_e = st.slider("Timur/Barat (m)", -20.0, 20.0, 0.0)
    st.text_input("Kod EPSG", "4390", disabled=True)

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
        # Apply Offset
        df['E'] = pd.to_numeric(df['E']) + off_e
        df['N'] = pd.to_numeric(df['N']) + off_n
        df = convert_coords(df)
        
        if not df.empty:
            centroid_lat = df['lat'].mean()
            centroid_lon = df['lon'].mean()
            
            # CIPTA PETA LEAFLET (Max Zoom 22 supaya tidak hilang bila zoom in)
            m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=20, max_zoom=22)

            # GOOGLE HYBRID SATELLITE (Sangat Stabil)
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
                
                # Kira Bearing & Jarak (Geomatik)
                de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = math.sqrt(de**2 + dn**2)
                angle_rad = math.atan2(de, dn)
                angle_deg = math.degrees(angle_rad)
                bearing = angle_deg if angle_deg >= 0 else angle_deg + 360
                
                # Format Bearing
                d = int(bearing)
                m_arc = int((bearing - d) * 60)
                label_text = f"{d}°{m_arc:02d}' | {dist:.3f}m"
                
                # Kira Putaran Teks (Sejajar dengan garisan)
                # Teks dipusing mengikut arah garisan (CSS rotate)
                text_rotation = 90 - angle_deg 
                if text_rotation > 90: text_rotation -= 180
                elif text_rotation < -90: text_rotation += 180

                # Label Tengah Garisan
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                
                folium.Marker(
                    [mid_lat, mid_lon],
                    icon=folium.DivIcon(
                        icon_size=(200,30),
                        icon_anchor=(100,15),
                        html=f"""
                        <div style="
                            font-size: 9pt; 
                            color: #00FF00; 
                            font-weight: bold; 
                            text-align: center; 
                            white-space: nowrap;
                            transform: rotate({text_rotation}deg);
                            text-shadow: 1px 1px 2px black;">
                            {label_text}
                        </div>
                        """
                    )
                ).add_to(m)

            # MARKER STESEN (MERAH)
            for _, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=5, color='red', fill=True, fill_color='red', fill_opacity=1
                ).add_to(m)

            # Paparkan Peta
            folium_static(m, width=1100, height=650)

            # 3. METRIK BAWAH
            st.divider()
            luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            c1, c2, c3 = st.columns(3)
            c1.metric("Bil. Stesen", len(df))
            c2.metric("Luas Tanah", f"{luas:.2f} m²")
            c3.metric("Sesi Pengguna", "Khalid")

    else:
        st.error("Fail 'point.csv' tidak dijumpai.")
except Exception as e:
    st.error(f"Ralat: {e}")
