import os
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Conexión a MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
visitas_col = db['Puntos de Venta']

@app.route('/')
def index():
    # Obtener el consecutivo Id
    ultimo = visitas_col.find_one(sort=[("Id", -1)])
    next_id = (int(ultimo["Id"]) + 1) if ultimo and "Id" in ultimo else 1
    
    # Obtener todas las columnas actuales de la BD para mantener el orden
    sample_doc = visitas_col.find_one()
    if sample_doc:
        columnas = [k for k in sample_doc.keys() if k not in ['_id', 'MES', 'Fecha', 'Fecha_Sistema']]
    else:
        # Estructura base si no hay datos
        columnas = ["Id", "Nombre de punto", "Direccion", "Ubicacion", "Ciudad", "Departamento", "Desarrollador", "Estado", "Rango"]
    
    # Asegurar que 'Nombre de punto' esté en la lista si no existe aún en la estructura
    if "Nombre de punto" not in columnas:
        columnas.insert(1, "Nombre de punto")

    return render_template('index.html', next_id=next_id, columnas=columnas)

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        data = request.json
        # Guardar en MongoDB tal cual viene del formulario
        visitas_col.insert_one(data)
        return jsonify({"status": "success", "message": "Punto registrado correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
