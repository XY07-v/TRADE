{% extends "base.html" %}
{% block content %}
<div class="space-y-5">
    <div class="bg-white p-5 rounded-[30px] shadow-md border border-slate-100">
        <form action="/registros" method="GET" class="space-y-3">
            <div class="grid grid-cols-2 gap-2">
                <input type="date" name="f_inicio" value="{{ f_inicio }}" class="w-full p-3 bg-slate-50 rounded-xl text-xs border-none" required>
                <input type="date" name="f_fin" value="{{ f_fin }}" class="w-full p-3 bg-slate-50 rounded-xl text-xs border-none" required>
            </div>
            <button type="submit" class="w-full bg-blue-900 text-white font-black py-3 rounded-xl uppercase text-[10px]">Consultar</button>
        </form>
        {% if registros %}
        <a href="{{ url_for('descargar_excel', f_inicio=f_inicio, f_fin=f_fin) }}" class="block mt-2 w-full bg-green-600 text-white text-center font-black py-3 rounded-xl uppercase text-[10px]">📥 Descargar Excel</a>
        {% endif %}
    </div>

    <div class="space-y-4 pb-24">
        {% if not registros %}
            <p class="text-center text-slate-400 text-xs py-10">Seleccione un rango de fechas.</p>
        {% else %}
            {% for r in registros %}
            <div class="bg-white p-4 rounded-[30px] shadow-sm border border-slate-100">
                <div class="flex justify-between text-[9px] mb-2">
                    <span class="font-black text-blue-900 uppercase">{{ r.funcionario }}</span>
                    <span class="text-slate-400 font-bold">{{ r.fecha }}</span>
                </div>
                <h3 class="font-bold text-sm text-slate-800">{{ r.poc }}</h3>
                <p class="text-[10px] text-slate-500 mb-3">{{ r.distancia_mts }}m | {{ r.motivo }}</p>
                <div class="grid grid-cols-2 gap-2">
                    <img src="/foto/{{ r.foto_maquina_id }}" class="w-full h-32 object-cover rounded-2xl border bg-slate-50">
                    <img src="/foto/{{ r.foto_fachada_id }}" class="w-full h-32 object-cover rounded-2xl border bg-slate-50">
                </div>
            </div>
            {% endfor %}
        {% endif %}
    </div>
</div>
{% endblock %}
