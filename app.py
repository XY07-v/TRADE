import os
from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- CONFIGURACIÓN DE DATOS ESTÁNDAR ---
PREGUNTAS_ESTANDAR = {
    "infraestructura": "¿El punto cuenta con el mobiliario completo?",
    "inventario": "¿Se encuentra el stock mínimo requerido?",
    "visibilidad": "¿El material POP está ubicado correctamente?",
    "servicio": "¿El personal sigue el protocolo de atención?",
    "limpieza": "¿El área de exhibición está limpia y ordenada?"
}

PUNTOS_POR_CIUDAD = {
    "Bogotá": ["Punto Norte 1", "Punto Centro 2", "Punto Sur 3"],
    "Medellín": ["Punto Poblado", "Punto Laureles"],
    "Cali": ["Punto Chipichape", "Punto Unicentro"],
    "Barranquilla": ["Punto Buenavista", "Punto Prado"]
}

# --- LÓGICA DE BASE DE DATOS (CONEXIÓN BAJO DEMANDA) ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"

def guardar_en_db(datos):
    """Se conecta solo al momento de insertar"""
    client = MongoClient(MONGO_URI)
    db = client['POWER_TRADE']
    coleccion = db['Visitas_a_POC']
    resultado = coleccion.insert_one(datos)
    client.close()
    return resultado.inserted_id

# --- PLANTILLA HTML (FRONTEND) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro de Visitas POC</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen p-8">
    <div class="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-md">
        <h2 class="text-2xl font-bold mb-6 text-gray-800 border-b pb-2">Registro de Visita a POC</h2>
        
        <form action="/guardar" method="POST" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Ciudad</label>
                    <select id="ciudad" name="ciudad" onchange="actualizarPuntos()" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 bg-gray-50" required>
                        <option value="">Seleccione...</option>
                        {% for ciudad in ciudades %}
                        <option value="{{ ciudad }}">{{ ciudad }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Punto de Venta</label>
                    <select id="punto" name="punto" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 bg-gray-50" required>
                        <option value="">Primero elija ciudad</option>
                    </select>
                </div>
            </div>

            <hr>

            <div class="space-y-4">
                <h3 class="text-lg font-semibold text-blue-600">Evaluación Estándar</h3>
                {% for key, pregunta in preguntas.items() %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <label class="text-gray-700 text-sm w-2/3">{{ pregunta }}</label>
                    <div class="flex gap-4">
                        <label class="flex items-center space-x-1 cursor-pointer">
                            <input type="radio" name="{{ key }}" value="-1" class="text-green-500" required>
                            <span class="text-xs">Chulo (OK)</span>
                        </label>
                        <label class="flex items-center space-x-1 cursor-pointer">
                            <input type="radio" name="{{ key }}" value="" class="text-red-500">
                            <span class="text-xs">X (Déficit)</span>
                        </label>
                    </div>
                </div>
                {% endfor %}
            </div>

            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition duration-200">
                Guardar Registro
            </button>
        </form>
    </div>

    <script>
        const dataPuntos = {{ puntos_json | safe }};
        
        function actualizarPuntos() {
            const ciudadSel = document.getElementById('ciudad').value;
            const puntoSelect = document.getElementById('punto');
            puntoSelect.innerHTML = '<option value="">Seleccione un punto...</option>';
            
            if(ciudadSel && dataPuntos[ciudadSel]) {
                dataPuntos[ciudadSel].forEach(punto => {
                    const opt = document.createElement('option');
                    opt.value = punto;
                    opt.innerHTML = punto;
                    puntoSelect.appendChild(opt);
                });
            }
        }
    </script>
</body>
</html>
"""

# --- RUTAS ---
@app.route('/')
def index():
    import json
    return render_template_string(
        HTML_TEMPLATE, 
        ciudades=PUNTOS_POR_CIUDAD.keys(), 
        preguntas=PREGUNTAS_ESTANDAR,
        puntos_json=json.dumps(PUNTOS_POR_CIUDAD)
    )

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        # Construir el documento para MongoDB
        registro = {
            "ciudad": request.form.get('ciudad'),
            "punto": request.form.get('punto'),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "respuestas": {}
        }
        
        # Iterar sobre las preguntas del diccionario para recolectar respuestas
        for key in PREGUNTAS_ESTANDAR.keys():
            registro["respuestas"][key] = request.form.get(key)

        # Guardar solo al enviar
        guardar_en_db(registro)
        
        return "<h1>Registro guardado con éxito en POWER_TRADE.Visitas_a_POC</h1><a href='/'>Volver</a>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

if __name__ == '__main__':
    # Usar el puerto de Render si está disponible
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
