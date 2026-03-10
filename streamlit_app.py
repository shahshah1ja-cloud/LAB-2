import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import json
from pyproj import Transformer
import folium
from streamlit_folium import folium_static

# 1. KONFIGURASI HALAMAN & SESI
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_session' not in st.session_state:
    st.session_state['user_session'] = "Khalid"

# --- FUNGSI LOG MASUK ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        selected_user = st.selectbox("Pilih Sesi Pengguna", ["Khalid", "SHAH", "JA'AR"])
        id_input = st.text_input("ID Pengguna", placeholder="Masukkan ID anda")
        pass_input = st.text_input("Kata Laluan", type="password", placeholder="Masukkan kata laluan")
        
        if st.button("Masuk", use_container_width=True):
            if id_input == "01DGU24F1033" and pass_input == "KHALID123":
                st.session_state['logged_in'] = True
                st.session_state['user_session'] = selected_user
                st.rerun()
            else:
                st.error("ID atau Kata Laluan Salah!")

# --- FUNGSI UTAMA APLIKASI ---
def main_app():
    def find_file(variants):
        for v in variants:
            if os.path.exists(v): return v
        return None

    image_file = find_file(["gmbr_puoR.png", "logo.png"])

    with st.sidebar:
        st.markdown(f"**Sesi:** <span style='color: #00FF00;'>{st.session_state['user_session']}</span>", unsafe_allow_html=True)
        if st.button("🚪 Log Keluar"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.divider()
        st.markdown("### 📂 Muat Naik Data")
        uploaded_file = st.file_uploader("Pilih fail CSV points", type=["csv"])
        st.divider()
        st.markdown("### 🌍 Eksport ke QGIS")
        export_placeholder = st.empty()
        st.divider()
        st.markdown("### 👁️ Kawalan Paparan")
        show_sat = st.toggle("Paparkan Imej Satelit", value=True)
        show_stn = st.checkbox("Paparkan No Stesen", value=True)
        show_brng = st.checkbox("Paparkan Bearing/Jarak", value=True)
        show_poly = st.checkbox("Paparkan Poligon & Luas", value=True)
        lot_color = st.color_picker("Warna Kawasan Lot", "#00FFFF")
        st.divider()
        st.markdown("### 🛠️ Tetapan Saiz Teks")
        size_stn = st.slider("Saiz No Stesen", 8, 20, 12)
        size_brng = st.slider("Saiz Bearing/Jarak", 8, 20, 10)
        st.divider()
        epsg_code = st.text_input("Kod EPSG", value="4390")

    col_logo, col_text = st.columns([1, 4])
    with col_logo:
        if image_file: st.image(image_file, width=150)
    with col_text:
        st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)
    st.divider()

    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lat'], df['lon'] = lat, lon

            # --- LOGIK DATA UNTUK QGIS (GEOJSON) ---
            total_perimeter = 0
            lines_info = []
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                d = math.sqrt(de**2 + dn**2)
                total_perimeter += d
                b = math.degrees(math.atan2(de, dn))
                if b < 0: b += 360
                lines_info.append(f"S{int(p1['STN'])}-S{int(p2['STN'])}: {int(b)}°{int((b%1)*60)}' | {d:.3f}m")

            luas_val = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            coords_geojson = [[row['lon'], row['lat']] for _, row in df.iterrows()]
            coords_geojson.append(coords_geojson[0]) 
            
            # Memasukkan maklumat ke dalam GeoJSON Properties
            geojson_data = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "Sesi": st.session_state['user_session'],
                        "Luas_m2": round(luas_val, 3),
                        "Perimeter_m": round(total_perimeter, 3),
                        "Bearing_Jarak": " | ".join(lines_info),
                        "Koordinat_List": df[['STN','N','E']].to_dict('records')
                    },
                    "geometry": {"type": "Polygon", "coordinates": [coords_geojson]}
                }]
            }
            
            geojson_str = json.dumps(geojson_data)
            with export_placeholder:
                st.download_button(
                    label="📥 Muat Turun GeoJSON (QGIS)",
                    data=geojson_str,
                    file_name=f"lot_{st.session_state['user_session']}.geojson",
                    mime="application/json",
                    use_container_width=True
                )

            # --- BINA PETA FOLIUM ---
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=20, max_zoom=25)
            if show_sat:
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite', name='Google Satellite', max_zoom=25, max_native_zoom=20, overlay=False, control=False).add_to(m)

            if show_poly:
                folium.Polygon(locations=[[row['lat'], row['lon']] for _, row in df.iterrows()], color=lot_color, weight=0, fill=True, fill_color=lot_color, fill_opacity=0.4).add_to(m)
                for i in range(len(df)):
                    p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                    popup_html = f"<b>INFO LOT</b><br>Luas: {luas_val:.3f} m²<br>Perimeter: {total_perimeter:.3f} m<br><hr>STN {int(p1['STN'])}<br>N: {p1['N']:.3f}<br>E: {p1['E']:.3f}"
                    folium.CircleMarker(location=[p1['lat'], p1['lon']], radius=5, color='red', fill=True, fill_color='red', popup=folium.Popup(popup_html, max_width=200)).add_to(m)
                    folium.PolyLine([[p1['lat'], p1['lon']], [p2['lat'], p2['lon']]], color="yellow", weight=3).add_to(m)
                    
                    de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                    dist = math.sqrt(de**2 + dn**2)
                    brng_val = math.degrees(math.atan2(de, dn))
                    if brng_val < 0: brng_val += 360
                    
                    if show_brng:
                        mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                        folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(icon_size=(200,40), icon_anchor=(100,20), html=f'<div style="color:#00FF00; font-weight:bold; text-shadow:2px 2px 3px black; font-size:{size_brng}pt;">{int(brng_val)}°{int((brng_val%1)*60)}\' | {dist:.3f}m</div>')).add_to(m)
                    if show_stn:
                        folium.Marker([p1['lat'], p1['lon']], icon=folium.DivIcon(icon_anchor=(-10, 10), html=f'<div style="font-size:{size_stn}pt; color:white; font-weight:bold; text-shadow:1px 1px 2px black;">{int(p1["STN"])}</div>')).add_to(m)

            folium_static(m, width=1100, height=600)
            if show_poly:
                st.success(f"📐 Luas: {luas_val:.3f} m² | 📏 Perimeter: {total_perimeter:.3f} m")

        else:
            st.info(f"👋 Selamat Datang, {st.session_state['user_session']}! Sila muat naik fail CSV points.")
    except Exception as e:
        st.error(f"Ralat: {e}")

if st.session_state['logged_in']:
    main_app()
else:
    login_page()
