import os
import json
import gridfs
import pytz
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, Response, send_file
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "power_trade_ultra_2026")

# --- CONEXIÓN MONGODB ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['POWER_TRADE']
fs = gridfs.GridFS(db) 
coleccion_visitas = db['Visitas_a_POC']

# --- CONFIGURACIÓN DE FORMULARIOS DINÁMICOS ---
CONFIG_FORMULARIOS = {
    "prospecciones": {
        "titulo": "Registro de Prospecto",
        "icono": "fa-magnifying-glass-location",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "contacto", "label": "Nombre Propietario", "type": "text", "required": True},
            {"id": "telefono", "label": "Teléfono", "type": "number", "required": True},
            {"id": "direccion", "label": "Dirección", "type": "text", "required": True},
            {"id": "Sector", "label": "Sector", "type": "select", "options": ["Educacion", "Cafeteria", "Panaderia","Restaurante","Salud","Transporte","Tinteros"], "required": True},
            {"id": "Interesado en?", "label": "Interesado en?", "type": "select", "options": ["Maquina", "Food", "Ambos","No esta interesado"], "required": True},
            {"id": "productos", "label": "Productos", "type": "multiselect", "options": 
             ["Maquina",
              "Nescafe Alegria Cappuccino 4 X 1 Kgco",
"Nescafe Alegria Cappu Vainillanp 4 X 1Kgco",
"Nescafe Alegria Cappu Vainillanp 4 X 1Kgco",
"Abuelita Chocolate Venta 6 X 750G Mx ",
"Nescafe Cafe En Grano Npro 6 X 1Kg Co",
"Nestle Cobertura De Cacao Leche 2 X 5Kg Co",
"Nestle Cobertura Cac Semiamarga 2 X 5Kg Co",
"La Lechera Leche Condensada 4 X 4.5Kg Co",
"La Lechera Npro Leche Condensada6 X 800Gco",
"Nescafe Dolca Npro 11 X 1Kg Co",
"Maggi Caldo Gallina Polvo 4 X 1.6Kg Co",
"Maggi Caldo Gallina Npro 4 X 2.97Kg Co",
"Maggi  X Contenido Caldo Gallina 4 X 1760G Co",
"Maggi Npro Doble Gusto Costilla 6 X 900Gco",
"Maggi Npro Salsa Demi-Glace 6 X 900G Co",
"Maggi Npro Salsa Bechamel 6 X 900G Co",
"Maggi Crema Marinera Npro 6 X 800G Co",
"Milo Activ-Go 4 X 2Kg Co",
"Milo X Npro 4 X 2200G Pr10%Co",
"Milo Activ-Go 4 X 2.5Kg Co",
"Milo  Npro 4 X 2750G Pr10%Co",
"Nescafe Tradicion Npro Lata 6 X 500G Co",
"Nescafe Cafe Con Leche X 800G",
"Natures Heart",
"Cobertura Chocolate Con Leche 500 Gr",
"Leche Klim 2.400 Gr",
"Leche Klim 2.000 Gr",
"Leche Klim 1.000 Gr",
"Leche Klim 840 Gr",
"Leche Rodeo 875 Gr",
"Leche Rodeo 1.250 Gr",
"La Lechera 800 Gr",
"La Lechera 4.5 Gr",
"Crema De Leche 186 Gr",
"Crema De Leche Lata 295 Gr",
"Milo Crema Untable 1Kg",
"Maggi Base Salsa Blanca 800Gr",
"Maggi Base De Tomate 800Gr",
"Morenitas Bites X 600 Gr",
"Maggi Desmenuzado X 500 Gr"], "required": True},
            
            {"id": "Venta Efectiva", "label": "Venta Efectiva", "type": "select", "options": ["Si", "No"], "required": True},
            {"id": "Seguimiento", "label": "Seguimiento", "type": "select", "options": ["Si", "No"], "required": True},
            {"id": "observaciones", "label": "Notas", "type": "textarea", "required": False}
        ]
    },
    "leads": {
        "titulo": "Gestión de Leads", "icono": "fa-user-tie",
        "preguntas": [
            {"id": "cliente", "label": "Nombre Cliente", "type": "text", "required": True},
            {"id": "interes", "label": "Interés", "type": "multiselect", "options": ["Máquina Café", "Insumos", "Soporte"], "required": True},
            {"id": "estado", "label": "Estado", "type": "select", "options": ["Nuevo", "Seguimiento", "Cerrado"], "required": True}
        ]
    },
    "food": {
        "titulo": "Food Service", "icono": "fa-utensils",
        "preguntas": [
            {"id": "negocio", "label": "Nombre del Establecimiento", "type": "text", "required": True},
            {"id": "producto_1", "label": "Productos_1", "type": "select", "options": 
             ["Aro - Caldo Desmenuzado 800 Grs",
"Aro - Caldo gallina 1 Kg",
"Aro - Base bechamel Aro x 1 Kg",
"Aro - Leche condesada Aro x 1.3 Kg",
"Aro - Leche condesada Aro x 3.9 Kg",
"Aro - Leche condesada Aro x 5 Kg",
"Bugueña - Leche condensada la bugueña x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Carreta - Leche condensada la Carreta x 1 Kg",
"Carreta - Leche condensada la Carreta x 5 Kg",
"Colombina - Nucita x 1 Kg",
"Colombina - Nucita x 1.5 Kg",
"Colombina - Nucita x 2 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate con leche x 500 Grs",
"Cordillera - Cobertura dulce Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate amargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 1 Kg",
"Cordillera - Cobertura dulce Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate con leche x 1 Kg",
"Cordillera - Cobertura de chocolate amargo Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2 Kg",
"Cordillera - Cobertura dulce Cordillera x 2.5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2.5 Kg",
"Cordillera - Cobertura dulce Cordillera x 5 Kg",
"Cordillera - Cobertura de chocolate con leche x 5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 5 Kg",
"Corona - Cobertura de chocolate semiamargo corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 1 Kg",
"Corona - Cobertura tipo leche corona x 2 Kg",
"DLuchi - Cobertura de chocolate DLuchi x 500 Grs",
"DLuchi - Cobertura de chocolate semiamargo DLuchi x 500 Grs",
"Doña gallina - Doña gallina en cubos x 240 cubos",
"Doña gallina - Doña gallina en cubos x 270 cubos",
"Doña Gallina - Caldo Doña Gallina x 900 Grs",
"Doña Gallina - Caldo Doña Gallina x 1.5 Kg",
"DVida - Leche condesada Dvida x 500 Grs",
"DVida - Leche condesada Dvida x 1 Kg",
"DVida - Leche condesada Dvida x 1250 Grs",
"DVida - Leche condesada Dvida x 2.5 Kg",
"DVida - Leche condesada Dvida x 2650 Grs",
"DVida - Leche condesada Dvida x 4 Kg",
"DVida - Leche condesada Dvida x 5 Kg",
"Knorr - Caldo Knorr gallina x 240 cubos",
"Knorr - Base de tomate knorr x 500 Grs",
"Knorr - Caldo de Gallina Knorr x 500 Grs",
"Knorr - Caldo Knorr gallina x 500 Grs",
"Knorr - Caldo de costilla x 600 Grs",
"Knorr - Salsa bechamel Knorr x 800 Grs",
"Knorr - Salsa demiglace Knorr x 800 Grs",
"Knorr - Caldo de Gallina Knorr x 800 Grs",
"Knorr - Crema de champiñones Knorr x 800 Grs",
"Knorr - Crema de pollo Knorr x 800 Grs",
"Knorr - Caldo de costilla x 800 Grs",
"Knorr - Caldo de costilla x 900 Grs",
"Knorr - Salsa demiglace Knorr x 900 Grs",
"Knorr - Salsa demiglace Knorr x 1 Kg",
"Knorr - Caldo de Gallina Knorr x 1.5 Kg",
"Knorr - Caldo de costilla desmenuzado x 1.5 Kg",
"Knorr - Caldo de Gallina Knorr x 1.6 Kg",
"Lujus - Leche condesada Lujus x 1 Kg",
"Lujus - Leche condesada Lujus x 1250 Grs",
"Luker - Cobertura chocolate con leche luker x 1 Kg",
"Luker - Cobertura semiamarga Luker x 1 Kg",
"Luker - Cobertura de chocolate negro luker x 1 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 1 Kg",
"luker - Cobertura chocolate con leche luker x 1.5 Kg",
"Luker - Cobertura semiamarga Luker x 2.5 Kg",
"Luker - Cobertura chocolate con leche luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 2.5 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 5 Kg",
"Maggi - Maggi Crema Marinera Npro 6X800G Co",
"Maggi - Maggi Npro Salsa Bechamel 6X900G Co",
"Maggi - Maggi Npro Salsa Demi-Glace 6X900G Co",
"Maggi - Caldo Maggi Doble Gusto Costilla x 900 Grs",
"Maggi - Salsa Bechamel Maggi X 900 Grs",
"Maggi - Caldo de gallina Maggi x 1.6 Kg",
"Maggi - Caldo maggi x 270 cubos",
"Melosa - Leche condensada la melosa x 2.5 Kg",
"Melosa - Leche condensada la melosa x 5 Kg",
"Melyma - Caldo de gallina Melyma x 800 Grs",
"Melyma - Caldo de costilla melyma x 800 Grs",
"Melyma - Salsa bechamel Aro x 1 Kg",
"Melyma - Caldo de costilla melyma x 1. Kg",
"Melyma - Caldo de costilla melyma x 1.6 Kg",
"Melyma - Caldo de gallina Melyma x 1.6 Kg",
"Melyma - Caldo de pescado Melyma x 1.6 Kg",
"Mi Vaquita - Leche Condensada Mi Vaquita x 800 Grs",
"Mi Vaquita - Leche Condensada Mi Vaquita x 4.5 Kg",
"Nestle - La Lechera Npro Leche Condensada 6X800 Grs",
"Nestle - La Lechera leche condensada 4X4.5Kg Co",
"Nestle - Cobertura de chocolate semiamargo Nestle x 5 Kg",
"Nestle - Cobertura de chocolate con leche Nestle x 5 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 1 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 2.5 Kg",
"Ricostilla - Ricostilla en cubos x 220 cubos",
"Ricostilla - Ricostilla en cubos x 240 cubos",
"Ricostilla - Ricostilla en cubos x 270 cubos",
"Ricostilla - Ricostilla x 500 Grs",
"Ricostilla - Caldo de costilla en polvo 900 Grs",
"Ricostilla - Caldo de costilla en polvo 1.5 Kg",
"Santillana - Cobertura de chocolate negro Santillana x 1 Kg",
"Santillana - Cobertura de chocolate blanca Santillana x 1 Kg",
"Santillana - Cobertura de chocolate semiamargo Santillana x 1 Kg",
"Santillana - Leche condensada santillana x 3.8 Kg",
"Sicao - Chocolate Sicao semiamargo x  5 Kg",
"Sicao - Chocolate Sicao x  5 Kg",
"Sicao - Chocolate semiamargo Sicao x  5 Kg",
"Vakanisima - Leche condesada Vakanisima x 500 Grs",
"Vakanisima - Leche condesada Vakanisima x 1 Kg",
"Vakanisima - Leche condesada Vakanisima x 1.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 2.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 4 Kg",
"Vakanisima - Leche condesada Vakanisima x 5 Kg",
"Zafran - Salsa bechamel Zafran 1 Kg",
"Zafran - Caldo de gallina zafran x 1 Kg",
"Zafran - Caldo de gallina zafran x 1.5 Kg",
"Zafran - Caldo de gallina zafran x 5 Kg",
"Melyma - Crema Marinera Melyma x 900 Grs",
"Tecna - Caldo de gallina tecna x 1 Kg",
"Dulpan - Leche condesada Dulpan x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Amy - Leche condesada Amy x 3.9 Kg",
"Amy - Leche condesada Amy x 5 Kg",
"Maggi - Base de tomate Maggi 800 Grs",
"Maggi - Base salsa blanca Maggi 800 Grs",
"Imperio - Leche condesada Imperio x 4,8 Kg",
"Imperio - Leche condesada Imperio x 2,6 Kg",
"Pastelfnuf - Leche condesada Pastelfnuf x 4,8 Kg",
"Secreto - Leche condensada Secreto del tropico x 1 Kg",
"Santillana -  Lechera Santillana X 1.4 Kg",
"Santillana -  Lechera Santillana X 575 Kg",
"Selva -  Cobertura Selva 1Kg",
"Selva -  Cobertura Selva 2.5Kg",
"Nestle -  Lechera Nestlé X 2Kg",
"Maggi Barato"], "required": True},
            
            {"id": "Precio_1", "label": "Precio_1",  "type": "text", "required": True},
            {"id": "producto_2", "label": "Productos_2", "type": "select", "options": 
             ["Aro - Caldo Desmenuzado 800 Grs",
"Aro - Caldo gallina 1 Kg",
"Aro - Base bechamel Aro x 1 Kg",
"Aro - Leche condesada Aro x 1.3 Kg",
"Aro - Leche condesada Aro x 3.9 Kg",
"Aro - Leche condesada Aro x 5 Kg",
"Bugueña - Leche condensada la bugueña x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Carreta - Leche condensada la Carreta x 1 Kg",
"Carreta - Leche condensada la Carreta x 5 Kg",
"Colombina - Nucita x 1 Kg",
"Colombina - Nucita x 1.5 Kg",
"Colombina - Nucita x 2 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate con leche x 500 Grs",
"Cordillera - Cobertura dulce Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate amargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 1 Kg",
"Cordillera - Cobertura dulce Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate con leche x 1 Kg",
"Cordillera - Cobertura de chocolate amargo Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2 Kg",
"Cordillera - Cobertura dulce Cordillera x 2.5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2.5 Kg",
"Cordillera - Cobertura dulce Cordillera x 5 Kg",
"Cordillera - Cobertura de chocolate con leche x 5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 5 Kg",
"Corona - Cobertura de chocolate semiamargo corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 1 Kg",
"Corona - Cobertura tipo leche corona x 2 Kg",
"DLuchi - Cobertura de chocolate DLuchi x 500 Grs",
"DLuchi - Cobertura de chocolate semiamargo DLuchi x 500 Grs",
"Doña gallina - Doña gallina en cubos x 240 cubos",
"Doña gallina - Doña gallina en cubos x 270 cubos",
"Doña Gallina - Caldo Doña Gallina x 900 Grs",
"Doña Gallina - Caldo Doña Gallina x 1.5 Kg",
"DVida - Leche condesada Dvida x 500 Grs",
"DVida - Leche condesada Dvida x 1 Kg",
"DVida - Leche condesada Dvida x 1250 Grs",
"DVida - Leche condesada Dvida x 2.5 Kg",
"DVida - Leche condesada Dvida x 2650 Grs",
"DVida - Leche condesada Dvida x 4 Kg",
"DVida - Leche condesada Dvida x 5 Kg",
"Knorr - Caldo Knorr gallina x 240 cubos",
"Knorr - Base de tomate knorr x 500 Grs",
"Knorr - Caldo de Gallina Knorr x 500 Grs",
"Knorr - Caldo Knorr gallina x 500 Grs",
"Knorr - Caldo de costilla x 600 Grs",
"Knorr - Salsa bechamel Knorr x 800 Grs",
"Knorr - Salsa demiglace Knorr x 800 Grs",
"Knorr - Caldo de Gallina Knorr x 800 Grs",
"Knorr - Crema de champiñones Knorr x 800 Grs",
"Knorr - Crema de pollo Knorr x 800 Grs",
"Knorr - Caldo de costilla x 800 Grs",
"Knorr - Caldo de costilla x 900 Grs",
"Knorr - Salsa demiglace Knorr x 900 Grs",
"Knorr - Salsa demiglace Knorr x 1 Kg",
"Knorr - Caldo de Gallina Knorr x 1.5 Kg",
"Knorr - Caldo de costilla desmenuzado x 1.5 Kg",
"Knorr - Caldo de Gallina Knorr x 1.6 Kg",
"Lujus - Leche condesada Lujus x 1 Kg",
"Lujus - Leche condesada Lujus x 1250 Grs",
"Luker - Cobertura chocolate con leche luker x 1 Kg",
"Luker - Cobertura semiamarga Luker x 1 Kg",
"Luker - Cobertura de chocolate negro luker x 1 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 1 Kg",
"luker - Cobertura chocolate con leche luker x 1.5 Kg",
"Luker - Cobertura semiamarga Luker x 2.5 Kg",
"Luker - Cobertura chocolate con leche luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 2.5 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 5 Kg",
"Maggi - Maggi Crema Marinera Npro 6X800G Co",
"Maggi - Maggi Npro Salsa Bechamel 6X900G Co",
"Maggi - Maggi Npro Salsa Demi-Glace 6X900G Co",
"Maggi - Caldo Maggi Doble Gusto Costilla x 900 Grs",
"Maggi - Salsa Bechamel Maggi X 900 Grs",
"Maggi - Caldo de gallina Maggi x 1.6 Kg",
"Maggi - Caldo maggi x 270 cubos",
"Melosa - Leche condensada la melosa x 2.5 Kg",
"Melosa - Leche condensada la melosa x 5 Kg",
"Melyma - Caldo de gallina Melyma x 800 Grs",
"Melyma - Caldo de costilla melyma x 800 Grs",
"Melyma - Salsa bechamel Aro x 1 Kg",
"Melyma - Caldo de costilla melyma x 1. Kg",
"Melyma - Caldo de costilla melyma x 1.6 Kg",
"Melyma - Caldo de gallina Melyma x 1.6 Kg",
"Melyma - Caldo de pescado Melyma x 1.6 Kg",
"Mi Vaquita - Leche Condensada Mi Vaquita x 800 Grs",
"Mi Vaquita - Leche Condensada Mi Vaquita x 4.5 Kg",
"Nestle - La Lechera Npro Leche Condensada 6X800 Grs",
"Nestle - La Lechera leche condensada 4X4.5Kg Co",
"Nestle - Cobertura de chocolate semiamargo Nestle x 5 Kg",
"Nestle - Cobertura de chocolate con leche Nestle x 5 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 1 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 2.5 Kg",
"Ricostilla - Ricostilla en cubos x 220 cubos",
"Ricostilla - Ricostilla en cubos x 240 cubos",
"Ricostilla - Ricostilla en cubos x 270 cubos",
"Ricostilla - Ricostilla x 500 Grs",
"Ricostilla - Caldo de costilla en polvo 900 Grs",
"Ricostilla - Caldo de costilla en polvo 1.5 Kg",
"Santillana - Cobertura de chocolate negro Santillana x 1 Kg",
"Santillana - Cobertura de chocolate blanca Santillana x 1 Kg",
"Santillana - Cobertura de chocolate semiamargo Santillana x 1 Kg",
"Santillana - Leche condensada santillana x 3.8 Kg",
"Sicao - Chocolate Sicao semiamargo x  5 Kg",
"Sicao - Chocolate Sicao x  5 Kg",
"Sicao - Chocolate semiamargo Sicao x  5 Kg",
"Vakanisima - Leche condesada Vakanisima x 500 Grs",
"Vakanisima - Leche condesada Vakanisima x 1 Kg",
"Vakanisima - Leche condesada Vakanisima x 1.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 2.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 4 Kg",
"Vakanisima - Leche condesada Vakanisima x 5 Kg",
"Zafran - Salsa bechamel Zafran 1 Kg",
"Zafran - Caldo de gallina zafran x 1 Kg",
"Zafran - Caldo de gallina zafran x 1.5 Kg",
"Zafran - Caldo de gallina zafran x 5 Kg",
"Melyma - Crema Marinera Melyma x 900 Grs",
"Tecna - Caldo de gallina tecna x 1 Kg",
"Dulpan - Leche condesada Dulpan x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Amy - Leche condesada Amy x 3.9 Kg",
"Amy - Leche condesada Amy x 5 Kg",
"Maggi - Base de tomate Maggi 800 Grs",
"Maggi - Base salsa blanca Maggi 800 Grs",
"Imperio - Leche condesada Imperio x 4,8 Kg",
"Imperio - Leche condesada Imperio x 2,6 Kg",
"Pastelfnuf - Leche condesada Pastelfnuf x 4,8 Kg",
"Secreto - Leche condensada Secreto del tropico x 1 Kg",
"Santillana -  Lechera Santillana X 1.4 Kg",
"Santillana -  Lechera Santillana X 575 Kg",
"Selva -  Cobertura Selva 1Kg",
"Selva -  Cobertura Selva 2.5Kg",
"Nestle -  Lechera Nestlé X 2Kg",
"Maggi Barato"], "required": True},
            
            {"id": "Precio_2", "label": "Precio_2",  "type": "text", "required": True},
            {"id": "producto_3", "label": "Productos_3", "type": "select", "options": 
             ["Aro - Caldo Desmenuzado 800 Grs",
"Aro - Caldo gallina 1 Kg",
"Aro - Base bechamel Aro x 1 Kg",
"Aro - Leche condesada Aro x 1.3 Kg",
"Aro - Leche condesada Aro x 3.9 Kg",
"Aro - Leche condesada Aro x 5 Kg",
"Bugueña - Leche condensada la bugueña x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Carreta - Leche condensada la Carreta x 1 Kg",
"Carreta - Leche condensada la Carreta x 5 Kg",
"Colombina - Nucita x 1 Kg",
"Colombina - Nucita x 1.5 Kg",
"Colombina - Nucita x 2 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate con leche x 500 Grs",
"Cordillera - Cobertura dulce Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate amargo Cordillera x 500 Grs",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 1 Kg",
"Cordillera - Cobertura dulce Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate con leche x 1 Kg",
"Cordillera - Cobertura de chocolate amargo Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate blanco Cordillera x 1 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2 Kg",
"Cordillera - Cobertura dulce Cordillera x 2.5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 2.5 Kg",
"Cordillera - Cobertura dulce Cordillera x 5 Kg",
"Cordillera - Cobertura de chocolate con leche x 5 Kg",
"Cordillera - Cobertura de chocolate semiamargo Cordillera x 5 Kg",
"Corona - Cobertura de chocolate semiamargo corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 500 Grs",
"Corona - Cobertura tipo leche corona x 1 Kg",
"Corona - Cobertura tipo leche corona x 2 Kg",
"DLuchi - Cobertura de chocolate DLuchi x 500 Grs",
"DLuchi - Cobertura de chocolate semiamargo DLuchi x 500 Grs",
"Doña gallina - Doña gallina en cubos x 240 cubos",
"Doña gallina - Doña gallina en cubos x 270 cubos",
"Doña Gallina - Caldo Doña Gallina x 900 Grs",
"Doña Gallina - Caldo Doña Gallina x 1.5 Kg",
"DVida - Leche condesada Dvida x 500 Grs",
"DVida - Leche condesada Dvida x 1 Kg",
"DVida - Leche condesada Dvida x 1250 Grs",
"DVida - Leche condesada Dvida x 2.5 Kg",
"DVida - Leche condesada Dvida x 2650 Grs",
"DVida - Leche condesada Dvida x 4 Kg",
"DVida - Leche condesada Dvida x 5 Kg",
"Knorr - Caldo Knorr gallina x 240 cubos",
"Knorr - Base de tomate knorr x 500 Grs",
"Knorr - Caldo de Gallina Knorr x 500 Grs",
"Knorr - Caldo Knorr gallina x 500 Grs",
"Knorr - Caldo de costilla x 600 Grs",
"Knorr - Salsa bechamel Knorr x 800 Grs",
"Knorr - Salsa demiglace Knorr x 800 Grs",
"Knorr - Caldo de Gallina Knorr x 800 Grs",
"Knorr - Crema de champiñones Knorr x 800 Grs",
"Knorr - Crema de pollo Knorr x 800 Grs",
"Knorr - Caldo de costilla x 800 Grs",
"Knorr - Caldo de costilla x 900 Grs",
"Knorr - Salsa demiglace Knorr x 900 Grs",
"Knorr - Salsa demiglace Knorr x 1 Kg",
"Knorr - Caldo de Gallina Knorr x 1.5 Kg",
"Knorr - Caldo de costilla desmenuzado x 1.5 Kg",
"Knorr - Caldo de Gallina Knorr x 1.6 Kg",
"Lujus - Leche condesada Lujus x 1 Kg",
"Lujus - Leche condesada Lujus x 1250 Grs",
"Luker - Cobertura chocolate con leche luker x 1 Kg",
"Luker - Cobertura semiamarga Luker x 1 Kg",
"Luker - Cobertura de chocolate negro luker x 1 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 1 Kg",
"luker - Cobertura chocolate con leche luker x 1.5 Kg",
"Luker - Cobertura semiamarga Luker x 2.5 Kg",
"Luker - Cobertura chocolate con leche luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 2.5 Kg",
"Luker - Cobertura de chocolate Blanco Luker x 2.5 Kg",
"Luker - Cobertura de chocolate negro luker x 5 Kg",
"Maggi - Maggi Crema Marinera Npro 6X800G Co",
"Maggi - Maggi Npro Salsa Bechamel 6X900G Co",
"Maggi - Maggi Npro Salsa Demi-Glace 6X900G Co",
"Maggi - Caldo Maggi Doble Gusto Costilla x 900 Grs",
"Maggi - Salsa Bechamel Maggi X 900 Grs",
"Maggi - Caldo de gallina Maggi x 1.6 Kg",
"Maggi - Caldo maggi x 270 cubos",
"Melosa - Leche condensada la melosa x 2.5 Kg",
"Melosa - Leche condensada la melosa x 5 Kg",
"Melyma - Caldo de gallina Melyma x 800 Grs",
"Melyma - Caldo de costilla melyma x 800 Grs",
"Melyma - Salsa bechamel Aro x 1 Kg",
"Melyma - Caldo de costilla melyma x 1. Kg",
"Melyma - Caldo de costilla melyma x 1.6 Kg",
"Melyma - Caldo de gallina Melyma x 1.6 Kg",
"Melyma - Caldo de pescado Melyma x 1.6 Kg",
"Mi Vaquita - Leche Condensada Mi Vaquita x 800 Grs",
"Mi Vaquita - Leche Condensada Mi Vaquita x 4.5 Kg",
"Nestle - La Lechera Npro Leche Condensada 6X800 Grs",
"Nestle - La Lechera leche condensada 4X4.5Kg Co",
"Nestle - Cobertura de chocolate semiamargo Nestle x 5 Kg",
"Nestle - Cobertura de chocolate con leche Nestle x 5 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 1 Kg",
"Palenque - Cobertura de chocolate oscuro Palenque x 2.5 Kg",
"Ricostilla - Ricostilla en cubos x 220 cubos",
"Ricostilla - Ricostilla en cubos x 240 cubos",
"Ricostilla - Ricostilla en cubos x 270 cubos",
"Ricostilla - Ricostilla x 500 Grs",
"Ricostilla - Caldo de costilla en polvo 900 Grs",
"Ricostilla - Caldo de costilla en polvo 1.5 Kg",
"Santillana - Cobertura de chocolate negro Santillana x 1 Kg",
"Santillana - Cobertura de chocolate blanca Santillana x 1 Kg",
"Santillana - Cobertura de chocolate semiamargo Santillana x 1 Kg",
"Santillana - Leche condensada santillana x 3.8 Kg",
"Sicao - Chocolate Sicao semiamargo x  5 Kg",
"Sicao - Chocolate Sicao x  5 Kg",
"Sicao - Chocolate semiamargo Sicao x  5 Kg",
"Vakanisima - Leche condesada Vakanisima x 500 Grs",
"Vakanisima - Leche condesada Vakanisima x 1 Kg",
"Vakanisima - Leche condesada Vakanisima x 1.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 2.5 Kg",
"Vakanisima - Leche condesada Vakanisima x 4 Kg",
"Vakanisima - Leche condesada Vakanisima x 5 Kg",
"Zafran - Salsa bechamel Zafran 1 Kg",
"Zafran - Caldo de gallina zafran x 1 Kg",
"Zafran - Caldo de gallina zafran x 1.5 Kg",
"Zafran - Caldo de gallina zafran x 5 Kg",
"Melyma - Crema Marinera Melyma x 900 Grs",
"Tecna - Caldo de gallina tecna x 1 Kg",
"Dulpan - Leche condesada Dulpan x 1 Kg",
"Bugueña - Leche condensada la bugueña x 5 Kg",
"Amy - Leche condesada Amy x 3.9 Kg",
"Amy - Leche condesada Amy x 5 Kg",
"Maggi - Base de tomate Maggi 800 Grs",
"Maggi - Base salsa blanca Maggi 800 Grs",
"Imperio - Leche condesada Imperio x 4,8 Kg",
"Imperio - Leche condesada Imperio x 2,6 Kg",
"Pastelfnuf - Leche condesada Pastelfnuf x 4,8 Kg",
"Secreto - Leche condensada Secreto del tropico x 1 Kg",
"Santillana -  Lechera Santillana X 1.4 Kg",
"Santillana -  Lechera Santillana X 575 Kg",
"Selva -  Cobertura Selva 1Kg",
"Selva -  Cobertura Selva 2.5Kg",
"Nestle -  Lechera Nestlé X 2Kg",
"Maggi Barato"], "required": True},
            
            {"id": "Precio_3", "label": "Precio_3",  "type": "text", "required": True},
        ]
    },
    "competencias": {
        "titulo": "Competencia", "icono": "fa-handshake-slash",
        "preguntas": [
            {"id": "marca", "label": "Marca Competidora", "type": "text", "required": True},
            {"id": "modelo", "label": "Modelo", "type": "select", "options": ["Venta", "Comodato"], "required": True}
        ]
    },
    "ingredientes": {
        "titulo": "Insumos e Ingredientes", "icono": "fa-jar",
        "preguntas": [
            {"id": "item", "label": "Ingrediente", "type": "text", "required": True},
            {"id": "stock", "label": "Estado", "type": "select", "options": ["Ok", "Bajo", "Agotado"], "required": True}
        ]
    }
}

