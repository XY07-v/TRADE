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
usuarios_col = db['usuarios'] # Ajustado según tu imagen (minúsculas)

# --- HTML LOGIN ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { font-family: -apple-system, sans-serif; background: #F2F2F7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 90%; max-width: 320px; text-align: center; }
        input { width: 100%; padding: 15px; margin: 15px 0; border: 1px solid #DDD; border-radius: 10px; font-size: 16px; text-align: center; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #007AFF; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h3>Power Trade</h3>
        <form method="POST">
            <input type="password" name="cedula" placeholder="Cédula" required>
            <button type="submit">Entrar</button>
            {% if error %}<p style="color:red; font-size:12px; margin-top:10px;">Acceso denegado</p>{% endif %}
        </form>
    </div>
</body>
</html>
"""

# --- RUTAS DE ACCESO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula_ingresada = request.form.get('cedula').strip()
        
        # BUSQUEDA FLEXIBLE: Buscamos el string exacto que aparece en tu imagen
        # Probamos como String y como Entero por si acaso
        user = usuarios_col.find_one({
            "$or": [
                {"password": cedula_ingresada},
                {"password": int(cedula_ingresada) if cedula_ingresada.isdigit() else None}
            ]
        })

        if user:
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['user'] = user['usuario']
            session['nombre'] = user['nombre_completo']
            print(f"DEBUG: Login exitoso para {user['usuario']}")
            return redirect('/')
        else:
            print(f"DEBUG: Intento fallido con cedula: {cedula_ingresada}")
            return render_template_string(HTML_LOGIN, error=True)
            
    return render_template_string(HTML_LOGIN)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    # Aquí iría tu HTML_SISTEMA (el de los tabs)
    return f"Bienvenido {session['nombre']} <br> <a href='/logout'>Salir</a>"

# (Las APIs de buscar y guardar se mantienen igual que el código anterior)

if __name__ == '__main__':
    # Usamos puerto 5000 para local o el que asigne el servidor
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
