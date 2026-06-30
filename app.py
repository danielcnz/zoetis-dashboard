import streamlit as st
import gspread
import pandas as pd
import numpy as np
import plotly.express as px
import base64
import os

# Configuración de página
st.set_page_config(page_title="Zoetis Pricing Intel", layout="wide")

# --- FUNCIÓN PARA LOGOS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- CSS DEFINITIVO: TARJETAS GLOW NARANJAS Y POSICIÓN LOGOS ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3); border: 1px solid #FF8C00;
        text-align: center;
    }
    div[data-testid="stMetricValue"] { color: #FF8C00; font-weight: bold; font-size: 20px; }
    div[data-testid="stMetricLabel"] { color: #666; font-size: 11px; text-transform: uppercase; }
    .logo-top { position: absolute; top: 10px; right: 20px; width: 150px; }
    .logo-bottom { position: absolute; bottom: 20px; right: 20px; width: 120px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN MULTI-USUARIO SEGURO ---
if 'autenticado' not in st.session_state: 
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("## 🔐 Acceso Seguro al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        users = st.secrets.get("usuarios", {})
        if u in users and users[u] == p:
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- SIDEBAR CON LOGOS ---
# --- SIDEBAR CON LOGOS (SOLO SE CARGAN SI ESTÁ AUTENTICADO) ---
# if st.session_state['autenticado']:
#    try:
#       zoetis_b64 = get_base64_of_bin_file("zoetis.png")
#        canada_b64 = get_base64_of_bin_file("canada_zoom.png")
#       st.sidebar.markdown(f"""
#            <img src="data:image/png;base64,{zoetis_b64}" class="logo-top">
#            <img src="data:image/png;base64,{canada_b64}" class="logo-bottom">
#        """, unsafe_allow_html=True)
#   except Exception as e:
#        st.sidebar.warning(f"Error cargando logos: {e}")

# --- CARGA Y LIMPIEZA CON API ---
@st.cache_data(ttl=60)
def load_data():
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key("1a44CzuSvqhdF90CwhHZbbnJnPmwi7O8bv8r5PibVkOg")
    worksheet = sh.sheet1
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    price_cols = [f'Precio {i}' for i in range(1, 31)]
    for col in price_cols:
        df[col] = (df[col].astype(str).str.replace('$', '', regex=False).str.replace('.', '', regex=False))
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, price_cols

df, price_cols = load_data()

# --- FILTROS Y DASHBOARD ---
cat_sel = st.sidebar.selectbox("Categoría", ["Todas"] + list(df['Categoría'].unique()))
prod_lista = df[df['Categoría'] == cat_sel]['Product Name'].unique() if cat_sel != "Todas" else df['Product Name'].unique()
prod_sel = st.sidebar.selectbox("Producto", ["Todos"] + list(prod_lista))

# ... (El resto de tu código de lógica de dashboard sigue igual)
