import os, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONEXIÓN ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']

# --- HTML UNIFICADO (Dashboard Dinámico) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --blue: #007AFF; --bg: #F2F2F7; --red: #FF3B30; --green: #34C759; }
        body { font-family: -apple-system, sans-serif; background: var(--bg); margin: 0; padding-bottom: 20px; }
        .nav { background: white; padding: 15px; border-bottom: 1px solid #ddd; font-weight: bold; display: flex; justify-content: space-between; }
        .container { padding: 15px; }
        .card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .btn-blue { background: var(--blue); color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: 600; cursor: pointer; }
        .tabs { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #ddd; background: white; text-align: center; cursor: pointer; }
        .tab.active { background: var(--blue); color: white; border-color: var(--blue); }
        input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        .scroll { overflow-x: auto; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th, td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8f9fa; color: #666; }
    </style>
</head>
<body>
    <div class="nav"><span>Power Trade 2026</span> <a href="/logout" style="color:var(--red); text-decoration:none;">Salir</a></div>
    
    <div class="container">
        <div class="tabs">
            <div id="t1" class="tab active" onclick="switchTab('puntos')">🏢 Puntos</div>
            <div id="t2" class="tab" onclick="switchTab('visitas')">📊 Visitas</div>
        </div>

        <div class="card">
            <input type="text" id="q" placeholder="Buscar por Nombre o BMB..." onkeyup="consultar()">
            <div id="extra_form" style="display:none; margin-top:10px;">
                <input type="text" id="new_bmb" placeholder="Nuevo BMB">
                <input type="text" id="new_nom" placeholder="Nuevo Nombre">
                <button class="btn-blue" style="background:var(--green);" onclick="inyectarPunto()">Inyectar Punto</button>
            </div>
            <button id="btn_toggle" class="btn-blue" style="margin-top:5px; background:none; color:var(--blue); border:1px solid var(--blue);" onclick="toggleExtra()">+ Crear Nuevo Punto</button>
        </div>

        <div class="card scroll">
            <table id="tabla">
                <thead id="head"></thead>
                <tbody id="body"></tbody>
            </table>
        </div>
    </div>

    <script>
        let tabActual = 'puntos';

        function switchTab(t) {
            tabActual = t;
            document.getElementById('t1').className = t == 'puntos' ? 'tab active' : 'tab';
            document.getElementById('t2').className = t == 'visitas' ? 'tab active' : 'tab';
            consultar();
        }

        function toggleExtra() {
            const f = document.getElementById('extra_form');
            f.style.display = f.style.display == 'none' ? 'block' : 'none';
        }

        async function consultar() {
            const q = document.getElementById('q').value;
            const r = await fetch(`/api/datos?col=${tabActual}&q=${q}`);
            const data = await r.json();
            const head = document.getElementById('head');
            const body = document.getElementById('body');
            head.innerHTML = ""; body.innerHTML = "";

            if(data.length > 0) {
                let cols = Object.keys(data[0]).filter(k => k !== '_id');
                let hRow = "<tr>";
                cols.forEach(c => hRow += `<th>${c}</th>`);
                head.innerHTML = hRow + "</tr>";

                data.forEach(item => {
                    let bRow = "<tr>";
                    cols.forEach(c => bRow += `<td>${item[c] || ''}</td>`);
                    body.innerHTML += bRow + "</tr>";
                });
            } else {
                body.innerHTML = "<tr><td>No hay datos</td></tr>";
            }
        }

        async function inyectarPunto() {
            const bmb = document.getElementById('new_bmb').value;
            const nom = document.getElementById('new_nom').value;
            if(!bmb || !nom) return alert("Llena los campos");
            
            await fetch('/api/inyectar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({bmb, nom})
            });
            alert("Punto Inyectado");
            location.reload();
        }

        window.onload = consultar;
    </script>
</body>
</html>
"""

# --- RUTAS ---
@app.route('/')
def index():
    if 'usuario' not in session: return redirect('/login')
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['usuario'] = "Andres Vanegas"
        return redirect('/')
    return '<h2>Power Trade Login</h2><form method="post"><input name="cc" placeholder="CC"><button>Entrar</button></form>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/datos')
def get_datos():
    col = request.args.get('col')
    q = request.args.get('q', '').strip()
    query = {"$or": [{"Nombre de punto": {"$regex": q, "$options": "i"}}, {"BMB": {"$regex": q, "$options": "i"}}]} if q else {}
    
    if col == 'puntos':
        res = list(puntos_col.find(query).limit(50))
    else:
        # PROTECCIÓN ANTI-ERROR: Excluimos las fotos para no saturar la memoria
        res = list(visitas_col.find(query, {"foto_maquina": 0, "foto_fachada": 0}).sort("fecha", -1).limit(50))
    
    for d in res: d['_id'] = str(d['_id'])
    return jsonify(res)

@app.route('/api/inyectar', methods=['POST'])
def inyectar():
    data = request.json
    puntos_col.insert_one({
        "BMB": data['bmb'],
        "Nombre de punto": data['nom'],
        "Ubicacion": "0,0",
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d")
    })
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
