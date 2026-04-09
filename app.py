import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim

# --- CONFIGURACIÓN TIPO IOS ---
st.set_page_config(page_title="Creación de Punto", page_icon="🏢", layout="centered")

MESES_ES = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", 
    "April": "Abril", "May": "Mayo", "June": "Junio", 
    "July": "Julio", "August": "Agosto", "September": "Septiembre", 
    "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

st.markdown("""
    <style>
    .stApp { background-color: #F2F2F7; }
    [data-testid="stForm"] {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.05);
        max-width: 480px;
        margin: auto;
    }
    .stButton > button {
        border-radius: 12px; background-color: #007AFF; color: white; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS MANUALES ---
dict_ubicaciones = {"Bogotá": "Cundinamarca", "Medellín": "Antioquia", "Cali": "Valle del Cauca", "Barranquilla": "Atlántico"}
dict_desarrolladores = ["Andrés Vanegas", "Admin Power", "Soporte"]

# --- LÓGICA DE GEOLOCALIZACIÓN ---
geolocator = Nominatim(user_agent="power_trade_app")
loc = get_geolocation()

direccion_formateada = ""
coords_str = ""

if loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    coords_str = f"{lat}, {lon}"
    try:
        # Traducir coordenadas a dirección real (Carrera, Calle, etc.)
        location_obj = geolocator.reverse((lat, lon))
        direccion_formateada = location_obj.address.split(',')[0] + ", " + location_obj.address.split(',')[1]
    except:
        direccion_formateada = "Dirección no detectada"

# --- OBTENER TODAS LAS COLUMNAS EXISTENTES ---
sample_doc = visitas_col.find_one()
todas_las_columnas = list(sample_doc.keys()) if sample_doc else []
columnas_ignorar = ['_id', 'Id', 'Ciudad', 'Departamento', 'Direccion', 'Ubicacion', 'Desarrollador', 'Estado', 'MES']

# --- FORMULARIO ---
st.title("🏢 Creación de Punto")

with st.form("creacion_punto_form"):
    # 1. ID e Info Básica
    ultimo = visitas_col.find_one(sort=[("Id", -1)])
    next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    st.text_input("🆔 ID Registro", value=next_id, disabled=True)
    
    desarrollador = st.selectbox("👨‍💻 Desarrollador", options=dict_desarrolladores)

    # 2. Ubicación Inteligente
    ciudad = st.selectbox("🏙️ Ciudad", options=list(dict_ubicaciones.keys()))
    depto = st.text_input("🗺️ Departamento", value=dict_ubicaciones[ciudad], disabled=True)
    
    # Dirección automática con formato de texto (Carrera/Calle)
    dir_escrita = st.text_input("🏠 Dirección Cercana (Auto)", value=direccion_formateada)
    coord_input = st.text_input("📍 Coordenadas", value=coords_str, disabled=True)

    # 3. Estado con Botones
    st.write("🔘 **Estado**")
    estado = st.radio("", ["Habilitado", "Deshabilitado"], horizontal=True, label_visibility="collapsed")

    # 4. Mes automático
    mes_es = MESES_ES.get(datetime.now().strftime("%B"), datetime.now().strftime("%B"))
    mes = st.text_input("📅 Mes", value=mes_es)

    # 5. CARGA DINÁMICA DEL RESTO DE LA BD
    st.markdown("---")
    campos_extra = {}
    for col in todas_las_columnas:
        if col not in columnas_ignorar:
            campos_extra[col] = st.text_input(f"📄 {col}")

    # ENVÍO
    if st.form_submit_button("Crear Punto de Venta"):
        nuevo_doc = {
            "Id": next_id,
            "Desarrollador": desarrollador,
            "Ciudad": ciudad,
            "Departamento": dict_ubicaciones[ciudad],
            "Direccion": dir_escrita,
            "Ubicacion": coord_input,
            "Estado": estado,
            "MES": mes,
            "Fecha_Creacion": datetime.now()
        }
        # Unimos los campos extra detectados de la BD
        nuevo_doc.update(campos_extra)
        
        visitas_col.insert_one(nuevo_doc)
        st.success(f"✅ Punto #{next_id} creado con éxito.")
        st.balloons()

st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 0.8rem;'>Módulo: Creación de Punto</p>", unsafe_allow_html=True)
