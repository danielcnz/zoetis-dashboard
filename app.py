import streamlit as st
import gspread
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración inicial
st.set_page_config(page_title="Zoetis Pricing Intel", layout="wide")

# 2. LOGIN (BLOQUE ÚNICO Y SUPERIOR)
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("## 🔐 Acceso Seguro al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "daniel.perez" and p == "Zoetis2026*":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop() # Detiene el script aquí hasta que se logueen

# --- DASHBOARD (Solo llega aquí si está autenticado) ---

@st.cache_data(ttl=60)
def load_data():
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("DB Zoetis Maestra Jun 2026") # <-- RECUERDA PONER EL NOMBRE AQUÍ
    worksheet = sh.sheet1 
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    df.columns = df.columns.str.strip()
    price_cols = [f'Precio {i}' for i in range(1, 31)]
    
    for col in price_cols:
        # LÓGICA DE LIMPIEZA AGRESIVA PARA TU FORMATO
        # Convertimos a string, quitamos el signo de moneda y quitamos LAS COMAS
        # Si el número original es "$1,250", esto lo convierte a "1250"
        df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        # Convertimos a numérico, forzamos a NaN si no es número y llenamos con 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    return df, price_cols

df, price_cols = load_data()

# --- INTERFAZ ---
cat_sel = st.sidebar.selectbox("Categoría", ["Todas"] + list(df['Categoría'].unique()))
prod_lista = df[df['Categoría'] == cat_sel]['Product Name'].unique() if cat_sel != "Todas" else df['Product Name'].unique()
prod_sel = st.sidebar.selectbox("Producto", ["Todos"] + list(prod_lista))

df_f = df.copy()
if cat_sel != "Todas": df_f = df_f[df_f['Categoría'] == cat_sel]
if prod_sel != "Todos": df_f = df_f[df_f['Product Name'] == prod_sel]

st.title(f"📈 Dashboard de Precios: {prod_sel}")

# Mostrar datos
if not df_f.empty:
    precios = df_f[price_cols].replace(0, np.nan).stack()
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Precio Promedio", f"${precios.mean():,.0f}")
    k2.metric("Mediana", f"${precios.median():,.0f}")
    k3.metric("Mínimo", f"${precios.min():,.0f}")
    k4.metric("Máximo", f"${precios.max():,.0f}")
    k5.metric("Desv. Est.", f"{precios.std():,.0f}")
    k6.metric("SKUs", len(df_f))

    st.dataframe(df_f[['Product Name'] + price_cols], use_container_width=True)
