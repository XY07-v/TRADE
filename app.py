import os
import json
import gridfs
import pytz
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "power_trade_ultra_2026")

# --- CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
fs = gridfs.GridFS(db) 
coleccion_visitas = db['Visitas_a_POC']

# --- CONFIGURACIÓN DE FORMULARIOS DINÁMICOS ---
CONFIG_FORMULARIOS = {
    "prospecciones": {
        "titulo": "Registro de Prospecto",
        "icono": "fa-magnifying-glass-location",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "contacto", "label": "Nombre Propietario", "type": "text", "required": True},
            {"id": "telefono", "label": "Teléfono", "type": "number", "required": True},
            {"id": "direccion", "label": "Dirección", "type": "text", "required": True},
            {"id": "Sector", "label": "Sector", "type": "select", "options": ["Educacion", "Cafeteria", "Panaderia","Restaurante","Salud","Transporte","Tinteros"], "required": True},
            {"id": "Interesado en?", "label": "Interesado en?", "type": "select", "options": ["Maquina", "Food", "Ambos","No esta interesado"], "required": True},
            {"id": "productos", "label": "Productos", "type": "multiselect", "options": 
             ["Maquina",
              "Nescafe Alegria Cappuccino 4 X 1 Kgco", 
              "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco",
              "Nescafe Alegria Cappuccino 4 X 1 Kgco",
                "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco",
                "Nescafe Alegria Cappu Vainillanp 4 X 1Kgco",
                "Abuelita Chocolate Venta 6 X 750G Mx ",
                "Nescafe Cafe En Grano Npro 6 X 1Kg Co",
                "Nestle Cobertura De Cacao Leche 2 X 5Kg Co",
                "Nestle Cobertura Cac Semiamarga 2 X 5Kg Co",
                "La Lechera Leche Condensada 4 X 4.5Kg Co",
                "La Lechera Npro Leche Condensada6 X 800Gco",
                "Nescafe Dolca Npro 11 X 1Kg Co",

              "Milo Granulado", "Leche Nestlé"], "required": True},
            
            {"id": "Venta Efectiva", "label": "Venta Efectiva", "type": "select", "options": ["Si", "No"], "required": True},
            {"id": "Seguimiento", "label": "Seguimiento", "type": "select", "options": ["Si", "No"], "required": True},
            {"id": "observaciones", "label": "Notas", "type": "textarea", "required": False}
        ]
    },
    "leads": {
        "titulo": "Gestión de Leads", "icono": "fa-user-tie",
        "preguntas": [
            {"id": "cliente", "label": "Nombre Cliente", "type": "text", "required": True},
            {"id": "interes", "label": "Interés", "type": "multiselect", "options": ["Máquina Café", "Insumos", "Soporte"], "required": True},
            {"id": "estado", "label": "Estado", "type": "select", "options": ["Nuevo", "Seguimiento", "Cerrado"], "required": True}
        ]
    },
    "food": {
        "titulo": "Food Service", "icono": "fa-utensils",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "Producto #1", "label": "Categoría", "type": "select", "options": [
                "Aro - Caldo Desmenuzado 800 Grs",
"Aro - Caldo gallina 1 Kg",
"Aro - Base bechamel Aro x 1 Kg",
"Aro - Leche condesada Aro x 1.3 Kg",
"Aro - Leche condesada Aro x 3.9 Kg",
"Aro - Leche condesada Aro x 5 Kg",
"Bugueña - Leche condensada la bugueña x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Carreta - Leche condensada la Carreta x 1 Kg",
"Carreta - Leche condensada la Carreta x 5 Kg",
"Colombina - Nucita x 1 Kg",
"Colombina - Nucita x 1.5 Kg"
            ], "required": True}
            
            {"id": "Precio #1", "label": "Categoría",  "type": "text", "required": True},
        ]
    },
    "competencias": {
        "titulo": "Competencia", "icono": "fa-handshake-slash",
        "preguntas": [
            {"id": "marca", "label": "Marca Competidora", "type": "text", "required": True},
            {"id": "modelo", "label": "Modelo", "type": "select", "options": ["Venta", "Comodato"], "required": True}
        ]
    },
    "ingredientes": {
        "titulo": "Insumos e Ingredientes", "icono": "fa-jar",
        "preguntas": [
            {"id": "item", "label": "Ingrediente", "type": "text", "required": True},
            {"id": "stock", "label": "Estado", "type": "select", "options": ["Ok", "Bajo", "Agotado"], "required": True}
        ]
    }
}

