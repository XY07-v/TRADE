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
    label { font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS ---
dict_ubicaciones = {"Bogotá": "Cundinamarca", "Medellín": "Antioquia", "Cali": "Valle del Cauca", "Barranquilla": "Atlántico"}
dict_desarrolladores = ["Andrés Vanegas", "Admin Power", "Soporte"]

# --- CAPTURA DE GPS (FUERA DEL FORMULARIO PARA ACTIVAR EL SENSOR) ---
st.write("🛰️ **Localizando punto...**")
geolocator = Nominatim(user_agent="power_trade_app")
loc = get_geolocation()

dir_auto = ""
coords_auto = ""

if loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    coords_auto = f"{lat}, {lon}"
    try:
        location_obj = geolocator.reverse((lat, lon))
        # Esto extrae "Carrera X # Y - Z"
        dir_auto = location_obj.address.split(',')[0] + ", " + location_obj.address.split(',')[1]
    except:
        dir_auto = "Dirección no disponible (GPS activo)"

# --- OBTENER ORDEN DE COLUMNAS ---
sample_doc = visitas_col.find_one()
columnas_bd = list(sample_doc.keys()) if sample_doc else ["Id", "Ciudad", "Departamento", "Direccion", "Ubicacion", "Desarrollador", "Estado", "MES", "Rango"]
if '_id' in columnas_bd: columnas_bd.remove('_id')

# --- FORMULARIO ---
st.title("🏢 Creación de Punto")

with st.form("creacion_punto_form"):
    respuestas = {}

    for col in columnas_bd:
        # 1. LÓGICA DE ID
        if col == "Id":
            ultimo = visitas_col.find_one(sort=[("Id", -1)])
            next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
            respuestas[col] = st.text_input(f"🆔 {col}", value=next_id, disabled=True)
            
        # 2. LÓGICA DE DIRECCIÓN (AUTOMÁTICA)
        elif col == "Direccion":
            respuestas[col] = st.text_input(f"🏠 {col}", value=dir_auto, help="Generado automáticamente por GPS")
            
        # 3. LÓGICA DE UBICACIÓN (COORDENADAS)
        elif col == "Ubicacion":
            respuestas[col] = st.text_input(f"📍 {col}", value=coords_auto, disabled=True)
            
        # 4. LÓGICA DE CIUDAD / DEPTO
        elif col == "Ciudad":
            respuestas[col] = st.selectbox(f"🏙️ {col}", options=list(dict_ubicaciones.keys()))
            
        elif col == "Departamento":
            # Nota: Se llenará en el envío basado en la Ciudad seleccionada
            st.text_input(f"🗺️ {col}", value=dict_ubicaciones.get(respuestas.get("Ciudad", "Bogotá"), ""), disabled=True)
            
        # 5. DESARROLLADOR Y ESTADO
        elif col == "Desarrollador":
            respuestas[col] = st.selectbox(f"👨‍💻 {col}", options=dict_desarrolladores)
            
        elif col == "Estado":
            st.write(f"🔘 **{col}**")
            respuestas[col] = st.radio("", ["Habilitado", "Deshabilitado"], horizontal=True, label_visibility="collapsed")
            
        # 6. RANGO FIJO
        elif col == "Rango":
            respuestas[col] = st.text_input(f"📏 {col}", value="200", disabled=True)
            
        # 7. MES AUTOMÁTICO
        elif col == "MES":
            mes_actual = MESES_ES.get(datetime.now().strftime("%B"), datetime.now().strftime("%B"))
            respuestas[col] = st.text_input(f"📅 {col}", value=mes_actual)
            
        # 8. RESTO DE COLUMNAS DE LA BD
        else:
            respuestas[col] = st.text_input(f"📄 {col}")

    # BOTÓN DE GUARDAR
    if st.form_submit_button("Confirmar Registro"):
        if not coords_auto:
            st.warning("⚠️ Esperando señal GPS. Por favor asegúrate de dar permisos de ubicación.")
        else:
            # Construcción del documento final respetando el orden
            nuevo_doc = {k: v for k, v in respuestas.items()}
            # Forzar valores automáticos finales
            nuevo_doc["Departamento"] = dict_ubicaciones.get(respuestas["Ciudad"], "")
            nuevo_doc["Rango"] = 200
            nuevo_doc["Fecha_Creado"] = datetime.now()

            try:
                visitas_col.insert_one(nuevo_doc)
                st.success(f"✅ ¡Registro #{respuestas['Id']} guardado con éxito!")
                st.balloons()
            except Exception as e:
                st.error(f"Error al conectar con la base de datos: {e}")

st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 0.8rem;'>Power Trade | Creación de Punto</p>", unsafe_allow_html=True)
