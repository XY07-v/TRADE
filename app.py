import os, base64
from flask import Flask, render_template_string, request, jsonify, session, redirect
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONEXIÓN A MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
puntos_col = db['Puntos de Venta']
visitas_col = db['Visitas']
usuarios_col = db['Usuarios'] # <--- Aquí buscará el documento que me pasaste

# --- INTERFACES HTML ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Acceso Power Trade</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #F2F2F7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: white; padding: 30px; border-radius: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 90%; max-width: 350px; text-align: center; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #D1D1D6; border-radius: 12px; font-size: 18px; text-align: center; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #007AFF; color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-card">
        <h3 style="margin-top:0">Power Trade BI</h3>
        <p style="color:gray; font-size:14px;">Ingrese su cédula para continuar</p>
        <form action="/login" method="POST">
            <input type="password" name="cedula" placeholder="Cédula" required autocomplete="current-password">
            <button type="submit">Entrar</button>
            {% if error %}<p style="color:#FF3B30; font-size:14px; margin-top:10px;">Usuario no encontrado</p>{% endif %}
        </form>
    </div>
</body>
</html>
"""

# (La interfaz HTML_SISTEMA se mantiene igual a la anterior, solo cambia la lógica de Python abajo)
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Power Trade BI</title>
    <style>
        :root { --blue: #007AFF; --green: #34C759; --bg: #F2F2F7; --gray: #8E8E93; --radius: 14px; }
        * { box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: var(--bg); margin: 0; padding: 10px; }
        .tabs { display: flex; gap: 8px; margin-bottom: 15px; position: sticky; top: 0; background: var(--bg); z-index: 100; padding: 10px 0; }
        .tab-btn { flex: 1; padding: 15px; border: none; border-radius: var(--radius); background: #E5E5EA; font-weight: 700; color: var(--gray); font-size: 15px; }
        .tab-btn.active { background: var(--blue); color: white; }
        .content { display: none; background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .content.active { display: block; }
        input, select, textarea { width: 100%; padding: 16px; margin: 10px 0; border: 1px solid #D1D1D6; border-radius: var(--radius); font-size: 16px; }
        button.primary { width: 100%; padding: 18px; background: var(--blue); color: white; border: none; border-radius: var(--radius); font-weight: bold; font-size: 17px; }
        .img-preview { width: 100%; height: auto; max-height: 200px; object-fit: cover; border-radius: 12px; margin: 10px 0; display: none; }
        .punto-item { padding: 15px; border-bottom: 1px solid #F2F2F7; cursor: pointer; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; padding:5px 10px; font-size:13px; color:gray;">
        <span>Bienvenido: <b>{{ session['nombre'] }}</b></span>
        <a href="/logout" style="color:#FF3B30; text-decoration:none; font-weight:bold;">Cerrar</a>
    </div>

    <div class="tabs">
        <button class="tab-btn active" id="btn-t1" onclick="switchTab('tab-buscar')">🔍 Buscar</button>
        <button class="tab-btn" id="btn-t2" onclick="switchTab('tab-registro')">📝 Reporte</button>
    </div>

    <div id="tab-buscar" class="content active">
        <input type="text" id="q_puntos" placeholder="Escriba Nombre o BMB..." onkeyup="if(event.key === 'Enter') buscarPuntos()">
        <button class="primary" onclick="buscarPuntos()">Consultar Punto</button>
        <div id="res_puntos" style="margin-top:15px;"></div>
    </div>

    <div id="tab-registro" class="content">
        <form id="form-visita">
            <input type="text" id="f_pv" placeholder="Punto de Venta" readonly style="background:#F2F2F7;">
            <input type="text" id="f_bmb" placeholder="BMB" readonly style="background:#F2F2F7;">
            <select id="f_estado">
                <option value="Visita Exitosa">Visita Exitosa</option>
                <option value="Punto Cerrado">Punto Cerrado</option>
                <option value="Maquina Retirada">Maquina Retirada</option>
            </select>
            <input type="file" accept="image/*" capture="camera" onchange="procesarFoto(this, 'p1')">
            <img id="p1" class="img-preview">
            <textarea id="f_obs" placeholder="Observaciones..."></textarea>
            <input type="hidden" id="f_gps">
            <button type="button" class="primary" onclick="enviarVisita()">Guardar Reporte</button>
        </form>
    </div>

    <script>
        function switchTab(id) {
            document.querySelectorAll('.content, .tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            document.getElementById(id === 'tab-buscar' ? 'btn-t1' : 'btn-t2').classList.add('active');
        }

        function procesarFoto(input, idDestino) {
            const file = input.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = function (e) {
                const img = new Image();
                img.src = e.target.result;
                img.onload = function () {
                    const canvas = document.createElement('canvas');
                    const scale = 800 / img.width;
                    canvas.width = 800; canvas.height = img.height * scale;
                    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                    const preview = document.getElementById(idDestino);
                    preview.src = canvas.toDataURL('image/jpeg', 0.5);
                    preview.style.display = 'block';
                }
            }
        }

        async function buscarPuntos() {
            const q = document.getElementById('q_puntos').value;
            const resDiv = document.getElementById('res_puntos');
            resDiv.innerHTML = "Buscando...";
            const r = await fetch('/api/buscar?q=' + q);
            const data = await r.json();
            resDiv.innerHTML = "";
            data.forEach(p => {
                const div = document.createElement('div');
                div.className = "punto-item";
                div.innerHTML = `<strong>${p['Punto de Venta']}</strong><br><small>BMB: ${p['BMB']}</small>`;
                div.onclick = () => {
                    document.getElementById('f_pv').value = p['Punto de Venta'];
                    document.getElementById('f_bmb').value = p['BMB'];
                    switchTab('tab-registro');
                };
                resDiv.appendChild(div);
            });
        }

        async function enviarVisita() {
            const payload = {
                pv: document.getElementById('f_pv').value,
                bmb: document.getElementById('f_bmb').value,
                estado: document.getElementById('f_estado').value,
                f1: document.getElementById('p1').src,
                obs: document.getElementById('f_obs').value,
                gps: document.getElementById('f_gps').value
            };
            const r = await fetch('/api/guardar_visita', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if(r.ok) { alert("¡Reporte Guardado!"); location.reload(); }
        }

        navigator.geolocation.getCurrentPosition(p => {
            document.getElementById('f_gps').value = p.coords.latitude + ',' + p.coords.longitude;
        });
    </script>
</body>
</html>
"""

