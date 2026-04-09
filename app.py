import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval, get_geolocation

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Registro PT", page_icon="📱", layout="centered")

# Traducción de meses a español
MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", 
    "April": "Abril", "May": "Mayo", "June": "Junio", 
    "July": "Julio", "August": "Agosto", "September": "Septiembre", 
    "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

# CSS Estilo iOS con formulario estrecho
st.markdown("""
    <style>
    .stApp { background-color: #F2F2F7; }
    [data-testid="stForm"] {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.05);
        max-width: 450px;
        margin: auto;
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        background-color: #007AFF;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS ---
dict_ubicaciones = {
    "Bogotá": "Cundinamarca",
    "Medellín": "Antioquia",
    "Cali": "Valle del Cauca",
    "Barranquilla": "Atlántico"
}
dict_desarrolladores = ["Andrés Vanegas", "Soporte PT", "Admin"]

# --- LÓGICA DE UBICACIÓN ---
st.write("🛰️ **Sensor GPS Activo**")
loc = get_geolocation()

coord_display = ""
if loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    coord_display = f"{lat}, {lon}"
else:
    st.warning("Por favor, permite el acceso a la ubicación en tu teléfono.")

# --- FORMULARIO ---
st.title("📍 Nuevo Punto")

with st.form("form_ios"):
    # ID Consecutivo
    ultimo_reg = visitas_col.find_one(sort=[("Id", -1)])
    proximo_id = (int(ultimo_reg["Id"]) + 1) if ultimo_reg else 1
    st.text_input("🆔 ID Registro", value=proximo_id, disabled=True)

    # Ciudad y Depto
    ciudad = st.selectbox("🏙️ Ciudad", options=list(dict_ubicaciones.keys()))
    st.text_input("🗺️ Departamento", value=dict_ubicaciones[ciudad], disabled=True)

    # GPS Automático
    # Para la "Dirección Cercana", al ser web, usamos el enlace de mapa o el texto de coordenadas
    direccion_gps = st.text_input("🏠 Dirección Cercana (Auto)", value=f"Cerca de: {coord_display}" if coord_display else "Buscando...", help="Se toma automáticamente del GPS")
    ubicacion_gps = st.text_input("📍 Ubicación (Coordenadas)", value=coord_display, disabled=True)

    # Desarrollador y Estado
    desarrollador = st.selectbox("👨‍💻 Desarrollador", options=dict_desarrolladores)
    
    st.write("🔘 **Estado**")
    estado = st.radio("", ["Habilitado", "Deshabilitado"], horizontal=True, label_visibility="collapsed")

    # Mes en Español
    mes_en_ingles = datetime.now().strftime("%B")
    mes_espanol = MESES_ES.get(mes_en_ingles, mes_en_ingles)
    mes = st.text_input("📅 Mes", value=mes_espanol)

    submitted = st.form_submit_button("Guardar Registro")

    if submitted:
        if not coord_display:
            st.error("No se pudo obtener la ubicación. Asegúrate de tener el GPS encendido.")
        else:
            nuevo_punto = {
                "Id": proximo_id,
                "Desarrollador": desarrollador,
                "Ciudad": ciudad,
                "Departamento": dict_ubicaciones[ciudad],
                "Direccion": direccion_gps,
                "Ubicacion": ubicacion_gps,
                "Estado": estado,
                "MES": mes,
                "Fecha": datetime.now()
            }
            visitas_col.insert_one(nuevo_punto)
            st.success("✅ ¡Registrado exitosamente!")
            st.balloons()

st.markdown("<p style='text-align: center; color: #8E8E93;'>Power Trade Management</p>", unsafe_allow_html=True)