# --- DATOS MAESTROS ---
FUNCIONARIOS = sorted(["ANDRES VANEGAS", "CINDY BOCANEGRA", "KEVIN MARIN", "MAURICIO LADINO", "MONICA PATIÑO"])
TABLA_PUNTOS = [["Tienda El Porvenir", "BMB-1010", "4.6097, -74.0817"]]
DATOS_MAESTROS = [{"Poc": f[0], "BMB": f[1], "Ubicacion_Ref": f[2]} for f in TABLA_PUNTOS]

def get_colombia_time():
    return datetime.now(pytz.timezone('America/Bogota'))

# --- RUTAS ---

@app.route('/')
def index():
    return render_template('formulario.html', funcionarios=FUNCIONARIOS, maestro=DATOS_MAESTROS, maestro_json=json.dumps(DATOS_MAESTROS))

@app.route('/form/<tipo>')
def render_form_dinamico(tipo):
    if tipo not in CONFIG_FORMULARIOS: return "Error", 404
    config = CONFIG_FORMULARIOS[tipo]
    return render_template('prospecciones.html', funcionarios=FUNCIONARIOS, preguntas=config['preguntas'], titulo=config['titulo'], icono=config['icono'], tipo_url=tipo)


@app.route('/guardar_dinamico/<tipo>', methods=['POST'])
def guardar_dinamico(tipo):
    ahora = get_colombia_time()
    datos_raw = request.form.to_dict(flat=False)
    datos_procesados = {k: v if len(v) > 1 else v[0] for k, v in datos_raw.items()}
    datos_procesados["fecha"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
    db[tipo].insert_one(datos_procesados)
    return redirect(url_for('render_form_dinamico', tipo=tipo))

@app.route('/guardar_visita', methods=['POST'])
def guardar_visita():
    try:
        f1 = fs.put(request.files['foto_maquina'], filename="maquina.jpg")
        f2 = fs.put(request.files['foto_fachada'], filename="fachada.jpg")
        ahora = get_colombia_time()
        doc = {
            "funcionario": request.form.get('funcionario'),
            "poc": request.form.get('poc'),
            "bmb": request.form.get('bmb'),
            "gps_real": request.form.get('gps_real'),
            "distancia_mts": request.form.get('distancia_metros'),
            "motivo": request.form.get('motivo'),
            "observacion": request.form.get('observacion'),
            "foto_maquina_id": str(f1),
            "foto_fachada_id": str(f2),
            "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S")
        }
        coleccion_visitas.insert_one(doc)
        return redirect(url_for('ver_registros', f_inicio=ahora.strftime("%Y-%m-%d"), f_fin=ahora.strftime("%Y-%m-%d")))
    except Exception as e: return f"Error: {e}", 500

