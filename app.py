import os, math
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_final_2026"

# CONEXIÓN MONGODB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

# USUARIOS (Cédula: Nombre)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cc = request.form.get('cc')
        if cc in USUARIOS:
            session['usuario'] = USUARIOS[cc]
            return redirect(url_for('home'))
        return render_template('login.html', error="Cédula incorrecta")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- APIs ---

@app.route('/api/puntos', methods=['GET'])
def get_puntos():
    return jsonify(list(puntos_col.find({}, {"_id":0}).sort("Id", -1)))

@app.route('/api/guardar_punto', methods=['POST'])
def guardar_punto():
    try:
        data = request.json
        # Validar duplicados
        if puntos_col.find_one({"BMB": data['BMB']}): return jsonify({"status":"err", "msg":"BMB ya existe"}), 400
        if puntos_col.find_one({"Nombre de punto": data['Nombre de punto']}): return jsonify({"status":"err", "msg":"Nombre ya existe"}), 400
        
        # Obtener siguiente ID
        ultimo = puntos_col.find_one(sort=[("Id", -1)])
        data['Id'] = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
        
        puntos_col.insert_one(data)
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"err", "msg": str(e)}), 500

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_visita():
    data = request.json
    dist = calcular_distancia(data['ubicacion_punto'], data['ubicacion_actual'])
    data['distancia_real'] = dist
    data['fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visitas_col.insert_one(data)
    return jsonify({"status":"ok", "distancia": dist})

@app.route('/api/historial')
def get_historial():
    return jsonify(list(visitas_col.find({}, {"_id":0}).sort("fecha", -1)))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
