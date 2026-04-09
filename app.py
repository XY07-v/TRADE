import streamlit as st
import os
from pymongo import MongoClient
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA (ESTILO IOS) ---
st.set_page_config(page_title="Registro PT", page_icon="📱", layout="centered")

# CSS Personalizado para estética profesional y estrecha
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #F2F2F7;
    }
    /* Contenedor del formulario */
    [data-testid="stForm"] {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        border: none;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.05);
        max-width: 500px;
        margin: auto;
    }
    /* Botones de radio tipo segmentado */
    div.row-widget.stRadio > div {
        background-color: #E9E9EB;
        padding: 4px;
        border-radius: 10px;
        display: flex;
        justify-content: space-around;
    }
    /* Estilo del botón principal */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        background-color: #007AFF;
        color: white;
        border: none;
        font-weight: 500;
        padding: 0.6rem;
    }
    /* Inputs redondeados */
    input {
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# --- DICCIONARIOS MANUALES (Editable) ---
# Aquí puedes agregar más ciudades y sus departamentos
dict_ubicaciones = {
    "Bogotá": "Cundinamarca",
    "Medellín": "Antioquia",
    "Cali": "Valle del Cauca",
    "Barranquilla": "Atlántico",
    "Cartagena": "Bolívar",
    "Pereira": "Risaralda"
}

# Aquí puedes alimentar la lista de desarrolladores
dict_desarrolladores = ["Andrés Vanegas", "Laura García", "Carlos Ruiz"]

# --- FUNCIONES DE LÓGICA ---
def obtener_siguiente_id():
    ultimo_registro = visitas_col.find_one(sort=[("Id", -1)])
    if ultimo_registro and "Id" in ultimo_registro:
        return int(ultimo_registro["Id"]) + 1
    return 1

# --- INTERFAZ DEL FORMULARIO ---
st.title("📍 Nuevo Punto")
st.markdown("##### Complete los detalles del punto de venta")

with st.form("form_ios"):
    # 1. ID CONSECUTIVO (Automático)
    proximo_id = obtener_siguiente_id()
    st.text_input("🆔 ID de Registro", value=proximo_id, disabled=True)

    # 2. DESARROLLADOR (Diccionario)
    desarrollador = st.selectbox("👨‍💻 Desarrollador", options=dict_desarrolladores)

    # 3. CIUDAD Y DEPARTAMENTO (Lógica encadenada)
    ciudad = st.selectbox("🏙️ Ciudad", options=list(dict_ubicaciones.keys()))
    departamento = st.text_input("🗺️ Departamento", value=dict_ubicaciones[ciudad], disabled=True)

    # 4. DIRECCIÓN Y UBICACIÓN
    direccion = st.text_input("🏠 Dirección Cercana", placeholder="Ej: Calle 100 #15-20")
    coordenadas = st.text_input("📍 Ubicación (Coordenadas)", placeholder="Latitud, Longitud")

    # 5. ESTADO (Botones segmentados)
    st.write("🔘 **Estado**")
    estado = st.radio("", ["Habilitado", "Deshabilitado"], horizontal=True, label_visibility="collapsed")

    # 6. MES (Basado en tu regla previa de formato texto)
    mes_actual = datetime.now().strftime("%B").capitalize()
    mes = st.text_input("📅 Mes", value=mes_actual)

    # BOTÓN DE ACCIÓN
    submitted = st.form_submit_button("Guardar Registro")

    if submitted:
        nuevo_punto = {
            "Id": proximo_id,
            "Desarrollador": desarrollador,
            "Ciudad": ciudad,
            "Departamento": departamento,
            "Direccion": direccion,
            "Ubicacion": coordenadas,
            "Estado": estado,
            "MES": mes,
            "Timestamp": datetime.now()
        }
        
        try:
            visitas_col.insert_one(nuevo_punto)
            st.success("✅ ¡Punto registrado con éxito!")
            st.balloons()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# Footer minimalista
st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 0.8rem;'>Power Trade | App Interna 2026</p>", unsafe_allow_html=True)
