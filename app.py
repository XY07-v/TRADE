import os
import json
from flask import Flask, render_template_string, request
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "power_trade_ultra_2026"

# --- 1. DICCIONARIO DE FUNCIONARIOS ---
FUNCIONARIOS = sorted([
    "CINDY JULIETH BOCANEGRA GARZON", "CINDY PAOLA CASTRO OROZCO", "CRISTIAN CAMILO BAQUERO MURCIA",
    "DIANA MARCELA ERAZO CAICEDO", "EDWIN ALEXANDER FORERO VELASQUEZ", "ELIECER ARDILA LUCIO",
    "ESNEYDI YELEYSI JIMENEZ JIMENEZ", "FABIANA ARDILA ORTEGA", "GERALDINE RAMIREZ MORENO",
    "HAYDE CAROLINA ORJUELA FORIGUA", "JHEINER ALBEIRO AMADO LOZANO", "JOHN EDISON MERCHAN SEGURA",
    "JUAN CAMILO PADILLA GRAVIER", "KELLY JOHANA BARRERA DE AVILA", "KEVIN SANTIAGO MARIN GALEANO",
    "LUZ MARLENE RESTREPO -", "MAURICIO LADINO LARGO", "MICHAEL GONZALEZ RODRIGUEZ",
    "MONICA MARIA PATIÑO P", "MONICA MILENA OTALVARO METAUTE", "NESTOR ANDRES CARMONA HUERTAS",
    "RIGOBERTO SIERRA PELAEZ", "SHIRLEY YEPES BETANCUR", "SIGIFREDO RAMIREZ SARAY",
    "VANESA MONTOYA BUITRAGO", "WILSON JAVIER GRIMALDO NAVARRO", "YEIMI PAOLA CASTRILLON URREGO",
    "YEISON JOSE GONZALES BERRIO", "YOANA ANDREA HINCAPIE ZEA"
])

# --- 2. MAESTRO DE PUNTOS (ESTILO TABLA: MÁS FÁCIL DE LLENAR) ---
# Orden de las columnas: [Nombre Poc, Código BMB, Dirección, Coordenadas Ref, Ciudad, Departamento]
TABLA_PUNTOS = [
    ["Tienda El Porvenir", "BMB-1010", "Calle 1 #2-3", "4.6097, -74.0817", "Bogotá", "Cundinamarca"],
    ["Almacen Central", "BMB-2020", "Carrera 15 #40-10", "6.2442, -75.5812", "Medellín", "Antioquia"],
    ["Punto Rapido 24/7", "BMB-3030", "Av 6 #10-20", "3.4516, -76.5320", "Cali", "Valle del Cauca"],
    # Para agregar más, solo añade una línea igual a las anteriores aquí abajo:
]

# Conversión automática a diccionario eficiente
DATOS_MAESTROS = [
    {
        "Poc": f[0], "BMB": f[1], "Direccion": f[2], 
        "Ubicacion_Ref": f[3], "Ciudad": f[4], "Departamento": f[5]
    } for f in TABLA_PUNTOS
]

# --- 3. CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"

def guardar_registro(doc):
    with MongoClient(MONGO_URI) as client:
        db = client['POWER_TRADE']
        coleccion = db['Visitas_a_POC']
        return coleccion.insert_one(doc)

