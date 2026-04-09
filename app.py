import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# Conexión
client = MongoClient("mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
db = client['POWER_TRADE']

# --- RUTAS ---

@app.route('/')
def index():
    # Obtenemos todas las colecciones excepto la de 'usuarios' y las de sistema
    colecciones = [c for c in db.list_collection_names() if c != 'usuarios' and not c.startswith('system.')]
    return render_template('index.html', colecciones=colecciones)

@app.route('/buscar_punto')
def buscar_punto():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    # Buscamos en la colección 'Puntos de Venta' (o la que definas como maestra)
    # Buscamos por BMB (número/texto) o Nombre de punto (regex para no ser exactos)
    resultados = db['Puntos de Venta'].find({
        "$or": [
            {"Nombre de punto": {"$regex": query, "$options": "i"}},
            {"BMB": {"$regex": query, "$options": "i"}}
        ]
    }).limit(10)
    
    output = []
    for r in resultados:
        output.append({
            "id": str(r["_id"]),
            "nombre": r.get("Nombre de punto", "S/N"),
            "bmb": r.get("BMB", "S/N")
        })
    return jsonify(output)

@app.route('/formulario/<coleccion>/<punto_id>')
def formulario(coleccion, punto_id):
    # Traemos la info del punto para precargar BMB y Nombre
    punto = db['Puntos de Venta'].find_one({"_id": ObjectId(punto_id)})
    
    # Obtenemos un documento de ejemplo de la colección destino para saber qué campos tiene
    ejemplo = db[coleccion].find_one()
    campos = ejemplo.keys() if ejemplo else []
    
    return render_template('formulario.html', 
                           coleccion=coleccion, 
                           punto=punto, 
                           campos=campos)

@app.route('/guardar/<coleccion>', methods=['POST'])
def guardar(coleccion):
    datos = request.form.to_dict()
    db[coleccion].insert_one(datos)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
