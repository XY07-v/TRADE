import os
import json
from flask import Flask, render_template_string, request
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- DICCIONARIOS FIJOS ---

# Diccionario de Funcionarios
FUNCIONARIOS = ["CINDY JULIETH BOCANEGRA GARZON","CINDY PAOLA CASTRO OROZCO","CRISTIAN CAMILO BAQUERO MURCIA","DIANA MARCELA ERAZO CAICEDO","EDWIN ALEXANDER FORERO VELASQUEZ","ELIECER  ARDILA  LUCIO","ESNEYDI YELEYSI JIMENEZ JIMENEZ","FABIANA ARDILA ORTEGA","GERALDINE RAMIREZ MORENO","HAYDE CAROLINA ORJUELA FORIGUA","JHEINER ALBEIRO AMADO LOZANO","JOHN EDISON MERCHAN SEGURA","JUAN CAMILO PADILLA GRAVIER","KELLY JOHANA BARRERA DE AVILA","KEVIN SANTIAGO MARIN GALEANO","LUZ MARLENE RESTREPO -","MAURICIO LADINO LARGO","MICHAEL GONZALEZ RODRIGUEZ","MONICA MARIA PATIÑO P","MONICA MILENA OTALVARO METAUTE","NESTOR ANDRES CARMONA HUERTAS","RIGOBERTO SIERRA PELAEZ","SHIRLEY YEPES BETANCUR","SIGIFREDO RAMIREZ SARAY","VANESA MONTOYA BUITRAGO","WILSON JAVIER GRIMALDO NAVARRO","YEIMI PAOLA CASTRILLON URREGO","YEISON JOSE GONZALES BERRIO","YOANA ANDREA HINCAPIE ZEA"]

# Maestro de Puntos con Coordenadas de Referencia para validación
DATOS_MAESTROS = [
    {
        "Poc": "Tienda El Porvenir", 
        "BMB": "BMB-1010", 
        "Direccion": "Calle 1 #2-3", 
        "Ubicacion_Ref": "4.6097, -74.0817", # Lat, Lon de referencia
        "Ciudad": "Bogotá", 
        "Departamento": "Cundinamarca"
    },
    {
        "Poc": "Almacen Central", 
        "BMB": "BMB-2020", 
        "Direccion": "Carrera 15 #40-10", 
        "Ubicacion_Ref": "4.6097, -74.0817", 
        "Ciudad": "Medellín", 
        "Departamento": "Antioquia"
    }
]

# --- CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"

def guardar_registro(doc):
    client = MongoClient(MONGO_URI)
    db = client['POWER_TRADE']
    coleccion = db['Visitas_a_POC']
    res = coleccion.insert_one(doc)
    client.close()
    return res

