import streamlit as st
import pandas as pd
import numpy as np
import math
import os
from pyproj import Transformer
import folium
from streamlit_folium import folium_static

# 1. KONFIGURASI HALAMAN & SESI
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- FUNGSI LOG MASUK ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        id_input = st.text_input("ID Pengguna", placeholder="Masukkan ID anda")
        pass_input = st.text_input("Kata Laluan", type="password", placeholder="Masukkan kata laluan")
        
        if st.button("Masuk", use_container_width=True):
            if id_input == "01DGU24F1033" and pass_input == "KHALID123":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan Salah!")

# --- FUNGSI UTAMA APLIKASI ---
def main_app():
    def find_file(variants):
        for v in variants:
            if os.path.exists(v): return v
        return None

    file_path = find_file(["point.csv", "data_ukur.csv"])
    image_file = find_file(["gmbr_puoR.png", "logo.png"])

    # SIDEBAR (TETAPAN)
    with st.sidebar:
        st.markdown(f"**Sesi:** <span style='color: #00FF00;'>Khalid</span>", unsafe_allow_html=True)
        if st.button("🚪 Log Keluar"):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.divider()
        st.markdown("### 👁️ Kawalan Paparan")
        show_sat = st.toggle("Paparkan Imej Satelit", value=True)
        show_stn = st.checkbox("Paparkan No Stesen", value=True)
        show_brng = st.checkbox("Paparkan Bearing/Jarak", value=True)
        show_poly = st.checkbox("Paparkan Poligon & Luas", value=True) # Suis Utama
        
        st.divider()
        st.markdown("### 🛠️ Tetapan Saiz Teks")
        size_stn = st.slider("Saiz No Stesen", 8, 20, 12)
        size_brng = st.slider("Saiz Bearing/Jarak", 8, 20, 10)
        
        st.divider()
        st.text_input("Kod EPSG", value="4390")

    # TAJUK UTAMA
    col_logo, col_text = st.columns([1, 4])
    with col_logo:
        if image_file: st.image(image_file, width=150)
    with col_text:
        st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

    st.divider()

    # PAPARAN PETA
    try:
        if file_path:
            df = pd.read_csv(file_path)
            
            # Transformasi Koordinat
            transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df['lat'], df['lon'] = lat, lon

            # Peta Folium dengan Kawalan Zoom Pintar
            m = folium.Map(
                location=[df['lat'].mean(), df['lon'].mean()], 
                zoom_start=20, 
                max_zoom=25,
                control_scale=True
            )

            if show_sat:
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                    attr='Google Satellite',
                    name='Google Satellite',
                    max_zoom=25,
                    max_native_zoom=20, # Membaiki isu zoom hilang
                    overlay=False,
                    control=False
                ).add_to(m)

            total_perimeter = 0

            # Hanya lukis komponen lot jika show_poly diaktifkan
            if show_poly:
                for i in range(len(df)):
                    p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                    
                    # Batu Sempadan (Bucu Merah)
                    folium.CircleMarker(
                        location=[p1['lat'], p1['lon']], radius=4,
                        color='red', fill=True, fill_color='red', fill_opacity=1
                    ).add_to(m)
                    
                    # Garisan Sempadan Kuning
                    folium.PolyLine([[p1['lat'], p1['lon']], [p2['lat'], p2['lon']]], color="yellow", weight=3).add_to(m)
                    
                    # Logik Rotasi Sejajar & Jarak
                    de, dn = p2['E'] - p1['E'], p2['N'] - p1['N']
                    dist = math.sqrt(de**2 + dn**2)
                    total_perimeter += dist
                    
                    line_angle = math.degrees(math.atan2(dn, de))
                    if line_angle > 90: line_angle -= 180
                    elif line_angle < -90: line_angle += 180
                    txt_rot = -line_angle

                    # Papar Bearing/Jarak Sejajar jika ON
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

                    # Papar No Stesen
                    if show_stn:
                        try: stn_label = int(float(p1['STN']))
                        except: stn_label = p1['STN']
                            
                        folium.Marker(
                            [p1['lat'], p1['lon']], 
                            icon=folium.DivIcon(
                                icon_anchor=(-10, 10),
                                html=f'<div style="font-size:{size_stn}pt; color:white; font-weight:bold; text-shadow:1px 1px 2px black;">{stn_label}</div>'
                            )
                        ).add_to(m)

            folium_static(m, width=1100, height=600)
            
            # PAPARAN METRIK BAWAH PETA
            # Kotak ini hanya muncul jika 'Paparkan Poligon & Luas' diaktifkan
            if show_poly:
                luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
                
                # Box Luas (Hijau)
                st.markdown(f"""
                <div style="background-color: #1e3d2f; padding: 15px; border-radius: 10px; border-left: 5px solid #00FF00; margin-bottom: 10px;">
                    <span style="color: #00FF00; font-size: 20px; font-weight: bold;">📐 Luas: {luas:.3f} m²</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Box Perimeter (Biru)
                st.markdown(f"""
                <div style="background-color: #1b2e3e; padding: 15px; border-radius: 10px; border-left: 5px solid #3498db;">
                    <span style="color: #3498db; font-size: 20px; font-weight: bold;">📏 Perimeter: {total_perimeter:.3f} m</span>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("Fail data tidak dijumpai.")
    except Exception as e:
        st.error(f"Ralat: {e}")

# LOGIK HALAMAN
if st.session_state['logged_in']:
    main_app()
else:
    login_page()
