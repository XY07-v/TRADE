import os, math
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# CONEXIÓN (Asegúrate de tener la variable MONGO_URI en Render)
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

@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    datos = list(visitas_col.find().sort("fecha", -1).limit(50))
    return render_template('ver_visitas.html', datos=datos)

@app.route('/nueva_visita')
def nueva_visita():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nueva_visita.html')

@app.route('/nuevo_punto')
def nuevo_punto():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nuevo_punto.html')

@app.route('/ver_puntos')
def ver_puntos():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('ver_puntos.html')

@app.route('/api/buscar')
def buscar():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    query = {"$or": [{"Nombre de punto": {"$regex": q, "$options": "i"}}, {"BMB": {"$regex": q, "$options": "i"}}]}
    return jsonify(list(puntos_col.find(query, {"_id":0}).limit(20)))

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_v():
    data = request.json
    data['distancia_real'] = calcular_distancia(data['ubicacion_punto'], data['ubicacion_actual'])
    data['fecha'] = datetime.now().strftime("%Y-%m-%d")
    data['usuario'] = session.get('usuario')
    visitas_col.insert_one(data)
    return jsonify({"status":"ok", "distancia": data['distancia_real']})

@app.route('/api/guardar_punto', methods=['POST'])
def guardar_p():
    data = request.json
    data['fecha_creacion'] = datetime.now().strftime("%Y-%m-%d")
    puntos_col.insert_one(data)
    return jsonify({"status":"ok"})

@app.route('/descargar')
def descargar():
    ini, fin = request.args.get('ini'), request.args.get('fin')
    df = pd.DataFrame(list(visitas_col.find({"fecha": {"$gte": ini, "$lte": fin}}, {"_id":0})))
    if df.empty: return "No hay datos", 404
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    out.seek(0)
    return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name="Reporte.xlsx", as_attachment=True)

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
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
