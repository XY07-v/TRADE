import os
import json
from flask import Flask, render_template_string, request
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- 1. DICCIONARIOS FIJOS ---

# Diccionario con la estructura de la visita solicitada
VISITA_A_POC_DICT = {
    "Configuracion": {
        "Poc": "Nombre del Punto de Venta",
        "BMB": "Código Único BMB",
        "Ubicacion": "Coordenadas GPS (Automático)",
        "Motivo": ["Venta", "Mantenimiento", "Cobro", "Check-in Rutina", "Otro"],
        "Foto_Maquina": "Registro fotográfico obligatorio",
        "Foto_Fachada": "Registro fotográfico obligatorio",
        "Observacion": "Campo de texto abierto"
    }
}

# Maestro de Datos para el autocompletado cruzado
DATOS_MAESTROS = [
    {
        "Poc": "Tienda La Bendicion", 
        "BMB": "BMB-1010", 
        "Direccion": "Calle 1 #2-3", 
        "Ubicacion_Ref": "Sur", 
        "Ciudad": "Bogotá", 
        "Departamento": "Cundinamarca"
    },
    {
        "Poc": "Almacen Central", 
        "BMB": "BMB-2020", 
        "Direccion": "Carrera 15 #40-10", 
        "Ubicacion_Ref": "Norte", 
        "Ciudad": "Medellín", 
        "Departamento": "Antioquia"
    },
    {
        "Poc": "Punto Rapido 24/7", 
        "BMB": "BMB-3030", 
        "Direccion": "Av 6 #10-20", 
        "Ubicacion_Ref": "Oeste", 
        "Ciudad": "Cali", 
        "Departamento": "Valle del Cauca"
    }
]

# --- 2. CONEXIÓN BAJO DEMANDA ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"

def conectar_y_guardar(doc):
    client = MongoClient(MONGO_URI)
    db = client['POWER_TRADE']
    # Se guarda en la colección Visitas_a_POC
    coleccion = db['Visitas_a_POC']
    resultado = coleccion.insert_one(doc)
    client.close()
    return resultado

# --- 3. PLANTILLA HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power Trade | Visita POC</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 p-4 md:p-10">
    <div class="max-w-3xl mx-auto bg-white shadow-2xl rounded-3xl overflow-hidden">
        <div class="bg-blue-900 p-6 text-center">
            <h1 class="text-white text-2xl font-black uppercase tracking-tighter">Visita a POC</h1>
        </div>

        <form action="/guardar" method="POST" enctype="multipart/form-data" class="p-8 space-y-6">
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50 p-6 rounded-2xl border border-gray-200">
                <div class="space-y-2">
                    <label class="text-xs font-black text-gray-500 uppercase">Seleccionar POC</label>
                    <select id="poc_sel" name="poc" onchange="sincronizar('Poc')" class="w-full p-3 border-2 rounded-xl bg-white" required>
                        <option value="">-- Nombre POC --</option>
                        {% for p in maestro %}<option value="{{ p.Poc }}">{{ p.Poc }}</option>{% endfor %}
                    </select>
                </div>
                <div class="space-y-2">
                    <label class="text-xs font-black text-gray-500 uppercase">Seleccionar BMB</label>
                    <select id="bmb_sel" name="bmb" onchange="sincronizar('BMB')" class="w-full p-3 border-2 rounded-xl bg-white" required>
                        <option value="">-- Código BMB --</option>
                        {% for p in maestro %}<option value="{{ p.BMB }}">{{ p.BMB }}</option>{% endfor %}
                    </select>
                </div>
                
                <div class="md:col-span-2 text-[10px] grid grid-cols-2 gap-4 font-bold text-blue-800 uppercase italic">
                    <p>📍 Ciudad: <span id="view_ciudad" class="text-gray-900">-</span></p>
                    <p>🏢 Depto: <span id="view_depto" class="text-gray-900">-</span></p>
                    <p>🏠 Dirección: <span id="view_dir" class="text-gray-900 text-[9px]">-</span></p>
                    <p>🗺️ Ubicación: <span id="view_ubi" class="text-gray-900">-</span></p>
                </div>
                
                <input type="hidden" id="gps_coords" name="ubicacion_gps">
            </div>

            <div class="space-y-2">
                <label class="block text-sm font-black text-gray-700 uppercase italic">Motivo de Visita</label>
                <select name="motivo" class="w-full p-3 border-2 rounded-xl" required>
                    {% for m in motivos %}<option value="{{ m }}">{{ m }}</option>{% endfor %}
                </select>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-4 border-2 border-dashed rounded-2xl text-center">
                    <span class="text-xs font-black text-blue-900 block mb-2 uppercase">Foto de la Máquina *</span>
                    <input type="file" name="foto_maquina" accept="image/*" capture="camera" required class="text-[10px]">
                </div>
                <div class="p-4 border-2 border-dashed rounded-2xl text-center">
                    <span class="text-xs font-black text-blue-900 block mb-2 uppercase">Foto de la Fachada *</span>
                    <input type="file" name="foto_fachada" accept="image/*" capture="camera" required class="text-[10px]">
                </div>
            </div>

            <div class="space-y-2">
                <label class="block text-sm font-black text-gray-700 uppercase italic">Observación</label>
                <textarea name="observacion" rows="3" class="w-full p-4 border-2 rounded-2xl" placeholder="Escriba aquí sus observaciones..."></textarea>
            </div>

            <button type="submit" class="w-full bg-blue-900 text-white font-black py-4 rounded-2xl shadow-xl hover:bg-black transition-all">
                REGISTRAR VISITA EN MONGODB
            </button>
        </form>
    </div>

    <script>
        const maestro = {{ maestro_json | safe }};

        // Lógica para que BMB y POC se completen entre sí
        function sincronizar(origen) {
            const valPoc = document.getElementById('poc_sel').value;
            const valBmb = document.getElementById('bmb_sel').value;
            
            const item = maestro.find(x => origen === 'Poc' ? x.Poc === valPoc : x.BMB === valBmb);

            if(item) {
                document.getElementById('poc_sel').value = item.Poc;
                document.getElementById('bmb_sel').value = item.BMB;
                document.getElementById('view_ciudad').innerText = item.Ciudad;
                document.getElementById('view_depto').innerText = item.Departamento;
                document.getElementById('view_dir').innerText = item.Direccion;
                document.getElementById('view_ubi').innerText = item.Ubicacion_Ref;
            }
        }

        // Obtener ubicación GPS al abrir el formulario
        window.onload = function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(pos) {
                    document.getElementById('gps_coords').value = pos.coords.latitude + ", " + pos.coords.longitude;
                });
            }
        };
    </script>
</body>
</html>
"""

# --- 4. RUTAS FLASK ---

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        maestro=DATOS_MAESTROS,
        motivos=VISITA_A_POC_DICT["Configuracion"]["Motivo"],
        maestro_json=json.dumps(DATOS_MAESTROS)
    )

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        # Estructura del documento para MongoDB basado en el diccionario fijo
        registro = {
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "ubicacion_gps": request.form.get('ubicacion_gps'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "timestamp": datetime.now()
        }

        conectar_y_guardar(registro)
        return "<h1>✅ VISITA REGISTRADA</h1><a href='/'>Regresar al formulario</a>"
    except Exception as e:
        return f"<h1>❌ ERROR</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
