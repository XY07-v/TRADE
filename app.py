import os, math, base64
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONEXIÓN ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

USUARIOS = {"12345678": "Andres Vanegas"}

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

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

# --- MOTOR DE CONSULTA (Bajo Demanda) ---
@app.route('/api/consultar', methods=['GET'])
def consultar():
    coleccion = request.args.get('col') # 'puntos' o 'visitas'
    q = request.args.get('q', '').strip()
    
    query = {}
    if q:
        query = {"$or": [
            {"Nombre de punto": {"$regex": q, "$options": "i"}},
            {"BMB": {"$regex": q, "$options": "i"}},
            {"usuario": {"$regex": q, "$options": "i"}}
        ]}

    if coleccion == 'puntos':
        # Trae todos los campos del punto
        res = list(puntos_col.find(query).limit(50))
    else:
        # IMPORTANTE: Excluimos las fotos para que la consulta sea instantánea y no de error
        res = list(visitas_col.find(query, {"foto_maquina": 0, "foto_fachada": 0}).sort("fecha", -1).limit(50))
    
    for doc in res: doc['_id'] = str(doc['_id'])
    return jsonify(res)

# --- MOTOR DE INYECCIÓN (Guardado) ---
@app.route('/api/inyectar', methods=['POST'])
def inyectar():
    if 'usuario' not in session: return jsonify({"status": "error"}), 401
    
    target = request.form.get('target') # 'punto' o 'visita'
    data = dict(request.form)
    
    if target == 'punto':
        puntos_col.insert_one({
            "BMB": data.get('BMB'),
            "Nombre de punto": data.get('Nombre'),
            "Ubicacion": data.get('GPS'),
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d")
        })
    else:
        # Inyectar Visita con fotos
        f1 = request.files.get('foto1')
        f2 = request.files.get('foto2')
        doc = {
            "Nombre de punto": data.get('Nombre'),
            "BMB": data.get('BMB'),
            "motivo": data.get('motivo'),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "usuario": session['usuario'],
            "ubicacion_actual": data.get('GPS')
        }
        if f1: doc['foto_maquina'] = f"data:{f1.content_type};base64,{base64.b64encode(f1.read()).decode()}"
        if f2: doc['foto_fachada'] = f"data:{f2.content_type};base64,{base64.b64encode(f2.read()).decode()}"
        visitas_col.insert_one(doc)
        
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