# --- DATOS MAESTROS ---
FUNCIONARIOS = sorted(["ANDRES VANEGAS", "CINDY BOCANEGRA", "KEVIN MARIN", "MAURICIO LADINO", "MONICA PATIÑO"])
TABLA_PUNTOS = [["Tienda El Porvenir", "BMB-1010", "4.6097, -74.0817"]]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Ubicacion_Ref": f[2]} for f in TABLA_PUNTOS]

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/form/<tipo>')
def render_form_dinamico(tipo):
    if tipo not in CONFIG_FORMULARIOS: return "Error", 404
    config = CONFIG_FORMULARIOS[tipo]
    return render_template('prospecciones.html', funcionarios=FUNCIONARIOS, preguntas=config['preguntas'], titulo=config['titulo'], icono=config['icono'], tipo_url=tipo)


@app.route('/guardar_dinamico/<tipo>', methods=['POST'])
def guardar_dinamico(tipo):
    ahora = get_colombia_time()
    datos_raw = request.form.to_dict(flat=False)
    datos_procesados = {k: v if len(v) > 1 else v[0] for k, v in datos_raw.items()}
    datos_procesados["fecha"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
    db[tipo].insert_one(datos_procesados)
    return redirect(url_for('render_form_dinamico', tipo=tipo))

@app.route('/guardar_visita', methods=['POST'])
def guardar_visita():
    try:
        f1 = fs.put(request.files['foto_maquina'], filename="maquina.jpg")
        f2 = fs.put(request.files['foto_fachada'], filename="fachada.jpg")
        ahora = get_colombia_time()
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "gps_real": request.form.get('gps_real'),
            "distancia_mts": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "foto_maquina_id": str(f1),
            "foto_fachada_id": str(f2),
            "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S")
        }
        coleccion_visitas.insert_one(doc)
        return redirect(url_for('ver_registros', f_inicio=ahora.strftime("%Y-%m-%d"), f_fin=ahora.strftime("%Y-%m-%d")))
    except Exception as e: return f"Error: {e}", 500

@app.route('/registros')
def ver_registros():
    f_inicio = request.args.get('f_inicio', get_colombia_time().strftime("%Y-%m-%d"))
    f_fin = request.args.get('f_fin', get_colombia_time().strftime("%Y-%m-%d"))
    busqueda = request.args.get('busqueda', '').strip()
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    if busqueda:
        query["$or"] = [{"poc": {"$regex": busqueda, "$options": "i"}}, {"bmb": {"$regex": busqueda, "$options": "i"}}]
    registros = list(coleccion_visitas.find(query).sort("fecha", -1))
    return render_template('registros.html', registros=registros, f_inicio=f_inicio, f_fin=f_fin, busqueda=busqueda)

@app.route('/descargar_excel')
def descargar_excel():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    datos = list(coleccion_visitas.find(query))
    if not datos: return "No hay datos", 404
    df = pd.DataFrame(datos)
    for col in ['_id', 'foto_maquina_id', 'foto_fachada_id']:
        if col in df.columns: del df[col]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"PowerTrade_{f_inicio}.xlsx")

@app.route('/foto/<foto_id>')
def servir_foto(foto_id):
    archivo = fs.get(ObjectId(foto_id))
    return Response(archivo.read(), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
