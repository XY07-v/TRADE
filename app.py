import os, math, base64
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONEXIÓN A MONGODB ---
try:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['POWER_TRADE']
    puntos_col = db['Puntos de Venta']
    visitas_col = db['Visitas']
    client.admin.command('ping')
except Exception as e:
    print(f"ERROR CRÍTICO DE CONEXIÓN: {e}")

USUARIOS = {"12345678": "Andres Vanegas", "87654321": "Admin"}

def calcular_distancia(c1, c2):
    try:
        if not c1 or not c2: return 0
        lat1, lon1 = map(float, c1.split(','))
        lat2, lon2 = map(float, c2.split(','))
        R = 6371000 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)
    except: return 0

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        # CORRECCIÓN: Se agrega allowDiskUse=True para manejar el volumen de fotos en el ordenamiento
        cursor = visitas_col.find().sort("fecha", -1).limit(50).allow_disk_use(True)
        datos = list(cursor)
        return render_template('ver_visitas.html', datos=datos)
    except Exception as e:
        return f"Error en la base de datos: {e}", 500

@app.route('/nueva_visita')
def nueva_visita():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nueva_visita.html')

@app.route('/ver_puntos')
def ver_puntos():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('ver_puntos.html')

@app.route('/nuevo_punto')
def nuevo_punto():
    if 'usuario' not in session: return redirect(url_for('login'))
    return render_template('nuevo_punto.html')

# --- SISTEMA DE ACCESO ---

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
    q = request.args.get('q', '').strip()
    try:
        query = {}
        if q:
            query = {"$or": [{"Nombre de punto": {"$regex": q, "$options": "i"}}, {"BMB": {"$regex": q, "$options": "i"}}]}
        res = list(puntos_col.find(query, {"_id":0}).limit(20))
        return jsonify(res)
    except:
        return jsonify([])

@app.route('/api/filtrar_historial')
def filtrar_historial():
    q = request.args.get('q', '').strip()
    ini = request.args.get('ini', '')
    fin = request.args.get('fin', '')
    query = {}
    if q:
        query["$or"] = [{"Nombre de punto": {"$regex": q, "$options": "i"}}, {"BMB": {"$regex": q, "$options": "i"}}]
    if ini and fin:
        query["fecha"] = {"$gte": ini, "$lte": fin}
    
    try:
        # CORRECCIÓN: Se agrega allowDiskUse=True también aquí
        cursor = visitas_col.find(query, {"_id": 0}).sort("fecha", -1).limit(100).allow_disk_use(True)
        res = list(cursor)
        return jsonify(res)
    except:
        return jsonify([])

# --- APIs DE GUARDADO ---

@app.route('/api/guardar_visita', methods=['POST'])
def guardar_v():
    if 'usuario' not in session: return jsonify({"status":"error"}), 401
    try:
        data = request.form
        f_maquina = request.files.get('foto_maquina')
        f_fachada = request.files.get('foto_fachada')

        if not f_maquina or not f_fachada:
            return jsonify({"status":"error", "msg":"Fotos faltantes"}), 400

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

        doc['foto_maquina'] = f"data:{f_maquina.content_type};base64,{base64.b64encode(f_maquina.read()).decode()}"
        doc['foto_fachada'] = f"data:{f_fachada.content_type};base64,{base64.b64encode(f_fachada.read()).decode()}"

        visitas_col.insert_one(doc)
        return jsonify({"status":"ok", "distancia": doc['distancia_real']})
    except Exception as e:
        return jsonify({"status":"error", "msg": str(e)}), 500

@app.route('/api/guardar_punto', methods=['POST'])
def guardar_p():
    if 'usuario' not in session: return jsonify({"status":"error"}), 401
    try:
        data = request.json
        data['fecha_creacion'] = datetime.now().strftime("%Y-%m-%d")
        puntos_col.insert_one(data)
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error", "msg": str(e)}), 500

# --- EXPORTACIÓN ---

@app.route('/descargar')
def descargar():
    ini = request.args.get('ini')
    fin = request.args.get('fin')
    try:
        # CORRECCIÓN: Se agrega allowDiskUse=True para la descarga de reportes
        visitas = list(visitas_col.find({"fecha": {"$gte": ini, "$lte": fin}}, {"_id":0}).allow_disk_use(True))
        if not visitas: return "No hay datos", 404
        
        df = pd.DataFrame(visitas)
        for col in ['foto_maquina', 'foto_fachada']:
            if col in df.columns: df.drop(columns=[col], inplace=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        out.seek(0)
        return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=f"Reporte_{ini}.xlsx", as_attachment=True)
    except Exception as e:
        return f"Error al generar Excel: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
