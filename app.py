import os, math
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pt_gold_2026"

# Conexión
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas'] # Nueva colección

USUARIOS = {"12345678": "Andrés Vanegas", "87654321": "Admin Power"}

def calcular_distancia(coords1, coords2):
    # Coords en formato "lat, lon"
    try:
        lat1, lon1 = map(float, coords1.split(','))
        lat2, lon2 = map(float, coords2.split(','))
        R = 6371000 # Radio Tierra en metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

@app.route('/')
def root():
    return redirect(url_for('login')) if 'usuario' not in session else render_template('app.html', usuario=session['usuario'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cc = request.form.get('cc')
        if cc in USUARIOS:
            session['usuario'] = USUARIOS[cc]
            return redirect(url_for('root'))
        return render_template('login.html', error="Cédula no registrada")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API: Obtener puntos para búsqueda
@app.route('/api/puntos')
def get_puntos():
    puntos = list(puntos_col.find({}, {"_id":0, "Nombre de punto":1, "BMB":1, "Ubicacion":1, "Rango":1}))
    return jsonify(puntos)

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_visita():
    data = request.json
    # Validación de distancia
    distancia = calcular_distancia(data['ubicacion_punto'], data['ubicacion_actual'])
    data['diferencia_metros'] = round(distancia, 2)
    data['fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    visitas_col.insert_one(data)
    return jsonify({"status": "ok", "distancia": data['diferencia_metros']})

@app.route('/api/historial_visitas')
def historial():
    return jsonify(list(visitas_col.find({}, {"_id":0}).sort("fecha", -1)))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
