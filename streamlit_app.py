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

# --- FUNGSI TRANSFORMASI (KERTAU 4390 KE WGS84) ---
def convert_coords(df):
    try:
        # Transformasi Johor Grid (4390) ke Lat/Lon (4326)
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

# --- TAJUK ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if image_file: st.image(image_file, width=180)
with col_text:
    st.markdown("<h1 style='color: white; margin-bottom:0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00FF00; margin-top:0;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

st.divider()

# 2. PROSES DATA & PLOTTING (MENGGUNAKAN FOLIUM/LEAFLET)
try:
    if file_path:
        df = pd.read_csv(file_path)
        df = convert_coords(df)
        
        if not df.empty:
            centroid_lat = df['lat'].mean()
            centroid_lon = df['lon'].mean()
            
            # --- CIPTA PETA LEAFLET (FOLIUM) ---
            # Ini akan memastikan paparan sebijik macam screenshot anda (ada butang zoom)
            m = folium.Map(location=[centroid_lat, centroid_lon], zoom_start=19, control_scale=True)

            # TAMBAH GOOGLE SATELLITE LAYER (BACKEND)
            google_satellite = folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Satellite',
                overlay=False,
                control=True
            ).add_to(m)

            # LUKIS POLYGON (GARISAN KUNING/HIJAU)
            points = [[row['lat'], row['lon']] for index, row in df.iterrows()]
            points.append([df.iloc[0]['lat'], df.iloc[0]['lon']]) # Tutup loop
            
            folium.PolyLine(points, color="yellow", weight=4, opacity=1).add_to(m)
            
            # TAMBAH MARKER MERAH PADA SETIAP STESEN
            for index, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=5,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=1,
                    popup=f"Stesen: {row['STN']}"
                ).add_to(m)

            # PAPARKAN PETA DALAM STREAMLIT
            st.subheader("Paparan Satelit (Leaflet Enjin)")
            folium_static(m, width=1100, height=600)

            # 3. METRIK & JADUAL (KEKALKAN YANG BETUL)
            st.divider()
            c1, c2, c3 = st.columns(3)
            luas = 0.5 * np.abs(np.dot(df['E'], np.roll(df['N'], 1)) - np.dot(df['N'], np.roll(df['E'], 1)))
            perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
            
            c1.metric("Bil. Stesen", len(df))
            c2.metric("Perimeter", f"{perimeter:.3f} m")
            c3.metric("Luas Tanah", f"{luas:.2f} m²")

            st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
        else:
            st.error("Data tidak sah.")
    else:
        st.error("Fail data tidak dijumpai.")

except Exception as e:
    st.error(f"Ralat: {e}")