# --- 4. PLANTILLA HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power Trade | Registro de Visita</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-4">
    <div class="max-w-2xl mx-auto bg-white shadow-2xl rounded-2xl overflow-hidden">
        <div class="bg-blue-900 p-5 text-center text-white font-bold uppercase tracking-widest">
            Registro de Visita a POC
        </div>

        <form action="/guardar" method="POST" enctype="multipart/form-data" class="p-6 space-y-6">
            
            <div>
                <label class="block text-xs font-black text-gray-600 uppercase mb-1">Funcionario</label>
                <select name="funcionario" class="w-full p-3 border-2 rounded-xl bg-white" required>
                    <option value="">Seleccione su nombre...</option>
                    {% for f in funcionarios %}<option value="{{ f }}">{{ f }}</option>{% endfor %}
                </select>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-blue-50 p-5 rounded-2xl border-2 border-blue-100">
                <div>
                    <label class="block text-[10px] font-bold text-blue-700 uppercase">Nombre Poc</label>
                    <select id="poc_sel" name="poc" onchange="sync('Poc')" class="w-full p-2 border rounded-lg" required>
                        <option value="">-- Seleccione --</option>
                        {% for p in maestro %}<option value="{{ p.Poc }}">{{ p.Poc }}</option>{% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-blue-700 uppercase">Código BMB</label>
                    <select id="bmb_sel" name="bmb" onchange="sync('BMB')" class="w-full p-2 border rounded-lg" required>
                        <option value="">-- Seleccione --</option>
                        {% for p in maestro %}<option value="{{ p.BMB }}">{{ p.BMB }}</option>{% endfor %}
                    </select>
                </div>
                
                <div class="md:col-span-2 mt-2 p-3 bg-white border rounded-xl flex justify-between items-center shadow-sm">
                    <span class="text-[10px] font-black text-gray-500 uppercase">Distancia al punto:</span>
                    <span id="distancia_txt" class="text-sm font-black text-gray-400 italic">Esperando GPS...</span>
                </div>
                <input type="hidden" id="gps_input" name="ubicacion_gps">
                <input type="hidden" id="distancia_val" name="distancia_metros">
            </div>

            <div>
                <label class="block text-xs font-black text-gray-600 uppercase mb-1">Motivo</label>
                <select name="motivo" class="w-full p-3 border-2 rounded-xl" required>
                    <option value="Ruta">Ruta</option>
                    <option value="Maquina Retirada">Maquina Retirada</option>
                    <option value="Poc Cerrado">Poc Cerrado</option>
                    <option value="Novedad">Novedad</option>
                </select>
            </div>

            <div class="grid grid-cols-2 gap-4 text-center">
                <div class="border-2 border-dashed border-gray-300 p-4 rounded-2xl bg-gray-50">
                    <span class="text-[10px] font-bold block mb-2 text-blue-900 uppercase">Foto Máquina *</span>
                    <input type="file" name="foto_maquina" accept="image/*" capture="camera" required class="text-[10px] w-full">
                </div>
                <div class="border-2 border-dashed border-gray-300 p-4 rounded-2xl bg-gray-50">
                    <span class="text-[10px] font-bold block mb-2 text-blue-900 uppercase">Foto Fachada *</span>
                    <input type="file" name="foto_fachada" accept="image/*" capture="camera" required class="text-[10px] w-full">
                </div>
            </div>

            <div>
                <label class="block text-xs font-black text-gray-600 uppercase mb-1">Observación</label>
                <textarea name="observacion" rows="2" class="w-full p-3 border-2 rounded-xl focus:border-blue-500 outline-none" placeholder="Escriba aquí..."></textarea>
            </div>

            <button type="submit" class="w-full bg-blue-900 text-white font-black py-4 rounded-2xl shadow-lg hover:bg-black transition-all transform active:scale-95 uppercase tracking-widest">
                Guardar Registro
            </button>
        </form>
    </div>

    <script>
        const maestro = {{ maestro_json | safe }};
        let uLat, uLon;

        // Fórmula Haversine para metros
        function calcDist(lat1, lon1, lat2, lon2) {
            const R = 6371000;
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
                    const txt = document.getElementById('distancia_txt');
                    txt.innerText = mts + " metros";
                    document.getElementById('distancia_val').value = mts;
                    txt.className = mts > 150 ? "text-sm font-black text-red-600" : "text-sm font-black text-green-600";
                }
            }
        }

        navigator.geolocation.getCurrentPosition(p => {
            uLat = p.coords.latitude; uLon = p.coords.longitude;
            document.getElementById('gps_input').value = uLat + "," + uLon;
            document.getElementById('distancia_txt').innerText = "GPS OK - Seleccione Punto";
        });
    </script>
</body>
</html>
"""

# --- 5. RUTAS ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                 maestro=DATOS_MAESTROS, 
                                 funcionarios=FUNCIONARIOS, 
                                 maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/guardar', methods=['POST'])
def guardar():
    try:
        # Documento final para MongoDB con fecha limpia
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "ubicacion_gps": request.form.get('ubicacion_gps'),
            "desviacion_metros": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "fecha": datetime.now().strftime("%Y-%m-%d") # Guardar solo fecha
        }
        guardar_registro(doc)
        return """
        <body style="font-family:sans-serif; text-align:center; padding-top:50px; background:#f3f4f6;">
            <div style="background:white; display:inline-block; padding:30px; border-radius:20px; shadow:xl;">
                <h1 style="color:#1e3a8a;">✅ REGISTRO EXITOSO</h1>
                <p>La información se guardó correctamente.</p>
                <br>
                <a href="/" style="background:#1e3a8a; color:white; padding:10px 20px; border-radius:10px; text-decoration:none; font-weight:bold;">NUEVO REGISTRO</a>
            </div>
        </body>
        """
    except Exception as e:
        return f"<h1>Error al guardar: {e}</h1>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
