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

file_path = find_file(["point.csv", "data_ukur.csv"])
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
        return df

# 2. SIDEBAR (KAWALAN PAPARAN & TETAPAN)
with st.sidebar:
    st.markdown("### 👁️ Kawalan Paparan")
    show_sat = st.toggle("Paparkan Imej Satelit", value=True)
    show_stn = st.checkbox("Paparkan No Stesen", value=True)
    show_brng = st.checkbox("Paparkan Bearing/Jarak", value=True)
    show_poly = st.checkbox("Paparkan Poligon & Luas", value=True)
    
    st.divider()
    st.markdown("### 🛠️ Tetapan Saiz Teks")
    size_stn = st.slider("Saiz No Stesen", 8, 20, 12)
    size_brng = st.slider("Saiz Bearing/Jarak", 8, 20, 10)
    text_gap = st.slider("Keluasan Gap Teks", 10, 100, 40)
    
    st.divider()
    epsg_code = st.text_input("Kod EPSG", value="4390")
    st.info(f"Sesi: Khalid")

# 3. TAJUK UTAMA
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if image_file: st.image(image_file, width=150)
with col_text:
    st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

st.divider()

# 4. PROSES DATA & PETA
try:
    if file_path:
        df = pd.read_csv(file_path)
        df = convert_coords(df)
        
        if not df.empty:
            centroid_lat = df['lat'].mean()
            centroid_lon = df['lon'].mean()
            
            m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=20, max_zoom=22)

            # Logik Paparan Satelit
            if show_sat:
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                    attr='Google Satellite', name='Google Satellite', overlay=False
                ).add_to(m)

            # Logik Poligon
            if show_poly:
                points = [[row['lat'], row['lon']] for _, row in df.iterrows()]
                folium.Polygon(points, color="yellow", weight=2, fill=True, fill_opacity=0.2).add_to(m)

            # LUKIS GARISAN & TEKS SEJAJAR (LOGIK PARALLEL ANDA)
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                # Garisan Kuning
                locs = [[p1['lat'], p1['lon']], [p2['lat'], p2['lon']]]
                folium.PolyLine(locs, color="yellow", weight=3).add_to(m)
                
                # Kira Bearing & Jarak
                de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = math.sqrt(de**2 + dn**2)
                
                # Logik Rotasi Sejajar (Berdasarkan rujukan coding anda)
                line_angle_rad = math.atan2(dn, de)
                line_angle_deg = math.degrees(line_angle_rad)
                if line_angle_deg > 90: line_angle_deg -= 180
                elif line_angle_deg < -90: line_angle_deg += 180
                txt_rot = -line_angle_deg

                # Paparkan Bearing/Jarak
                if show_brng:
                    mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                    brng_val = math.degrees(math.atan2(de, dn))
                    if brng_val < 0: brng_val += 360
                    
                    folium.Marker(
                        [mid_lat, mid_lon],
                        icon=folium.DivIcon(
                            icon_size=(200,40), icon_anchor=(100,20),
                            html=f"""<div style="transform: rotate({txt_rot}deg); text-align:center;">
                                     <span style="font-size:{size_brng}pt; color:#00FF00; font-weight:bold; text-shadow:2px 2px 3px black;">
                                     {int(brng_val)}°{int((brng_val%1)*60)}' | {dist:.3f}m</span></div>"""
                        )
                    ).add_to(m)

                # Paparkan No Stesen
                if show_stn:
                    folium.Marker(
                        [p1['lat'], p1['lon']],
                        icon=folium.DivIcon(
                            icon_anchor=(0,0),
                            html=f'<div style="font-size:{size_stn}pt; color:white; font-weight:bold;">{p1["STN"]}</div>'
                        )
                    ).add_to(m)

            folium_static(m, width=1100, height=650)

            # METRIK BAWAH
            st.divider()
            luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            c1, c2 = st.columns(2)
            c1.info(f"📐 Luas: {luas:.3f} m²")
            c2.info(f"📏 Perimeter: {dist * len(df):.3f} m")

    else:
        st.error("Fail data tidak dijumpai.")
except Exception as e:
    st.error(f"Ralat: {e}")
