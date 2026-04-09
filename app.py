import os, math
import pandas as pd # Para el reporte Excel
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_pro_2026"

# CONEXIÓN MONGODB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

USUARIOS = {"12345678": "Andrés Vanegas", "87654321": "Admin Power"}

def calcular_distancia(c1, c2):
    try:
        lat1, lon1 = map(float, c1.split(','))
        lat2, lon2 = map(float, c2.split(','))
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)
    except: return 0

@app.route('/')
def home():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('app.html', usuario=session['usuario'])

# --- APIs DE BÚSQUEDA OPTIMIZADA ---

@app.route('/api/buscar_puntos', methods=['GET'])
def buscar_puntos():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    
    # Búsqueda por palabra clave en BMB (como texto) o Nombre de punto (regex no exacta)
    query = {
        "$or": [
            {"Nombre de punto": {"$regex": q, "$options": "i"}},
            {"BMB": {"$regex": q, "$options": "i"}}
        ]
    }
    # Limitamos a 50 resultados para no saturar el móvil
    resultados = list(puntos_col.find(query, {"_id":0}).limit(50))
    return jsonify(resultados)

@app.route('/api/guardar_punto', methods=['POST'])
def guardar_punto():
    data = request.json
    # Estandarizar fecha
    data['Fecha_Creacion'] = datetime.now().strftime("%Y-%m-%d")
    ultimo = puntos_col.find_one(sort=[("Id", -1)])
    data['Id'] = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    puntos_col.insert_one(data)
    return jsonify({"status":"ok"})

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_visita():
    data = request.json
    dist = calcular_distancia(data['ubicacion_punto'], data['ubicacion_actual'])
    data['distancia_real'] = dist
    data['fecha'] = datetime.now().strftime("%Y-%m-%d") # Solo fecha
    visitas_col.insert_one(data)
    return jsonify({"status":"ok", "distancia": dist})

# --- REPORTE EXCEL FILTRADO ---

@app.route('/api/descargar_reporte')
def descargar_reporte():
    f_inicio = request.args.get('inicio')
    f_fin = request.args.get('fin')
    
    query = {"fecha": {"$gte": f_inicio, "$lte": f_fin}}
    datos = list(visitas_col.find(query, {"_id":0}))
    
    if not datos: return "No hay datos en este rango", 404
    
    df = pd.DataFrame(datos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Visitas')
    output.seek(0)
    
    return send_file(output, attachment_filename=f"Reporte_{f_inicio}_al_{f_fin}.xlsx", as_attachment=True)

# (Mantener login y logout igual)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cc = request.form.get('cc'); session['usuario'] = USUARIOS.get(cc)
        if session['usuario']: return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
