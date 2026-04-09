import os, math
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# CONEXIÓN
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

USUARIOS = {"12345678": "Andres Vanegas", "87654321": "Admin"}

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

# --- VISTAS ---

@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    # Carga inicial: últimos 50 registros
    datos = list(visitas_col.find().sort("fecha", -1).limit(50))
    return render_template('ver_visitas.html', datos=datos)

# (Rutas /nueva_visita, /nuevo_punto, /ver_puntos se mantienen igual que antes)

# --- APIs ACTUALIZADAS ---

@app.route('/api/filtrar_historial')
def filtrar_historial():
    q = request.args.get('q', '').strip()
    ini = request.args.get('ini', '')
    fin = request.args.get('fin', '')
    
    query = {}
    
    # Filtro por texto (Nombre o BMB)
    if q:
        query["$or"] = [
            {"Nombre de punto": {"$regex": q, "$options": "i"}},
            {"BMB": {"$regex": q, "$options": "i"}}
        ]
    
    # Filtro por rango de fechas
    if ini and fin:
        query["fecha"] = {"$gte": ini, "$lte": fin}
    elif ini:
        query["fecha"] = {"$gte": ini}
    elif fin:
        query["fecha"] = {"$lte": fin}

    visitas = list(visitas_col.find(query, {"_id": 0}).sort("fecha", -1).limit(100))
    return jsonify(visitas)

@app.route('/descargar')
def descargar():
    ini = request.args.get('ini')
    fin = request.args.get('fin')
    
    if not ini or not fin:
        return "Rango de fechas requerido", 400

    query = {"fecha": {"$gte": ini, "$lte": fin}}
    datos = list(visitas_col.find(query, {"_id":0}))
    
    if not datos:
        return "No hay datos para este periodo", 404
    
    df = pd.DataFrame(datos)
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    out.seek(0)
    
    return send_file(
        out, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        download_name=f"Reporte_{ini}_{fin}.xlsx", 
        as_attachment=True
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cc = request.form.get('cc')
        if cc in USUARIOS:
            session['usuario'] = USUARIOS[cc]
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
