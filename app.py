import os, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONEXIÓN ---
client = MongoClient("mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0")
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']
usuarios_col = db['usuarios']

# --- INTERFAZ ÚNICA (CSS & HTML) ---
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root { --blue: #007AFF; --bg: #F2F2F7; --radius: 14px; }
        body { font-family: -apple-system, sans-serif; background: var(--bg); margin: 0; padding: 10px; }
        .tabs { display: flex; gap: 8px; position: sticky; top: 0; background: var(--bg); padding: 10px 0; z-index: 100; }
        .tab-btn { flex: 1; padding: 15px; border: none; border-radius: var(--radius); background: #E5E5EA; font-weight: bold; color: #8E8E93; }
        .tab-btn.active { background: var(--blue); color: white; }
        .card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: none; }
        .card.active { display: block; }
        input { width: 100%; padding: 16px; margin: 10px 0; border: 1px solid #D1D1D6; border-radius: var(--radius); font-size: 16px; box-sizing: border-box; }
        button.primary { width: 100%; padding: 18px; background: var(--blue); color: white; border: none; border-radius: var(--radius); font-weight: bold; font-size: 17px; margin-top: 10px; }
        .item-res { padding: 15px; border-bottom: 1px solid #EEE; cursor: pointer; background: #FFF; border-radius: 10px; margin-bottom: 5px; }
        .item-res:active { background: #F9F9F9; }
        .tag { font-size: 10px; padding: 3px 7px; background: #E5E5EA; border-radius: 5px; color: #666; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; padding:5px; font-size:12px; color:gray;">
        <span>Operador: <b>{{ session['nombre'] }}</b></span>
        <a href="/logout" style="color:#FF3B30; text-decoration:none;">Cerrar Sesión</a>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-puntos', this)">🏢 Puntos</button>
        <button class="tab-btn" onclick="switchTab('tab-visitas', this)">📊 Historial</button>
    </div>

    <div id="tab-puntos" class="card active">
        <input type="text" id="q_puntos" placeholder="Buscar BMB o Nombre..." onkeyup="if(event.key === 'Enter') buscarPuntos()">
        <button class="primary" onclick="buscarPuntos()">Consultar Punto</button>
        <div id="res_puntos" style="margin-top:15px;"></div>
    </div>

    <div id="tab-visitas" class="card">
        <input type="text" id="q_visitas" placeholder="BMB o Usuario de visita..." onkeyup="if(event.key === 'Enter') buscarVisitas()">
        <button class="primary" style="background:#5856D6" onclick="buscarVisitas()">Consultar Historial</button>
        <div id="res_visitas" style="margin-top:15px;"></div>
    </div>

    <script>
        function switchTab(id, btn) {
            document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            btn.classList.add('active');
        }

        async function buscarPuntos() {
            const q = document.getElementById('q_puntos').value;
            if(q.length < 2) return;
            const resDiv = document.getElementById('res_puntos');
            resDiv.innerHTML = "Cargando...";
            
            const r = await fetch('/api/buscar_puntos?q=' + q);
            const data = await r.json();
            resDiv.innerHTML = "";
            
            data.forEach(p => {
                const div = document.createElement('div');
                div.className = "item-res";
                div.innerHTML = `<b>${p['Nombre de punto']}</b><br>
                                 <span class="tag">BMB: ${p['BMB']}</span> 
                                 <span class="tag">${p['Ciudad']}</span><br>
                                 <small style="color:gray">${p['Direccion']}</small>`;
                div.onclick = () => alert("Aquí abrirías el formulario para: " + p['Nombre de punto']);
                resDiv.appendChild(div);
            });
        }

        async function buscarVisitas() {
            const q = document.getElementById('q_visitas').value;
            const resDiv = document.getElementById('res_visitas');
            resDiv.innerHTML = "Consultando...";
            
            const r = await fetch('/api/buscar_visitas?q=' + q);
            const data = await r.json();
            resDiv.innerHTML = "";
            
            data.forEach(v => {
                const div = document.createElement('div');
                div.className = "item-res";
                div.innerHTML = `<b>${v.pv || 'Punto'}</b> - <small>${v.fecha}</small><br>
                                 <span class="tag" style="background:#34C759; color:white">${v.motivo}</span>
                                 <span class="tag">Por: ${v.usuario}</span>`;
                resDiv.appendChild(div);
            });
        }
    </script>
</body>
</html>
"""

# --- RUTAS DE CONSULTA INTELIGENTE ---

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    return render_template_string(HTML_SISTEMA)

@app.route('/api/buscar_puntos')
def api_puntos():
    q = request.args.get('q', '').strip()
    # Buscamos por BMB (exacto o inicio) o Nombre (contiene)
    filtro = {"$or": [
        {"BMB": {"$regex": f"^{q}", "$options": "i"}},
        {"Nombre de punto": {"$regex": q, "$options": "i"}}
    ]}
    # Traemos solo los campos necesarios (Proyección)
    puntos = list(puntos_col.find(filtro, {
        "_id": 0, "Nombre de punto": 1, "BMB": 1, "Direccion": 1, "Ciudad": 1
    }).limit(20))
    return jsonify(puntos)

@app.route('/api/buscar_visitas')
def api_visitas():
    q = request.args.get('q', '').strip()
    filtro = {}
    if q:
        filtro = {"$or": [
            {"bmb": q},
            {"usuario": {"$regex": q, "$options": "i"}},
            {"pv": {"$regex": q, "$options": "i"}}
        ]}
    
    # CRÍTICO: Excluimos f_bmb y f_fachada para que la consulta no pese megas
    visitas = list(visitas_col.find(filtro, {
        "foto_equipo": 0, "f_bmb": 0, "f_fachada": 0, "_id": 0
    }).sort("fecha", -1).limit(20))
    
    return jsonify(visitas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form.get('cedula').strip()
        user = usuarios_col.find_one({"password": {"$in": [cedula, int(cedula) if cedula.isdigit() else ""]}})
        if user:
            session['user'] = user['usuario']
            session['nombre'] = user['nombre_completo']
            return redirect('/')
    return render_template_string("... (tu HTML_LOGIN) ...")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