# --- RUTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form.get('cedula').strip()
        # Busca por el campo 'password' de tu documento
        user = usuarios_col.find_one({"password": {"$in": [cedula, int(cedula) if cedula.isdigit() else ""]}})
        
        if user:
            session['user'] = user['usuario']
            session['nombre'] = user['nombre_completo']
            return redirect('/')
        return render_template_string(HTML_LOGIN, error=True)
    return render_template_string(HTML_LOGIN)

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    return render_template_string(HTML_SISTEMA)

@app.route('/api/buscar')
def api_buscar():
    q = request.args.get('q', '').strip()
    # Ajustado para buscar por Punto de Venta o BMB
    filtro = {"$or": [{"Punto de Venta": {"$regex": q, "$options": "i"}}, {"BMB": {"$regex": q, "$options": "i"}}]}
    puntos = list(puntos_col.find(filtro, {"_id":0, "Punto de Venta":1, "BMB":1}).limit(10))
    return jsonify(puntos)

@app.route('/api/guardar_visita', methods=['POST'])
def api_visita():
    d = request.json
    visitas_col.insert_one({
        "usuario": session['user'],
        "nombre_operador": session['nombre'],
        "pv": d['pv'], 
        "bmb": d['bmb'], 
        "motivo": d['estado'],
        "obs": d['obs'],
        "foto_equipo": d['f1'], 
        "gps": d['gps'],
        "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    return jsonify({"status": "ok"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
