import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pt_secret_2026" # Clave para sesiones

# Conexión a MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# Diccionario de Usuarios (Cédula: Nombre)
USUARIOS = {
    "12345678": "Andrés Vanegas",
    "87654321": "Admin Power",
    "10102020": "Soporte Técnico"
}

@app.route('/')
def root():
    return redirect(url_for('login')) if 'usuario' not in session else redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cc = request.form.get('cc')
        if cc in USUARIOS:
            session['usuario'] = USUARIOS[cc]
            return redirect(url_for('index'))
        return render_template('login.html', error="Cédula no registrada")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    ultimo = visitas_col.find_one(sort=[("Id", -1)])
    next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    # Definición de columnas a mostrar
    columnas = ["Id", "BMB", "Nombre de punto", "Direccion", "Ubicacion", "Ciudad", "Departamento", "Desarrollador", "Estado", "Rango"]
    return render_template('index.html', next_id=next_id, columnas=columnas, usuario=session['usuario'])

@app.route('/registros')
def registros():
    if 'usuario' not in session: return redirect(url_for('login'))
    datos = list(visitas_col.find().sort("Id", -1))
    return render_template('registros.html', datos=datos)

@app.route('/guardar', methods=['POST'])
def guardar():
    if 'usuario' not in session: return jsonify({"status": "error"}), 401
    try:
        data = request.json
        # VALIDACIONES
        if visitas_col.find_one({"BMB": data['BMB']}):
            return jsonify({"status": "error", "message": f"El BMB {data['BMB']} ya existe"}), 400
        if visitas_col.find_one({"Nombre de punto": data['Nombre de punto']}):
            return jsonify({"status": "error", "message": "El Nombre de punto ya existe"}), 400
        
        visitas_col.insert_one(data)
        return jsonify({"status": "success", "message": "Punto guardado con éxito"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
