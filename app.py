import os, math, base64
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Se utiliza la URI de MongoDB proporcionada
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

# Base de datos de usuarios (CC: Nombre)
USUARIOS = {"12345678": "Andres Vanegas", "87654321": "Admin"}

# --- UTILIDADES ---
def calcular_distancia(c1, c2):
    """Calcula la distancia en metros entre dos coordenadas GPS usando Haversine."""
    try:
        if not c1 or not c2: return 0
        lat1, lon1 = map(float, c1.split(','))
        lat2, lon2 = map(float, c2.split(','))
        R = 6371000  # Radio de la Tierra en metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)
    except:
        return 0

# --- VISTAS PRINCIPALES (PÁGINAS HTML) ---

@app.route('/')
def index():
    """Historial de Visitas (Página principal)."""
    if 'usuario' not in session: return redirect(url_for('login'))
    datos = list(visitas_col.find().sort("fecha", -1).limit(50))
    return render_template('ver_visitas.html', datos=datos)

@app.route('/nueva_visita')
def nueva_visita():
    """Formulario para reportar visita con fotos y motivo."""
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nueva_visita.html')

@app.route('/nuevo_punto')
def nuevo_punto():
    """Formulario para crear un nuevo punto de venta."""
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nuevo_punto.html')

@app.route('/ver_puntos')
def ver_puntos():
    """Listado de puntos de venta registrados."""
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('ver_puntos.html')

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

# --- APIs DE CONSULTA ---

@app.route('/api/buscar')
def buscar():
    """Busca puntos por nombre o BMB."""
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    query = {"$or": [
        {"Nombre de punto": {"$regex": q, "$options": "i"}},
        {"BMB": {"$regex": q, "$options": "i"}}
    ]}
    return jsonify(list(puntos_col.find(query, {"_id":0}).limit(20)))

@app.route('/api/filtrar_historial')
def filtrar_historial():
    """Filtra el historial de visitas por nombre/BMB y fechas."""
    q = request.args.get('q', '').strip()
    ini = request.args.get('ini', '')
    fin = request.args.get('fin', '')
    query = {}
    if q:
        query["$or"] = [
            {"Nombre de punto": {"$regex": q, "$options": "i"}},
            {"BMB": {"$regex": q, "$options": "i"}}
        ]
    if ini and fin:
        query["fecha"] = {"$gte": ini, "$lte": fin}
    
    visitas = list(visitas_col.find(query, {"_id": 0}).sort("fecha", -1).limit(100))
    return jsonify(visitas)

# --- APIs DE GUARDADO (POST) ---

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_v():
    """Guarda una visita incluyendo imágenes en Base64 y el motivo seleccionado."""
    if 'usuario' not in session: return jsonify({"status":"error", "msg":"Sesión expirada"}), 401
    
    data = request.form
    f_maquina = request.files.get('foto_maquina')
    f_fachada = request.files.get('foto_fachada')

    if not f_maquina or not f_fachada:
        return jsonify({"status":"error", "msg":"Fotos obligatorias faltantes"}), 400

    doc = {
        "Nombre de punto": data.get('Nombre de punto'),
        "BMB": data.get('BMB'),
        "motivo": data.get('motivo'),
        "observacion": data.get('observacion'),
        "ubicacion_punto": data.get('ubicacion_punto'),
        "ubicacion_actual": data.get('ubicacion_actual'),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "usuario": session.get('usuario'),
        "distancia_real": calcular_distancia(data.get('ubicacion_punto'), data.get('ubicacion_actual'))
    }

    # Procesamiento de imágenes (Lectura y codificación)
    doc['foto_maquina'] = f"data:{f_maquina.content_type};base64,{base64.b64encode(f_maquina.read()).decode()}"
    doc['foto_fachada'] = f"data:{f_fachada.content_type};base64,{base64.b64encode(f_fachada.read()).decode()}"

    visitas_col.insert_one(doc)
    return jsonify({"status":"ok", "distancia": doc['distancia_real']})

@app.route('/api/guardar_punto', methods=['POST'])
def guardar_p():
    """Registra un nuevo punto de venta."""
    if 'usuario' not in session: return jsonify({"status":"error"}), 401
    data = request.json
    data['fecha_creacion'] = datetime.now().strftime("%Y-%m-%d")
    puntos_col.insert_one(data)
    return jsonify({"status":"ok"})

# --- EXPORTACIÓN Y DESCARGAS ---

@app.route('/descargar')
def descargar():
    """Genera reporte Excel filtrado por fechas."""
    ini = request.args.get('ini')
    fin = request.args.get('fin')
    
    query = {"fecha": {"$gte": ini, "$lte": fin}}
    visitas = list(visitas_col.find(query, {"_id":0}))
    
    if not visitas: return "No hay datos para el rango seleccionado", 404
    
    df = pd.DataFrame(visitas)
    
    # Limpieza: No exportamos las imágenes pesadas al Excel
    if 'foto_maquina' in df.columns: df.drop(columns=['foto_maquina'], inplace=True)
    if 'foto_fachada' in df.columns: df.drop(columns=['foto_fachada'], inplace=True)
    
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte de Visitas')
    out.seek(0)
    
    return send_file(
        out, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        download_name=f"Reporte_PowerTrade_{ini}.xlsx", 
        as_attachment=True
    )

if __name__ == '__main__':
    # Configuración de puerto para despliegue
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
