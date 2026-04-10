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
coleccion_prospecciones = db['Prospecciones']

# --- CONFIGURACIÓN DE PREGUNTAS DE PROSPECCIÓN (MODIFICA AQUÍ) ---
PREGUNTAS_PROSPECCION = [
    {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
    {"id": "contacto", "label": "Nombre del Propietario / Encargado", "type": "text", "required": True},
    {"id": "telefono", "label": "Teléfono de Contacto", "type": "number", "required": True},
    {"id": "direccion", "label": "Dirección Exacta", "type": "text", "required": True},
    {"id": "Sector", "label": "Potencial del Punto", "type": "select", "options": ["Cafeteria", "Tinteros", "Transporte"], "required": True},
    {"id": "potencial", "label": "Potencial del Punto", "type": "select", "options": ["Maquina", "Food", "Ambos","No esta interesado"], "required": True},
    {"id": "Productos", "label": "Productos", "type": "select", "options": ["Nescafe Alegria Cappuccino 4 X 1 Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco", "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco","Nescafe Alegria Cappu Vainillanp 4 X 1Kgco"], "required": True},
    {"id": "Efectividad", "label": "Venta efectiva?", "type": "select", "options": ["Ninguna", "BetPlay", "Wplay", "Rushbet", "Otras"], "required": False},
    {"id": "Seguimiento", "label": "Queda en seguimiento?", "type": "textarea", "required": False},
    {"id": "Observaciones", "label": "Observaciones", "type": "textarea", "required": False}
]

# --- DATOS MAESTROS ---
FUNCIONARIOS = sorted([
    "ANDRES VANEGAS", "CINDY JULIETH BOCANEGRA GARZON", "CINDY PAOLA CASTRO OROZCO", 
    "CRISTIAN CAMILO BAQUERO MURCIA", "DIANA MARCELA ERAZO CAICEDO", "EDWIN ALEXANDER FORERO VELASQUEZ", 
    "ELIECER ARDILA LUCIO", "ESNEYDI YELEYSI JIMENEZ JIMENEZ", "FABIANA ARDILA ORTEGA", 
    "GERALDINE RAMIREZ MORENO", "HAYDE CAROLINA ORJUELA FORIGUA", "JHEINER ALBEIRO AMADO LOZANO", 
    "JOHN EDISON MERCHAN SEGURA", "JUAN CAMILO PADILLA GRAVIER", "KELLY JOHANA BARRERA DE AVILA", 
    "KEVIN SANTIAGO MARIN GALEANO", "LUZ MARLENE RESTREPO -", "MAURICIO LADINO LARGO", 
    "MICHAEL GONZALEZ RODRIGUEZ", "MONICA MARIA PATIÑO P", "MONICA MILENA OTALVARO METAUTE", 
    "NESTOR ANDRES CARMONA HUERTAS", "RIGOBERTO SIERRA PELAEZ", "SHIRLEY YEPES BETANCUR", 
    "SIGIFREDO RAMIREZ SARAY", "VANESA MONTOYA BUITRAGO", "WILSON JAVIER GRIMALDO NAVARRO", 
    "YEIMI PAOLA CASTRILLON URREGO", "YEISON JOSE GONZALES BERRIO", "YOANA ANDREA HINCAPIE ZEA"
])

TABLA_PUNTOS = [
    ["Tienda El Porvenir", "BMB-1010", "4.6097, -74.0817"],
    ["Almacen Central", "BMB-2020", "6.2442, -75.5812"]
]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Ubicacion_Ref": f[2]} for f in TABLA_PUNTOS]

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/prospecciones')
def prospecciones():
    return render_template('prospecciones.html', funcionarios=FUNCIONARIOS, preguntas=PREGUNTAS_PROSPECCION)

@app.route('/registros')
def ver_registros():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    busqueda = request.args.get('busqueda', '').strip()
    registros = []
    if f_inicio and f_fin:
        query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
        if busqueda:
            query["$or"] = [{"poc": {"$regex": busqueda, "$options": "i"}}, {"bmb": {"$regex": busqueda, "$options": "i"}}]
        registros = list(coleccion_visitas.find(query).sort("fecha", -1))
    return render_template('registros.html', registros=registros, f_inicio=f_inicio, f_fin=f_fin, busqueda=busqueda)

@app.route('/guardar_visita', methods=['POST'])
def guardar_visita():
    try:
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
        return redirect(url_for('ver_registros', f_inicio=ahora.strftime("%Y-%m-%d"), f_fin=ahora.strftime("%Y-%m-%d")))
    except Exception as e: return f"Error: {e}", 500

@app.route('/guardar_prospeccion', methods=['POST'])
def guardar_prospeccion():
    ahora = get_colombia_time()
    datos = request.form.to_dict()
    datos["fecha"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
    coleccion_prospecciones.insert_one(datos)
    return redirect(url_for('prospecciones'))

@app.route('/descargar_excel')
def descargar_excel():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    datos = list(coleccion_visitas.find(query))
    if not datos: return "No hay datos", 404
    df = pd.DataFrame(datos)
    for col in ['_id', 'foto_maquina_id', 'foto_fachada_id']:
        if col in df.columns: del df[col]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"Reporte_PowerTrade.xlsx")

@app.route('/foto/<foto_id>')
def servir_foto(foto_id):
    archivo = fs.get(ObjectId(foto_id))
    return Response(archivo.read(), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
