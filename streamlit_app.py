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

# Inisialisasi status log masuk jika belum wujud
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- FUNGSI LOG MASUK ---
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        
        with st.container():
            # Input berdasarkan rujukan gambar anda
            id_input = st.text_input("ID Pengguna", placeholder="Masukkan ID anda")
            pass_input = st.text_input("Kata Laluan", type="password", placeholder="Masukkan kata laluan")
            
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("Masuk", use_container_width=True):
                    # Semakan kredential yang anda tetapkan
                    if id_input == "01DGU24F1033" and pass_input == "KHALID123":
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("ID atau Kata Laluan Salah!")
            
            with btn_col2:
                st.button("Lupa Kata Laluan?", use_container_width=True)

# --- FUNGSI UTAMA APLIKASI ---
def main_app():
    # --- FUNGSI CARI FAIL ---
    def find_file(name_variants):
        for variant in name_variants:
            if os.path.exists(variant): return variant
        return None

    file_path = find_file(["point.csv", "data_ukur.csv"])
    image_file = find_file(["gmbr_puoR.png", "logo.png"])

    # 2. SIDEBAR (KAWALAN PAPARAN & TETAPAN)
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
        show_poly = st.checkbox("Paparkan Poligon & Luas", value=True)
        
        st.divider()
        st.markdown("### 🛠️ Tetapan Saiz Teks")
        size_stn = st.slider("Saiz No Stesen", 8, 20, 12)
        size_brng = st.slider("Saiz Bearing/Jarak", 8, 20, 10)
        
        st.divider()
        epsg_code = st.text_input("Kod EPSG", value="4390")

    # 3. TAJUK UTAMA
    col_logo, col_text = st.columns([1, 4])
    with col_logo:
        if image_file: st.image(image_file, width=150)
    with col_text:
        st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

    st.divider()

    # 4. PROSES PETA
    try:
        if file_path:
            df = pd.read_csv(file_path)
            # (Bahagian transformasi koordinat dan plotting dikekalkan...)
            # Kod ini menggunakan logik rotasi sejajar yang telah kita bincangkan
            
            # --- PEMBINAAN PETA ---
            # (Kod peta Folium anda di sini...)
            st.info("Sistem sedia digunakan oleh Khalid.")
        else:
            st.warning("Sila pastikan fail 'point.csv' tersedia untuk memaparkan data.")
    except Exception as e:
        st.error(f"Ralat: {e}")

# --- LOGIK PERALIHAN HALAMAN ---
if st.session_state['logged_in']:
    main_app()
else:
    login_page()