@app.route('/registros')
def ver_registros():
    f_inicio = request.args.get('f_inicio', get_colombia_time().strftime("%Y-%m-%d"))
    f_fin = request.args.get('f_fin', get_colombia_time().strftime("%Y-%m-%d"))
    busqueda = request.args.get('busqueda', '').strip()
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    if busqueda:
        query["$or"] = [{"poc": {"$regex": busqueda, "$options": "i"}}, {"bmb": {"$regex": busqueda, "$options": "i"}}]
    registros = list(coleccion_visitas.find(query).sort("fecha", -1))
    return render_template('registros.html', registros=registros, f_inicio=f_inicio, f_fin=f_fin, busqueda=busqueda)

@app.route('/descargar_excel')
def descargar_excel():
    f_inicio = request.args.get('f_inicio')
    f_fin = request.args.get('f_fin')
    query = {"fecha": {"$gte": f"{f_inicio} 00:00:00", "$lte": f"{f_fin} 23:59:59"}}
    datos = list(coleccion_visitas.find(query))
    if not datos: return "No hay datos", 404
    df = pd.DataFrame(datos)
    for col in ['_id', 'foto_maquina_id', 'foto_fachada_id']:
        if col in df.columns: del df[col]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"PowerTrade_{f_inicio}.xlsx")

@app.route('/foto/<foto_id>')
def servir_foto(foto_id):
    archivo = fs.get(ObjectId(foto_id))
    return Response(archivo.read(), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
