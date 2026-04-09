import os
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Conexión
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

@app.route('/')
def index():
    # 1. Obtener consecutivo
    ultimo = visitas_col.find_one(sort=[("Id", -1)])
    next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    
    # 2. Obtener TODAS las columnas de la BD (basado en el primer registro)
    sample_doc = visitas_col.find_one()
    if sample_doc:
        columnas = [k for k in sample_doc.keys() if k != '_id']
    else:
        # Columnas mínimas si la BD está vacía
        columnas = ["Id", "Direccion", "Ubicacion", "Ciudad", "Departamento", "Desarrollador", "Estado", "MES", "Rango"]
    
    return render_template('index.html', next_id=next_id, columnas=columnas)

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        data = request.json
        data['Fecha_Sistema'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        visitas_col.insert_one(data)
        return jsonify({"status": "success", "message": "Registro guardado correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
