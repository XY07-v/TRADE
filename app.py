import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim

# --- INTERFAZ LIMPIA TIPO IOS ---
st.set_page_config(page_title="Creación de Punto", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F2F2F7; }
    [data-testid="stForm"] {
        background-color: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.05);
        max-width: 450px;
        margin: auto;
        border: none;
    }
    .stButton > button {
        background-color: #007AFF;
        color: white;
        border-radius: 12px;
        width: 100%;
        height: 50px;
        font-weight: 600;
        border: none;
        margin-top: 10px;
    }
    input { 
        background-color: #F2F2F7 !important; 
        border: none !important; 
        border-radius: 10px !important; 
        height: 45px;
    }
    label { font-size: 1rem; color: #1C1C1E; font-weight: 500; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS Y CONFIG ---
dict_ubicaciones = {"Bogotá": "Cundinamarca", "Medellín": "Antioquia", "Cali": "Valle del Cauca", "Barranquilla": "Atlántico"}
dict_desarrolladores = ["Andrés Vanegas", "Admin", "Soporte"]
MESES_ES = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril", "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto", "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}

# --- CAPTURA DE GEOLOCALIZACIÓN REFORZADA ---
# Se solicita la ubicación antes de cargar el formulario
location = get_geolocation()

dir_escrita = ""
coords_val = ""

if location:
    lat = location['coords']['latitude']
    lon = location['coords']['longitude']
    coords_val = f"{lat}, {lon}"
    
    try:
        geolocator = Nominatim(user_agent="power_trade_app_v3")
        loc_obj = geolocator.reverse((lat, lon), timeout=10)
        # Formateo manual para obtener Carrera/Calle # Número
        address_parts = loc_obj.address.split(',')
        dir_escrita = f"{address_parts[0].strip()} # {address_parts[1].strip()}" if len(address_parts) > 1 else address_parts[0]
    except:
        dir_escrita = "Ubicación detectada (Sin nombre de calle)"

# --- OBTENER ESTRUCTURA DE COLUMNAS ---
sample = visitas_col.find_one()
columnas = list(sample.keys()) if sample else ["Id", "Ciudad", "Departamento", "Direccion", "Ubicacion", "Desarrollador", "Estado", "MES", "Rango"]
if '_id' in columnas: columnas.remove('_id')

# --- FORMULARIO PRINCIPAL ---
st.title("Creación de Punto")

if not location:
    st.info("⌛ Esperando señal GPS... Por favor, asegúrate de que el GPS esté activo y otorga permisos si aparece un mensaje.")

with st.form("punto_form"):
    respuestas = {}
    
    for col in columnas:
        if col == "Id":
            ultimo = visitas_col.find_one(sort=[("Id", -1)])
            next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
            respuestas[col] = st.text_input("Id", value=next_id, disabled=True)
            
        elif col == "Direccion":
            # Aquí va la dirección legible tipo "Carrera 13 # 1-3"
            respuestas[col] = st.text_input("Dirección", value=dir_escrita)
            
        elif col == "Ubicacion":
            # Aquí van las coordenadas lat, lon
            respuestas[col] = st.text_input("Ubicación", value=coords_val, disabled=True)
            
        elif col == "Ciudad":
            respuestas[col] = st.selectbox("Ciudad", options=list(dict_ubicaciones.keys()))
            
        elif col == "Departamento":
            respuestas[col] = st.text_input("Departamento", value=dict_ubicaciones.get(respuestas.get("Ciudad", "Bogotá"), ""), disabled=True)
            
        elif col == "Desarrollador":
            respuestas[col] = st.selectbox("Desarrollador", options=dict_desarrolladores)
            
        elif col == "Estado":
            respuestas[col] = st.radio("Estado", ["Habilitado", "Deshabilitado"], horizontal=True)
            
        elif col == "MES":
            mes_txt = MESES_ES.get(datetime.now().strftime("%B"), datetime.now().strftime("%B"))
            respuestas[col] = st.text_input("Mes", value=mes_txt)
            
        elif col == "Rango":
            respuestas[col] = 200
            st.text_input("Rango", value="200", disabled=True)
            
        else:
            respuestas[col] = st.text_input(col)

    submit = st.form_submit_button("Guardar Registro")

    if submit:
        if not coords_val:
            st.error("No se pudo guardar: El GPS aún no ha enviado las coordenadas.")
        else:
            final_data = {k: v for k, v in respuestas.items()}
            final_data["Id"] = next_id
            final_data["Departamento"] = dict_ubicaciones.get(respuestas["Ciudad"], "")
            final_data["Rango"] = 200
            
            visitas_col.insert_one(final_data)
            st.success("¡Punto creado exitosamente!")
            st.balloons()
