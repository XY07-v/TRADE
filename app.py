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
coleccion_visitas = db['Visitas_a_POC']

# --- CONFIGURACIÓN DE FORMULARIOS (Aquí ajustas tus preguntas) ---
CONFIG_FORMULARIOS = {
    "prospecciones": {
        "titulo": "Registro de Prospecto",
        "icono": "fa-magnifying-glass-location",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "contacto", "label": "Nombre del Propietario / Encargado", "type": "text", "required": True},
            {"id": "telefono", "label": "Teléfono de Contacto", "type": "number", "required": True},
            {"id": "direccion", "label": "Dirección Exacta", "type": "text", "required": True},
            {"id": "potencial", "label": "Potencial del Punto", "type": "select", "options": ["Bajo", "Medio", "Alto"], "required": True},
            {"id": "productos", "label": "Productos Interesados", "type": "multiselect", "options": ["Nescafe Alegria Cappuccino 4 X 1 Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco"], "required": True},
            {"id": "competencia", "label": "¿Tiene competencia instalada?", "type": "select", "options": ["Ninguna", "BetPlay", "Wplay", "Rushbet", "Otras"], "required": False},
            {"id": "observaciones", "label": "Notas de la Prospección", "type": "textarea", "required": False}
        ]
    },
    "leads": {
        "titulo": "Gestión de Leads",
        "icono": "fa-user-tie",
        "preguntas": [
            {"id": "cliente", "label": "Nombre Cliente", "type": "text", "required": True},
            {"id": "interes", "label": "Producto de Interés", "type": "multiselect", "options": ["Máquina Café", "Insumos", "Mantenimiento"], "required": True},
            {"id": "estado", "label": "Estado del Lead", "type": "select", "options": ["Nuevo", "En Seguimiento", "Cerrado"], "required": True}
        ]
    },
    "food": {
        "titulo": "Food Service",
        "icono": "fa-utensils",
        "preguntas": [
            {"id": "lugar", "label": "Restaurante/Hotel", "type": "text", "required": True},
            {"id": "consumo", "label": "Insumos requeridos", "type": "multiselect", "options": ["Café Molido", "Leche Polvo", "Chocolate"], "required": True}
        ]
    },
    "competencias": {
        "titulo": "Análisis Competencia",
        "icono": "fa-handshake-slash",
        "preguntas": [
            {"id": "marca", "label": "Marca Competidora", "type": "text", "required": True},
            {"id": "ventaja", "label": "Ventaja Observada", "type": "textarea", "required": False}
        ]
    },
    "ingredientes": {
        "titulo": "Control Ingredientes",
        "icono": "fa-jar",
        "preguntas": [
            {"id": "item", "label": "Ingrediente", "type": "text", "required": True},
            {"id": "alerta", "label": "Estado", "type": "select", "options": ["Suficiente", "Pedido Pendiente", "Agotado"], "required": True}
        ]
    }
}

# --- DATOS MAESTROS ---
FUNCIONARIOS = sorted(["ANDRES VANEGAS", "CINDY BOCANEGRA", "KEVIN MARIN", "MAURICIO LADINO", "MONICA PATIÑO"]) # ... Agrega todos
TABLA_PUNTOS = [["Tienda El Porvenir", "BMB-1010", "4.6097, -74.0817"]]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Ubicacion_Ref": f[2]} for f in TABLA_PUNTOS]

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/form/<tipo>')
def render_form_dinamico(tipo):
    if tipo not in CONFIG_FORMULARIOS: return "Error", 404
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
    datos_raw = request.form.to_dict(flat=False)
    datos_procesados = {k: v if len(v) > 1 else v[0] for k, v in datos_raw.items()}
    datos_procesados["fecha"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
    db[tipo].insert_one(datos_procesados)
    return redirect(url_for('render_form_dinamico', tipo=tipo))

@app.route('/guardar_visita', methods=['POST'])
def guardar_visita():
    f1 = fs.put(request.files['foto_maquina'], filename="maquina.jpg")
    f2 = fs.put(request.files['foto_fachada'], filename="fachada.jpg")
    ahora = get_colombia_time()
    doc = {
        "funcionario": request.form.get('funcionario'),
        "poc": request.form.get('poc'),
        "bmb": request.form.get('bmb'),
        "gps_real": request.form.get('gps_real'),
        "distancia_mts": request.form.get('distancia_metros'),
        "motivo": request.form.get('motivo'),
        "observacion": request.form.get('observacion'),
        "foto_maquina_id": str(f1),
        "foto_fachada_id": str(f2),
        "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S")
    }
    coleccion_visitas.insert_one(doc)
    return redirect(url_for('index'))

@app.route('/registros')
def ver_registros():
    f_inicio = request.args.get('f_inicio', get_colombia_time().strftime("%Y-%m-%d"))
    f_fin = request.args.get('f_fin', get_colombia_time().strftime("%Y-%m-%d"))
    busqueda = request.args.get('busqueda', '').strip()
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    if busqueda:
        query["$or"] = [{"poc": {"$regex": busqueda, "$options": "i"}}, {"bmb": {"$regex": busqueda, "$options": "i"}}]
    registros = list(coleccion_visitas.find(query).sort("fecha", -1))
    return render_template('registros.html', registros=registros, f_inicio=f_inicio, f_fin=f_fin, busqueda=busqueda)

@app.route('/foto/<foto_id>')
def servir_foto(foto_id):
    archivo = fs.get(ObjectId(foto_id))
    return Response(archivo.read(), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
