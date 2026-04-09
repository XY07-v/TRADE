import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "power_trade_secret_key" # Cambia esto por algo seguro

# Conexión a MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

# DICCIONARIO DE USUARIOS (Cédula: Nombre)
USUARIOS = {
    "12345678": "Andrés Vanegas",
    "87654321": "Admin Power",
    "10102020": "Soporte Técnico"
}

@app.route('/')
def root():
    if 'usuario' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

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
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    ultimo = visitas_col.find_one(sort=[("Id", -1)])
    next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    
    # Columnas base a mostrar
    columnas = ["Id", "BMB", "Nombre de punto", "Direccion", "Ubicacion", "Ciudad", "Departamento", "Desarrollador", "Estado", "Rango"]
    
    return render_template('index.html', next_id=next_id, columnas=columnas, usuario=session['usuario'])

@app.route('/guardar', methods=['POST'])
def guardar():
    if 'usuario' not in session:
        return jsonify({"status": "error", "message": "Sesión expirada"}), 401
        
    try:
        data = request.json
        
        # VALIDACIÓN: ¿Existe BMB?
        if visitas_col.find_one({"BMB": data['BMB']}):
            return jsonify({"status": "error", "message": f"El BMB {data['BMB']} ya existe"}), 400
            
        # VALIDACIÓN: ¿Existe Nombre de Punto?
        if visitas_col.find_one({"Nombre de punto": data['Nombre de punto']}):
            return jsonify({"status": "error", "message": f"El punto '{data['Nombre de punto']}' ya existe"}), 400
        
        visitas_col.insert_one(data)
        return jsonify({"status": "success", "message": "Punto registrado con éxito"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
