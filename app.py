import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim

# --- ESTILO LIMPIO TIPO IOS ---
st.set_page_config(page_title="Creación de Punto", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F2F2F7; }
    [data-testid="stForm"] {
        background-color: white;
        padding: 2.5rem;
        border-radius: 15px;
        border: none;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.05);
        max-width: 420px;
        margin: auto;
    }
    .stButton > button {
        background-color: #007AFF;
        color: white;
        border-radius: 10px;
        border: none;
        width: 100%;
        height: 45px;
        font-weight: 600;
    }
    input { border-radius: 8px !important; }
    label { font-size: 0.9rem; color: #8E8E93; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS ---
dict_ubicaciones = {"Bogotá": "Cundinamarca", "Medellín": "Antioquia", "Cali": "Valle del Cauca", "Barranquilla": "Atlántico"}
dict_desarrolladores = ["Andrés Vanegas", "Admin", "Soporte"]
MESES_ES = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril", "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto", "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}

# --- LÓGICA GPS ---
geolocator = Nominatim(user_agent="power_trade_app")
loc = get_geolocation()
dir_auto = ""
coords_auto = ""

if loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    coords_auto = f"{lat}, {lon}"
    try:
        location_obj = geolocator.reverse((lat, lon))
        raw_address = location_obj.raw.get('address', {})
        # Construcción limpia de la dirección (Calle/Carrera + Número)
        road = raw_address.get('road', 'Dirección no detectada')
        house_number = raw_address.get('house_number', '')
        dir_auto = f"{road} # {house_number}" if house_number else road
    except:
        dir_auto = "Ubicación detectada"

# --- OBTENER ESTRUCTURA DE LA BD ---
sample_doc = visitas_col.find_one()
columnas_bd = list(sample_doc.keys()) if sample_doc else ["Id", "Ciudad", "Departamento", "Direccion", "Ubicacion", "Desarrollador", "Estado", "MES", "Rango"]
if '_id' in columnas_bd: columnas_bd.remove('_id')

# --- FORMULARIO ---
st.title("Creación de Punto")

with st.form("main_form"):
    respuestas = {}

    for col in columnas_bd:
        if col == "Id":
            ultimo = visitas_col.find_one(sort=[("Id", -1)])
            next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
            respuestas[col] = st.text_input("ID", value=next_id, disabled=True)
            
        elif col == "Direccion":
            respuestas[col] = st.text_input("Dirección", value=dir_auto)
            
        elif col == "Ubicacion":
            respuestas[col] = st.text_input("Ubicación (Coordenadas)", value=coords_auto, disabled=True)
            
        elif col == "Ciudad":
            respuestas[col] = st.selectbox("Ciudad", options=list(dict_ubicaciones.keys()))
            
        elif col == "Departamento":
            respuestas[col] = st.text_input("Departamento", value=dict_ubicaciones.get(respuestas.get("Ciudad", "Bogotá"), ""), disabled=True)
            
        elif col == "Desarrollador":
            respuestas[col] = st.selectbox("Desarrollador", options=dict_desarrolladores)
            
        elif col == "Estado":
            respuestas[col] = st.radio("Estado", ["Habilitado", "Deshabilitado"], horizontal=True)
            
        elif col == "MES":
            mes_actual = MESES_ES.get(datetime.now().strftime("%B"), datetime.now().strftime("%B"))
            respuestas[col] = st.text_input("Mes", value=mes_actual)
            
        elif col == "Rango":
            respuestas[col] = 200
            st.text_input("Rango", value="200", disabled=True)
            
        else:
            respuestas[col] = st.text_input(col)

    if st.form_submit_button("Guardar"):
        if not coords_auto:
            st.error("Esperando señal de GPS...")
        else:
            # Asegurar datos finales antes de insertar
            doc_final = {k: v for k, v in respuestas.items()}
            doc_final["Id"] = next_id
            doc_final["Departamento"] = dict_ubicaciones.get(respuestas["Ciudad"], "")
            doc_final["Rango"] = 200
            
            visitas_col.insert_one(doc_final)
            st.success("Registro guardado")
            st.balloons()
