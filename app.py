import streamlit as st
import os
from pymongo import MongoClient
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Registro Puntos de Venta", layout="centered")

# 1. Conexión a MongoDB
# Nota: En Render, configura MONGO_URI en 'Environment Variables'
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

client = init_connection()
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

st.title("📝 Formulario de Puntos de Venta")
st.markdown("Ingrese la información para actualizar la base de datos.")

# 2. Obtener columnas dinámicamente
# Traemos un registro de muestra para saber qué campos existen
sample_doc = visitas_col.find_one()
if sample_doc:
    # Excluimos el ID de MongoDB para el formulario
    columnas = [key for key in sample_doc.keys() if key != '_id']
else:
    # Columnas por defecto si la colección está vacía
    columnas = ["MES", "NOMBRE_PUNTO", "ESTADO", "VALOR"]

# 3. Crear el Formulario
with st.form("formulario_registro", clear_on_submit=True):
    inputs = {}
    
    for col in columnas:
        # Personalización lógica según tus reglas guardadas:
        if col == "MES":
            inputs[col] = st.text_input(f"{col} (Nombre del mes)")
        elif col == "ESTADO":
            # Aplicando lógica de chulos (-1) y x (vacío)
            inputs[col] = st.selectbox(f"{col}", options=["-1", ""], help="-1 para Positivo, Vacío para Déficit")
        else:
            inputs[col] = st.text_input(f"{col}")

    submit_button = st.form_submit_button("Enviar a MongoDB")

# 4. Lógica de inserción
if submit_button:
    try:
        # Insertar en la colección
        visitas_col.insert_one(inputs)
        st.success("✅ Registro guardado exitosamente en la colección 'Puntos de Venta'.")
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")

# 5. Vista previa de datos (Opcional)
if st.checkbox("Mostrar últimos registros"):
    data = list(visitas_col.find().limit(10))
    if data:
        df = pd.DataFrame(data).drop(columns=['_id'], errors='ignore')
        st.dataframe(df)
