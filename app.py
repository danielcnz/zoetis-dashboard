import streamlit as st
import gspread
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Zoetis Pricing Intel", layout="wide")

# --- CSS DEFINITIVO: TARJETAS GLOW NARANJAS ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3);
        border: 1px solid #FF8C00;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        color: #FF8C00;
        font-weight: bold;
        font-size: 20px;
    }
    div[data-testid="stMetricLabel"] {
        color: #666;
        font-size: 11px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN PERSISTENTE ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# Esta función verifica el estado y detiene el script si no hay sesión
def check_password():
    if st.session_state['autenticado']:
        return True
    
    st.markdown("## 🔐 Acceso Seguro al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if u == "daniel.perez" and p == "Zoetis2026*":
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    return False

# Ejecutamos la verificación
if not check_password():
    st.stop()

# --- CARGA Y LIMPIEZA CON API ---
@st.cache_data(ttl=60)
def load_data():
    # Conexión vía API de Google
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    
    # IMPORTANTE: Usa el ID de tu hoja para evitar errores de nombre
    sh = gc.open_by_key("1a44CzuSvqhdF90CwhHZbbnJnPmwi7O8bv8r5PibVkOg")
    worksheet = sh.sheet1
    
    # Convertimos a DataFrame
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    df.columns = df.columns.str.strip()
    price_cols = [f'Precio {i}' for i in range(1, 31)]
    
    for col in price_cols:
        # MANTENEMOS TU LÓGICA DE LIMPIEZA ORIGINAL EXACTA
        df[col] = (df[col].astype(str)
                   .str.replace('$', '', regex=False)
                   .str.replace('.', '', regex=False))
        
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, price_cols

df, price_cols = load_data()

# --- FILTROS ---
cat_sel = st.sidebar.selectbox("Categoría", ["Todas"] + list(df['Categoría'].unique()))
prod_lista = df[df['Categoría'] == cat_sel]['Product Name'].unique() if cat_sel != "Todas" else df['Product Name'].unique()
prod_sel = st.sidebar.selectbox("Producto", ["Todos"] + list(prod_lista))

df_f = df.copy()
if cat_sel != "Todas": df_f = df_f[df_f['Categoría'] == cat_sel]
if prod_sel != "Todos": df_f = df_f[df_f['Product Name'] == prod_sel]

st.title(f"📈 Dashboard de Precios: {prod_sel}")

if not df_f.empty:
    # 6 KPIs
    precios = df_f[price_cols].replace(0, np.nan).stack()
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Precio Promedio", f"${precios.mean():,.0f}")
    k2.metric("Mediana Precio", f"${precios.median():,.0f}")
    k3.metric("P. Mínimo", f"${precios.min():,.0f}")
    k4.metric("P. Máximo", f"${precios.max():,.0f}")
    k5.metric("Desv. Est.", f"{precios.std():,.0f}")
    k6.metric("SKU Seleccionados", len(df_f))

    st.markdown("<br>", unsafe_allow_html=True)

    # GRÁFICO
    if prod_sel != "Todos":
        st.subheader("Dispersión de Precios")
        data_plot = pd.melt(df_f[price_cols].replace(0, np.nan), var_name='Obs', value_name='Precio')
        fig = px.box(data_plot, y="Precio", points="all", color_discrete_sequence=['#1F4E78'])
        st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df_f[['Product Name'] + price_cols], use_container_width=True)
else:
    st.warning("Selecciona una categoría o producto.")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()
