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

# --- CONFIGURACIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
fs = gridfs.GridFS(db) 
coleccion = db['Visitas_a_POC']

# --- DATOS MAESTROS (Asegúrate de tener tu lista completa aquí) ---
TABLA_PUNTOS = [
    ["Tienda El Porvenir", "BMB-1010", "Calle 1 #2-3", "4.6097, -74.0817", "Bogotá", "Cundinamarca"],
    ["Almacen Central", "BMB-2020", "Carrera 15 #40-10", "4.6097, -74.0817", "Medellín", "Antioquia"],
]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Direccion": f[2], "Ubicacion_Ref": f[3]} for f in TABLA_PUNTOS]

FUNCIONARIOS = sorted(["ANDRES VANEGAS", "CINDY BOCANEGRA", "KEVIN MARIN"]) # ... Tu lista completa

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/registros')
def ver_registros():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    busqueda = request.args.get('busqueda', '').strip()
    
    registros = []
    if f_inicio and f_fin:
        # Filtro base por fechas
        query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
        
        # Filtro adicional por Nombre o BMB si existe búsqueda
        if busqueda:
            query["$or"] = [
                {"poc": {"$regex": busqueda, "$options": "i"}},
                {"bmb": {"$regex": busqueda, "$options": "i"}}
            ]
            
        registros = list(coleccion.find(query).sort("fecha", -1))
    
    return render_template('registros.html', registros=registros, f_inicio=f_inicio, f_fin=f_fin, busqueda=busqueda)

@app.route('/descargar_excel')
def descargar_excel():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    datos = list(coleccion.find(query))
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
    try:
        archivo = fs.get(ObjectId(foto_id))
        return Response(archivo.read(), mimetype='image/jpeg')
    except: return "", 404

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        f1 = fs.put(request.files['foto_maquina'], filename="maquina.jpg")
        f2 = fs.put(request.files['foto_fachada'], filename="fachada.jpg")
        ahora = get_colombia_time()
        
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "ubicacion_gps_real": request.form.get('gps_real'),
            "distancia_mts": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'), # RESTAURADO
            "observacion": request.form.get('observacion'),
            "foto_maquina_id": str(f1),
            "foto_fachada_id": str(f2),
            "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S")
        }
        coleccion.insert_one(doc)
        return redirect(url_for('ver_registros', f_inicio=ahora.strftime("%Y-%m-%d"), f_fin=ahora.strftime("%Y-%m-%d")))
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