# --- PLANTILLA HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power Trade | Registro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-4">
    <div class="max-w-2xl mx-auto bg-white shadow-xl rounded-2xl overflow-hidden">
        <div class="bg-blue-900 p-4 text-center text-white font-bold uppercase">Registro de Visita</div>

        <form action="/guardar" method="POST" enctype="multipart/form-data" class="p-6 space-y-5">
            
            <div>
                <label class="block text-xs font-bold text-gray-600 uppercase">Funcionario</label>
                <select name="funcionario" class="w-full p-2 border rounded-lg" required>
                    <option value="">Seleccione...</option>
                    {% for f in funcionarios %}<option value="{{ f }}">{{ f }}</option>{% endfor %}
                </select>
            </div>

            <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border">
                <div>
                    <label class="block text-[10px] font-bold text-gray-500 uppercase">Poc</label>
                    <select id="poc_sel" name="poc" onchange="sync('Poc')" class="w-full p-2 border rounded" required>
                        <option value="">-- Seleccione --</option>
                        {% for p in maestro %}<option value="{{ p.Poc }}">{{ p.Poc }}</option>{% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-gray-500 uppercase">BMB</label>
                    <select id="bmb_sel" name="bmb" onchange="sync('BMB')" class="w-full p-2 border rounded" required>
                        <option value="">-- Seleccione --</option>
                        {% for p in maestro %}<option value="{{ p.BMB }}">{{ p.BMB }}</option>{% endfor %}
                    </select>
                </div>
                
                <div class="col-span-2 mt-2 p-2 bg-white border rounded flex justify-between items-center">
                    <span class="text-[10px] font-bold text-blue-700">DISTANCIA A PUNTO:</span>
                    <span id="distancia_txt" class="text-xs font-black text-gray-400 italic font-mono">GPS no cargado</span>
                </div>
                <input type="hidden" id="gps_input" name="ubicacion_gps">
                <input type="hidden" id="distancia_val" name="distancia_metros">
            </div>

            <div>
                <label class="block text-xs font-bold text-gray-600 uppercase">Motivo</label>
                <select name="motivo" class="w-full p-2 border rounded-lg" required>
                    <option value="Ruta">Ruta</option>
                    <option value="Maquina Retirada">Maquina Retirada</option>
                    <option value="Poc Cerrado">Poc Cerrado</option>
                    <option value="Novedad">Novedad</option>
                </select>
            </div>

            <div class="grid grid-cols-2 gap-4 text-center">
                <div class="border-2 border-dashed p-3 rounded-lg">
                    <span class="text-[10px] font-bold block mb-1">FOTO MÁQUINA *</span>
                    <input type="file" name="foto_maquina" accept="image/*" capture="camera" required class="text-[10px]">
                </div>
                <div class="border-2 border-dashed p-3 rounded-lg">
                    <span class="text-[10px] font-bold block mb-1">FOTO FACHADA *</span>
                    <input type="file" name="foto_fachada" accept="image/*" capture="camera" required class="text-[10px]">
                </div>
            </div>

            <div>
                <label class="block text-xs font-bold text-gray-600 uppercase">Observación</label>
                <textarea name="observacion" rows="2" class="w-full p-2 border rounded-lg"></textarea>
            </div>

            <button type="submit" class="w-full bg-blue-900 text-white font-bold py-3 rounded-xl hover:bg-black transition-all">GUARDAR REGISTRO</button>
        </form>
    </div>

    <script>
        const maestro = {{ maestro_json | safe }};
        let uLat, uLon;

        function calcDist(lat1, lon1, lat2, lon2) {
            const R = 6371e3;
            const dLat = (lat2-lat1)*Math.PI/180;
            const dLon = (lon2-lon1)*Math.PI/180;
            const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
            return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
        }

        function sync(tipo) {
            const pVal = document.getElementById('poc_sel').value;
            const bVal = document.getElementById('bmb_sel').value;
            const item = maestro.find(x => tipo === 'Poc' ? x.Poc === pVal : x.BMB === bVal);

            if(item) {
                document.getElementById('poc_sel').value = item.Poc;
                document.getElementById('bmb_sel').value = item.BMB;
                if(uLat && uLon) {
                    const [rLat, rLon] = item.Ubicacion_Ref.split(',').map(Number);
                    const mts = calcDist(uLat, uLon, rLat, rLon);
                    document.getElementById('distancia_txt').innerText = mts + " m";
                    document.getElementById('distancia_val').value = mts;
                    document.getElementById('distancia_txt').className = mts > 100 ? "text-xs font-black text-red-600" : "text-xs font-black text-green-600";
                }
            }
        }

        navigator.geolocation.getCurrentPosition(p => {
            uLat = p.coords.latitude; uLon = p.coords.longitude;
            document.getElementById('gps_input').value = uLat + "," + uLon;
            document.getElementById('distancia_txt').innerText = "GPS OK - Elija Punto";
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, maestro=DATOS_MAESTROS, funcionarios=FUNCIONARIOS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "ubicacion_gps": request.form.get('ubicacion_gps'),
            "desviacion_metros": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "fecha": datetime.now().strftime("%Y-%m-%d") # Solo fecha
        }
        guardar_registro(doc)
        return "<h1>✅ Guardado</h1><a href='/'>Volver</a>"
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
