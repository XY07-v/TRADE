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

# --- 2. MAESTRO DE PUNTOS ---
TABLA_PUNTOS = [
    ["Tienda El Porvenir", "BMB-1010", "Calle 1 #2-3", "4.6097, -74.0817", "Bogotá", "Cundinamarca"],
    ["Almacen Central", "BMB-2020", "Carrera 15 #40-10", "6.2442, -75.5812", "Medellín", "Antioquia"],
]

DATOS_MAESTROS = [
    {"Poc": f[0], "BMB": f[1], "Direccion": f[2], "Ubicacion_Ref": f[3], "Ciudad": f[4], "Departamento": f[5]} 
    for f in TABLA_PUNTOS
]

# --- 3. CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"

def guardar_registro(doc):
    with MongoClient(MONGO_URI) as client:
        db = client['POWER_TRADE']
        coleccion = db['Visitas_a_POC']
        return coleccion.insert_one(doc)

# --- 4. PLANTILLA HTML OPTIMIZADA PARA MÓVIL ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Power Trade Mobile</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .disabled-btn { background-color: #9ca3af !important; cursor: not-allowed; opacity: 0.6; }
        input, select, textarea { font-size: 16px !important; } /* Evita zoom en iOS */
    </style>
</head>
<body class="bg-slate-50 antialiased text-slate-900">
    <div class="min-h-screen flex flex-col">
        <header class="bg-blue-900 text-white p-4 shadow-lg text-center sticky top-0 z-50">
            <h1 class="text-lg font-black uppercase tracking-widest">Power Trade</h1>
            <p class="text-[10px] opacity-75">REGISTRO DE VISITA TÉCNICA</p>
        </header>

        <main class="flex-grow p-4">
            <form id="visitaForm" action="/guardar" method="POST" enctype="multipart/form-data" class="max-w-md mx-auto space-y-5">
                
                <div class="space-y-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase ml-1">Funcionario</label>
                    <select name="funcionario" class="w-full bg-white border-2 border-slate-200 p-3 rounded-2xl shadow-sm focus:border-blue-500 outline-none transition-all" required>
                        <option value="">Seleccione...</option>
                        {% for f in funcionarios %}<option value="{{ f }}">{{ f }}</option>{% endfor %}
                    </select>
                </div>

                <div class="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm space-y-4">
                    <div class="grid grid-cols-1 gap-4">
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-blue-800 uppercase ml-1">Poc</label>
                            <select id="poc_sel" name="poc" onchange="sync('Poc')" class="w-full bg-slate-50 border border-slate-200 p-3 rounded-xl outline-none" required>
                                <option value="">-- Buscar Punto --</option>
                                {% for p in maestro %}<option value="{{ p.Poc }}">{{ p.Poc }}</option>{% endfor %}
                            </select>
                        </div>
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold text-blue-800 uppercase ml-1">Código BMB</label>
                            <select id="bmb_sel" name="bmb" onchange="sync('BMB')" class="w-full bg-slate-50 border border-slate-200 p-3 rounded-xl outline-none" required>
                                <option value="">-- Buscar Código --</option>
                                {% for p in maestro %}<option value="{{ p.BMB }}">{{ p.BMB }}</option>{% endfor %}
                            </select>
                        </div>
                    </div>

                    <div id="gps_status_box" class="mt-2 p-3 bg-slate-100 rounded-2xl flex items-center justify-between border border-dashed border-slate-300">
                        <div class="flex flex-col">
                            <span class="text-[9px] font-black text-slate-400 uppercase">Validación GPS</span>
                            <span id="distancia_txt" class="text-xs font-bold text-slate-500 italic">Esperando señal...</span>
                        </div>
                        <div id="gps_indicator" class="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
                    </div>
                    <input type="hidden" id="gps_input" name="ubicacion_gps">
                    <input type="hidden" id="distancia_val" name="distancia_metros">
                </div>

                <div class="space-y-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase ml-1">Motivo</label>
                    <select name="motivo" class="w-full bg-white border-2 border-slate-200 p-3 rounded-2xl shadow-sm outline-none" required>
                        <option value="Ruta">Visita de Ruta</option>
                        <option value="Maquina Retirada">Máquina Retirada</option>
                        <option value="Poc Cerrado">Punto Cerrado</option>
                        <option value="Novedad">Novedad / Otros</option>
                    </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <label class="relative flex flex-col items-center justify-center p-4 bg-white border-2 border-dashed border-slate-300 rounded-3xl hover:bg-slate-50 transition-colors">
                        <span class="text-[10px] font-bold text-blue-900 uppercase">Máquina</span>
                        <input type="file" name="foto_maquina" accept="image/*" capture="camera" required class="absolute inset-0 opacity-0 cursor-pointer">
                        <span class="text-[9px] text-slate-400 mt-1">Tocar para Foto</span>
                    </label>
                    <label class="relative flex flex-col items-center justify-center p-4 bg-white border-2 border-dashed border-slate-300 rounded-3xl hover:bg-slate-50 transition-colors">
                        <span class="text-[10px] font-bold text-blue-900 uppercase">Fachada</span>
                        <input type="file" name="foto_fachada" accept="image/*" capture="camera" required class="absolute inset-0 opacity-0 cursor-pointer">
                        <span class="text-[9px] text-slate-400 mt-1">Tocar para Foto</span>
                    </label>
                </div>

                <div class="space-y-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase ml-1">Observación</label>
                    <textarea name="observacion" rows="3" class="w-full bg-white border-2 border-slate-200 p-3 rounded-2xl shadow-sm outline-none resize-none" placeholder="Detalles adicionales..."></textarea>
                </div>

                <button type="submit" id="btn_submit" disabled class="disabled-btn w-full bg-blue-900 text-white font-black py-4 rounded-2xl shadow-xl transition-all uppercase tracking-widest text-sm active:scale-95">
                    Finalizar Reporte
                </button>
            </form>
        </main>
    </div>

    <script>
        const maestro = {{ maestro_json | safe }};
        let uLat, uLon, gpsReady = false;

        const btn = document.getElementById('btn_submit');
        const txtDist = document.getElementById('distancia_txt');
        const indicator = document.getElementById('gps_indicator');

        function calcDist(lat1, lon1, lat2, lon2) {
            const R = 6371000;
            const dLat = (lat2-lat1)*Math.PI/180;
            const dLon = (lon2-lon1)*Math.PI/180;
            const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
            return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
        }

        function checkFormStatus() {
            const poc = document.getElementById('poc_sel').value;
            const dist = document.getElementById('distancia_val').value;
            
            if(gpsReady && poc !== "" && dist !== "") {
                btn.disabled = false;
                btn.classList.remove('disabled-btn');
            } else {
                btn.disabled = true;
                btn.classList.add('disabled-btn');
            }
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
                    txtDist.innerText = mts + " metros de distancia";
                    document.getElementById('distancia_val').value = mts;
                    txtDist.className = mts > 150 ? "text-xs font-black text-red-600" : "text-xs font-black text-green-600";
                    checkFormStatus();
                }
            }
        }

        navigator.geolocation.watchPosition(p => {
            uLat = p.coords.latitude; 
            uLon = p.coords.longitude;
            gpsReady = true;
            document.getElementById('gps_input').value = uLat + "," + uLon;
            indicator.classList.replace('bg-red-500', 'bg-green-500');
            indicator.classList.remove('animate-pulse');
            if(document.getElementById('poc_sel').value) sync('Poc');
        }, err => {
            txtDist.innerText = "Error: Activa el GPS";
        }, { enableHighAccuracy: true });
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
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "ubicacion_gps": request.form.get('ubicacion_gps'),
            "desviacion_metros": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "fecha": datetime.now().strftime("%Y-%m-%d")
        }
        guardar_registro(doc)
        # Ventana de éxito tipo móvil
        return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-100 flex items-center justify-center min-h-screen p-6">
            <div class="bg-white p-8 rounded-[40px] shadow-2xl text-center max-w-xs w-full border-t-8 border-green-500">
                <div class="text-green-500 text-6xl mb-4">✔</div>
                <h1 class="text-2xl font-black text-slate-800 mb-2 italic">¡LISTO!</h1>
                <p class="text-slate-500 text-sm mb-6">El reporte ha sido guardado exitosamente.</p>
                <a href="/" class="block w-full bg-slate-900 text-white font-bold py-4 rounded-2xl shadow-lg uppercase tracking-tighter">Nueva Visita</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error: {e}</h1>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
