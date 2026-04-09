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
    label { font-weight: 600 !important; color: #1C1C1E !important; }
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

# --- LÓGICA DE GEOLOCALIZACIÓN ---
geolocator = Nominatim(user_agent="power_trade_app")
loc = get_geolocation()

dir_auto = ""
coords_auto = ""

if loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    coords_auto = f"{lat}, {lon}"
    try:
        location_obj = geolocator.reverse((lat, lon))
        # Extrae la dirección legible (Carrera, Calle, etc.)
        dir_auto = location_obj.address.split(',')[0] + ", " + location_obj.address.split(',')[1]
    except:
        dir_auto = "Ubicación detectada (sin dirección)"

# --- OBTENER ORDEN DE COLUMNAS DE LA BD ---
sample_doc = visitas_col.find_one()
columnas_bd = list(sample_doc.keys()) if sample_doc else []
if '_id' in columnas_bd: columnas_bd.remove('_id')

# --- FORMULARIO ---
st.title("🏢 Creación de Punto")

with st.form("creacion_punto_form"):
    respuestas = {}

    # Generamos los campos respetando el orden de la base de datos
    for col in columnas_bd:
        # Lógica especial para campos automatizados
        if col == "Id":
            ultimo = visitas_col.find_one(sort=[("Id", -1)])
            next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
            respuestas[col] = st.text_input(f"🆔 {col}", value=next_id, disabled=True)
            
        elif col == "Direccion":
            respuestas[col] = st.text_input(f"🏠 {col}", value=dir_auto)
            
        elif col == "Ubicacion":
            respuestas[col] = st.text_input(f"📍 {col}", value=coords_auto, disabled=True)
            
        elif col == "Ciudad":
            respuestas[col] = st.selectbox(f"🏙️ {col}", options=list(dict_ubicaciones.keys()))
            
        elif col == "Departamento":
            # Se auto-alimenta de la ciudad seleccionada arriba (en el envío se procesa)
            st.text_input(f"🗺️ {col}", value=dict_ubicaciones.get(respuestas.get("Ciudad", "Bogotá"), ""), disabled=True)
            
        elif col == "Desarrollador":
            respuestas[col] = st.selectbox(f"👨‍💻 {col}", options=dict_desarrolladores)
            
        elif col == "Estado":
            st.write(f"🔘 **{col}**")
            respuestas[col] = st.radio("", ["Habilitado", "Deshabilitado"], horizontal=True, label_visibility="collapsed")
            
        elif col == "MES":
            mes_actual = MESES_ES.get(datetime.now().strftime("%B"), datetime.now().strftime("%B"))
            respuestas[col] = st.text_input(f"📅 {col}", value=mes_actual)
            
        elif col == "Rango":
            respuestas[col] = st.text_input(f"📏 {col}", value="200", disabled=True)
            
        else:
            # Campos que no tienen lógica especial se muestran como texto normal
            respuestas[col] = st.text_input(f"📄 {col}")

    # ENVÍO DE DATOS
    if st.form_submit_button("Confirmar y Guardar"):
        # Aseguramos que el ID sea numérico
        ultimo = visitas_col.find_one(sort=[("Id", -1)])
        final_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
        
        # Construir el documento final
        nuevo_doc = {k: v for k, v in respuestas.items()}
        nuevo_doc["Id"] = final_id
        nuevo_doc["Departamento"] = dict_ubicaciones.get(respuestas["Ciudad"], "")
        nuevo_doc["Rango"] = 200
        nuevo_doc["Fecha_Sistema"] = datetime.now()

        try:
            visitas_col.insert_one(nuevo_doc)
            st.success(f"✅ Registro #{final_id} creado exitosamente.")
            st.balloons()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 0.8rem;'>Power Trade | Creación de Punto</p>", unsafe_allow_html=True)
