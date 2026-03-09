import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO - Unit Geomatik", layout="wide")

# --- FUNGSI CARI FAIL (MENGATASI ISU NAMA FAIL DI GITHUB) ---
def find_file(name_variants):
    """Mencari fail berdasarkan beberapa variasi nama."""
    for variant in name_variants:
        if os.path.exists(variant):
            return variant
    return None

# Variasi nama fail yang mungkin anda upload di GitHub
file_ukur = find_file(["data ukur.csv", "data_ukur.csv", "DATA UKUR.csv", "Data_Ukur.csv"])
file_point = find_file(["point.csv", "POINT.csv", "Point.csv", "points.csv"])
image_file = find_file(["gmbr_puoR.png", "gmbr puor.png", "logo.png"])

# --- BAHAGIAN TAJUK ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if image_file:
        st.image(image_file, width=200)
    else:
        st.info("Logo PUO tidak dijumpai.")

with col_text:
    st.markdown("<h1 style='margin-bottom: 0;'>POLITEKNIK UNGKU OMAR</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0; color: #00FF00;'>Jabatan Kejuruteraan Awam - Unit Geomatik</h3>", unsafe_allow_html=True)

st.divider()

# 2. FUNGSI PENGIRAAN GEOMETRI
def calculate_details(p1, p2, centroid_e, centroid_n):
    de = p2['E'] - p1['E']
    dn = p2['N'] - p1['N']
    dist = math.sqrt(de**2 + dn**2)
    
    angle_rad = math.atan2(de, dn)
    angle_deg = math.degrees(angle_rad)
    bearing_val = angle_deg if angle_deg >= 0 else angle_deg + 360
    brng_str = f"{int(bearing_val)}°{int((bearing_val%1)*60)}'{int(((bearing_val*60)%1)*60)}\""
    
    mid_e, mid_n = (p1['E'] + p2['E']) / 2, (p1['N'] + p2['N']) / 2
    
    line_angle_rad = math.atan2(dn, de)
    line_angle_deg = math.degrees(line_angle_rad)
    if line_angle_deg > 90: line_angle_deg -= 180
    elif line_angle_deg < -90: line_angle_deg += 180
    txt_rot = -line_angle_deg
    
    norm_e, norm_n = -dn, de
    vec_to_mid_e, vec_to_mid_n = mid_e - centroid_e, mid_n - centroid_n
    if (norm_e * vec_to_mid_e + norm_n * vec_to_mid_n) < 0:
        norm_e, norm_n = -norm_e, -norm_n
        
    length = math.sqrt(norm_e**2 + norm_n**2)
    offset_dist = 0.8  
    offset_e, offset_n = (norm_e / length) * offset_dist, (norm_n / length) * offset_dist
    
    return dist, brng_str, mid_e + offset_e, mid_n + offset_n, txt_rot

def get_area(df):
    x, y = df['E'].values, df['N'].values
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

# 3. PROSES DATA & PLOTTING
try:
    if file_ukur:
        df = pd.read_csv(file_ukur)
        
        centroid_e, centroid_n = df['E'].mean(), df['N'].mean()
        luas = get_area(df)

        fig = go.Figure()

        for i in range(len(df)):
            p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
            dist, brng, txt_e, txt_n, txt_rot = calculate_details(p1, p2, centroid_e, centroid_n)
            
            # Lukis Garisan
            fig.add_trace(go.Scatter(
                x=[p1['E'], p2['E']], y=[p1['N'], p2['N']],
                mode='lines', line=dict(color='#00FF00', width=2),
                hoverinfo='none', showlegend=False
            ))

            # Label Bearing & Jarak
            fig.add_annotation(
                x=txt_e, y=txt_n, text=f"<b>{brng}</b><br>{dist:.3f}m",
                showarrow=False, font=dict(size=10, color="#FFFF00"),
                textangle=txt_rot, align="center"
            )

        # Plot Titik Stesen
        fig.add_trace(go.Scatter(
            x=df['E'], y=df['N'], mode='markers+text',
            marker=dict(color='white', size=8, line=dict(color='red', width=1)),
            text=df['STN'], textposition="top center",
            textfont=dict(color="white", size=9), showlegend=False
        ))

        # Label Luas
        fig.add_annotation(
            x=centroid_e, y=centroid_n, text=f"<b>LUAS<br>{luas:.3f} m²</b>",
            showarrow=False, font=dict(size=18, color="white")
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis=dict(title="EASTING (m)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(title="NORTHING (m)", showgrid=True, gridcolor='rgba(255,255,255,0.1)', scaleanchor="x", scaleratio=1),
            paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", height=700
        )

        st.plotly_chart(fig, use_container_width=True)

        # Metrik Bawah
        st.divider()
        c1, c2, c3 = st.columns(3)
        perimeter = sum([math.sqrt((df.iloc[(i+1)%len(df)]['E']-df.iloc[i]['E'])**2 + (df.iloc[(i+1)%len(df)]['N']-df.iloc[i]['N'])**2) for i in range(len(df))])
        
        c1.metric("Bil. Stesen", len(df))
        c2.metric("Perimeter", f"{perimeter:.3f} m")
        c3.metric("Luas Tanah", f"{luas:.2f} m²")

    else:
        st.error("Ralat: Fail 'data ukur.csv' tidak dijumpai dalam repository GitHub anda.")
        st.info("Pastikan nama fail di GitHub adalah 'data ukur.csv' atau 'data_ukur.csv'.")

    # --- JADUAL POINT ---
    st.subheader("Data Koordinat (Point)")
    if file_point:
        df_point = pd.read_csv(file_point)
        st.dataframe(df_point, use_container_width=True)
    else:
        st.warning("Fail 'point.csv' tidak dijumpai.")

except Exception as e:
    st.error(f"Berlaku ralat teknikal: {e}")
    
