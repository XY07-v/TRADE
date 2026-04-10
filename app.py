import os
import json
import gridfs
import pytz
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "power_trade_ultra_2026")

# --- CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
fs = gridfs.GridFS(db) 

# --- CONFIGURACIÓN DE FORMULARIOS DINÁMICOS ---
# Aquí defines las preguntas para cada una de las nuevas secciones
CONFIG_FORMULARIOS = {
    "prospecciones": {
        "titulo": "Registro de Prospecto",
        "icono": "fa-magnifying-glass-location",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "productos", "label": "Productos", "type": "multiselect", "options": ["Nescafe Alegria Cappuccino 4 X 1 Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco"], "required": True},
            {"id": "observaciones", "label": "Notas", "type": "textarea", "required": False}
        ]
    },
    "leads": {
        "titulo": "Gestión de Leads",
        "icono": "fa-user-tie",
        "preguntas": [
            {"id": "cliente", "label": "Nombre del Cliente Potencial", "type": "text", "required": True},
            {"id": "origen", "label": "Origen del Lead", "type": "select", "options": ["Redes Sociales", "Referido", "Feria", "Directo"], "required": True},
            {"id": "prioridad", "label": "Prioridad", "type": "select", "options": ["Baja", "Media", "Alta"], "required": True}
        ]
    },
    "food": {
        "titulo": "Registro Food Service",
        "icono": "fa-utensils",
        "preguntas": [
            {"id": "establecimiento", "label": "Restaurante / Cafetería", "type": "text", "required": True},
            {"id": "tipo_comida", "label": "Categoría", "type": "select", "options": ["Rápida", "Gourmet", "Panadería", "Institucional"], "required": True},
            {"id": "consumo_estimado", "label": "Consumo Mensual (Kg)", "type": "number", "required": False}
        ]
    },
    "competencias": {
        "titulo": "Análisis de Competencia",
        "icono": "fa-handshake-slash",
        "preguntas": [
            {"id": "marca", "label": "Marca Competidora", "type": "text", "required": True},
            {"id": "modelo_negocio", "label": "Modelo Instalado", "type": "select", "options": ["Comodato", "Venta Directo", "Alquiler"], "required": True},
            {"id": "precios", "label": "Observación de Precios", "type": "textarea", "required": False}
        ]
    },
    "ingredientes": {
        "titulo": "Control de Ingredientes",
        "icono": "fa-jar",
        "preguntas": [
            {"id": "ingrediente", "label": "Nombre del Insumo", "type": "text", "required": True},
            {"id": "estado", "label": "Estado de Inventario", "type": "select", "options": ["Stock Ok", "Crítico", "Agotado"], "required": True},
            {"id": "lote", "label": "Número de Lote", "type": "text", "required": False}
        ]
    }
}

# --- DATOS MAESTROS ---
FUNCIONARIOS = sorted(["ANDRES VANEGAS", "CINDY BOCANEGRA", "KEVIN MARIN"]) # ... Agrega tu lista completa aquí
TABLA_PUNTOS = [["Tienda El Porvenir", "BMB-1010", "4.6097, -74.0817"]]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Ubicacion_Ref": f[2]} for f in TABLA_PUNTOS]

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

# Ruta Genérica para los 5 formularios
@app.route('/form/<tipo>')
def render_form_dinamico(tipo):
    if tipo not in CONFIG_FORMULARIOS: return "Formulario no encontrado", 404
    config = CONFIG_FORMULARIOS[tipo]
    return render_template('prospecciones.html', 
                           funcionarios=FUNCIONARIOS, 
                           preguntas=config['preguntas'], 
                           titulo=config['titulo'], 
                           icono=config['icono'],
                           tipo_url=tipo)

@app.route('/guardar_dinamico/<tipo>', methods=['POST'])
def guardar_dinamico(tipo):
    ahora = get_colombia_time()
    # flat=False para capturar listas del multiselect
    datos_raw = request.form.to_dict(flat=False)
    datos_procesados = {k: v if len(v) > 1 else v[0] for k, v in datos_raw.items()}
    
    datos_procesados["fecha_registro"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
    datos_procesados["tipo_formulario"] = tipo.upper()
    
    # Se guarda en la colección correspondiente al tipo (ej: db['leads'])
    db[tipo].insert_one(datos_procesados)
    return redirect(url_for('render_form_dinamico', tipo=tipo))

@app.route('/registros')
def ver_registros():
    # ... (Se mantiene igual que la versión anterior para Visitas a POC)
    return render_template('registros.html', registros=[], f_inicio="", f_fin="", busqueda="")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
