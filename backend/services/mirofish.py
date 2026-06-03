"""
MIROFISH — Motor de Agentes IA Predictivos
==========================================
11 agentes que generan predicciones para TODOS los filtros del proyecto:

CAPAS EXISTENTES (Mirofish agrega predicciones a cada una):
  1.  sismico_pred        → Filtro: Actividad Sísmica
  2.  viento_extremo      → Filtro: Ráfagas Extremas
  3.  temperatura_anomalia→ Filtro: Anomalías de Temperatura
  4.  deshielo_pred       → Filtro: Deshielo Marítimo
  5.  sequia_pred         → Filtro: Pérdida Agua Dulce
  6.  tsunami_compuesto   → Filtro: Riesgo Tsunami
  7.  incendios_pred      → Filtro: Riesgo Incendios

CAPAS PROPIAS MIROFISH (pesca/marina):
  8.  cardumen            → Filtro: Zonas de Cardumen
  9.  corriente           → Filtro: Corriente de Malvinas
  10. alerta_pesca        → Filtro: Alerta Pesca
  11. bio_riesgo          → Filtro: Marea Roja (HAB)
"""

from datetime import datetime, timedelta
import math


# ---------------------------------------------------------------------------
# Constantes y puntos de referencia
# ---------------------------------------------------------------------------

PUNTOS_MARITIMOS = [
    {"name": "Pasaje de Drake",        "lat": -59.5,  "lon": -64.0},
    {"name": "Mar Argentino Austral",  "lat": -53.0,  "lon": -62.0},
    {"name": "Islas Orcadas del Sur",  "lat": -60.7,  "lon": -45.0},
    {"name": "Estrecho de Magallanes", "lat": -53.5,  "lon": -70.5},
    {"name": "Mar de Weddell",         "lat": -64.0,  "lon": -45.0},
    {"name": "Península Antártica",    "lat": -65.0,  "lon": -60.0},
    {"name": "Banco Burdwood",         "lat": -54.5,  "lon": -59.0},
    {"name": "Canal Beagle",           "lat": -55.0,  "lon": -68.0},
    {"name": "Bahía San Julián",       "lat": -49.3,  "lon": -67.7},
]

PUNTOS_CONTINENTALES = [
    {"name": "Ushuaia",         "lat": -54.8,  "lon": -68.3},
    {"name": "Río Grande",      "lat": -53.78, "lon": -67.7},
    {"name": "Tolhuin",         "lat": -54.51, "lon": -67.19},
    {"name": "Río Gallegos",    "lat": -51.62, "lon": -69.22},
    {"name": "Rawson",          "lat": -43.3,  "lon": -65.1},
    {"name": "Viedma",          "lat": -40.81, "lon": -62.99},
    {"name": "Neuquén",         "lat": -38.95, "lon": -68.06},
    {"name": "Santa Rosa",      "lat": -36.62, "lon": -64.28},
    {"name": "Mendoza",         "lat": -32.89, "lon": -68.83},
    {"name": "Córdoba",         "lat": -31.42, "lon": -64.19},
]

# Corriente de Malvinas — nodos de referencia S→N
CORRIENTE_MALVINAS = [
    {"lat": -57.0, "lon": -64.0},
    {"lat": -54.0, "lon": -63.5},
    {"lat": -50.0, "lon": -62.0},
    {"lat": -46.0, "lon": -60.0},
    {"lat": -42.0, "lon": -58.5},
    {"lat": -38.0, "lon": -54.0},
]

# Zonas de alto riesgo sísmico regional (fallas conocidas en Patagonia y Andes)
FALLAS_REGIONALES = [
    {"name": "Falla Liquiñe-Ofqui",    "lat": -42.0, "lon": -73.0, "riesgo_base": 0.7},
    {"name": "Zona Subducción Sur",    "lat": -46.0, "lon": -76.0, "riesgo_base": 0.8},
    {"name": "Falla Magallanes",        "lat": -53.0, "lon": -71.0, "riesgo_base": 0.5},
    {"name": "Placa Scotia",            "lat": -57.0, "lon": -60.0, "riesgo_base": 0.6},
    {"name": "Zona Drake N",            "lat": -60.0, "lon": -63.0, "riesgo_base": 0.6},
    {"name": "Antártida Occidental",    "lat": -65.0, "lon": -80.0, "riesgo_base": 0.4},
    {"name": "Cordillera Neuquén",      "lat": -37.5, "lon": -70.5, "riesgo_base": 0.65},
    {"name": "Cordillera San Juan",     "lat": -31.0, "lon": -69.0, "riesgo_base": 0.75},
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _fecha_futura(dias: int) -> str:
    return (datetime.utcnow() + timedelta(days=dias)).strftime("%Y-%m-%dT12:00:00Z")


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return round(max(lo, min(hi, v)), 1)


def _dist(lat1, lon1, lat2, lon2) -> float:
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def _nearest(lat: float, lon: float, datos: list) -> dict | None:
    if not datos:
        return None
    return min(datos, key=lambda c: _dist(lat, lon, c["lat"], c["lon"]))


def _split_clima(datos_clima: list):
    """Separa el listado en marítimos (deshielo>0) y continentales."""
    mar = [c for c in datos_clima if c.get("deshielo_maritimo", 0) > 0]
    cont = [c for c in datos_clima if c.get("deshielo_maritimo", 0) == 0]
    return mar, cont


# ===========================================================================
# AGENTES PARA CAPAS EXISTENTES
# ===========================================================================

# ---------------------------------------------------------------------------
# AGENTE 1 — Predicción Sísmica (Mirofish)
# Alimenta el filtro: Actividad Sísmica
# ---------------------------------------------------------------------------
def agente_sismico_pred(sismos_recientes: list) -> list:
    """
    Analiza el clustering espacio-temporal de sismos recientes para estimar
    zonas de mayor probabilidad de futura actividad.
    
    Lógica:
    - Sismos >= 5.0 activan análisis de disipación de energía en falla
    - Sismos cluster (>= 3 eventos en radio 5°) sugieren secuencia activa
    - Zonas de falla regionales conocidas con probabilidad base aumentada
      si hay actividad reciente cercana
    - Proyección: días +2, +5, +7 con magnitud decreciente
    """
    predicciones = []

    fuertes = [s for s in sismos_recientes if s.get("magnitud", 0) >= 5.0]
    moderados = [s for s in sismos_recientes if 3.5 <= s.get("magnitud", 0) < 5.0]

    # Análisis de fallas regionales: ¿hay actividad cercana?
    for falla in FALLAS_REGIONALES:
        cercanos_fuertes = [
            s for s in fuertes
            if _dist(s["lat"], s["lon"], falla["lat"], falla["lon"]) < 6
        ]
        cercanos_mod = [
            s for s in moderados
            if _dist(s["lat"], s["lon"], falla["lat"], falla["lon"]) < 4
        ]

        # Calcular factor de riesgo combinado
        factor = falla["riesgo_base"]
        if cercanos_fuertes:
            mag_max = max(s["magnitud"] for s in cercanos_fuertes)
            factor += 0.15 * len(cercanos_fuertes) + (mag_max - 5.0) * 0.05
        if cercanos_mod:
            factor += 0.05 * min(len(cercanos_mod), 4)

        factor = _clip(factor, 0, 1)

        if factor < 0.45:
            continue  # riesgo bajo, no generar predicción

        # Magnitud predicha proporcional al factor
        mag_pred = round(3.0 + factor * 3.5, 1)
        intensidad = _clip(factor * 100)

        for dias, decay in [(2, 0.0), (5, -0.3), (7, -0.6)]:
            mag_dia = round(max(2.5, mag_pred + decay), 1)
            clasificacion = "Fuerte" if mag_dia >= 6 else "Moderado" if mag_dia >= 4 else "Bajo"
            color = "#ef4444" if clasificacion == "Fuerte" else "#f59e0b" if clasificacion == "Moderado" else "#60a5fa"

            predicciones.append({
                "tipo": "sismico_pred",
                "lat": round(falla["lat"] + (0.1 * dias), 4),
                "lon": round(falla["lon"] - (0.05 * dias), 4),
                "fecha": _fecha_futura(dias),
                "intensidad": _clip(intensidad - dias * 5),
                "descripcion": (
                    f"🤖 Mirofish Sísmico — {falla['name']}: "
                    f"M{mag_dia} estimada ({clasificacion}). "
                    f"Factor riesgo: {factor:.2f}. "
                    f"{'Basado en ' + str(len(cercanos_fuertes)) + ' evento(s) fuerte(s) reciente(s).' if cercanos_fuertes else 'Sin eventos fuertes cercanos recientes.'}"
                ),
                "color_hex": color,
                "es_alerta": mag_dia >= 5.5,
                # Campos extra para integrarse al estilo visual de sismos
                "magnitud": mag_dia,
                "clasificacion": clasificacion,
                "profundidad": 30.0,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 2 — Viento Extremo (Mirofish)
# Alimenta el filtro: Ráfagas Extremas
# ---------------------------------------------------------------------------
def agente_viento_extremo(datos_clima: list) -> list:
    """
    Proyecta evolución de ráfagas en zonas patagónicas usando:
    - Gradiente térmico continente-mar (fuerza el viento)  
    - Deshielo marítimo elevado → inestabilidad atmosférica
    - Efecto Föhn en vertiente oriental de la Cordillera
    Proyección: +1, +3, +5 días.
    """
    predicciones = []
    mar, cont = _split_clima(datos_clima)

    todos = datos_clima
    procesados = set()

    for c in todos:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        viento = c.get("viento", 0)
        temp = c.get("temperatura", 0)
        deshielo = c.get("deshielo_maritimo", 0)
        is_mar = c.get("deshielo_maritimo", 0) > 0

        # Calcular tendencia de viento proyectado
        # Efecto amplificador: deshielo genera gradiente de temperatura
        amp_deshielo = 1.0 + (deshielo / 150)
        # Orografía: latitudes entre -35 y -55 son el corredor patagónico
        amp_orografico = 1.2 if (-55 < c["lat"] < -35) else 1.0

        viento_pred_base = viento * amp_deshielo * amp_orografico

        if viento_pred_base < 30:
            continue  # Sin potencial de alerta

        for dias, trend in [(1, 1.05), (3, 1.12), (5, 0.95)]:
            v_dia = round(viento_pred_base * trend, 1)
            intensidad = _clip((v_dia / 120) * 100)

            if v_dia > 80:
                color = "#94a3b8"
                es_alerta = True
                nivel = "EXTREMO"
            elif v_dia > 55:
                color = "#cbd5e1"
                es_alerta = True
                nivel = "FUERTE"
            elif v_dia > 35:
                color = "#e2e8f0"
                es_alerta = False
                nivel = "MODERADO"
            else:
                continue

            predicciones.append({
                "tipo": "viento_extremo",
                "lat": round(c["lat"] + 0.05 * dias, 4),
                "lon": round(c["lon"] + 0.05 * dias, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": (
                    f"🤖 Mirofish Viento — {nivel}: {v_dia:.0f}km/h proyectados. "
                    f"{'Mar' if is_mar else 'Continental'} — "
                    f"Amp. orográfica {amp_orografico:.1f}x, Amp. deshielo {amp_deshielo:.2f}x."
                ),
                "color_hex": color,
                "es_alerta": es_alerta,
                "viento_pred": v_dia,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 3 — Anomalía Térmica (Mirofish)
# Alimenta el filtro: Anomalías de Temperatura
# ---------------------------------------------------------------------------
def agente_temperatura_anomalia(datos_clima: list) -> list:
    """
    Proyecta anomalías térmicas usando la tendencia observada en los 7 días
    de histórico vs. el promedio histórico patagónico regional.
    
    Promedios históricos de referencia (25 años):
    - Patagonia Norte (lat > -45): 12°C verano / 4°C invierno ≈ 8°C anual
    - Patagonia Sur  (lat < -45): 8°C verano / 0°C invierno ≈ 4°C anual
    - Subantártica   (lat < -55): 3°C en verano, < 0°C en invierno ≈ 1°C
    """
    PROMEDIOS = {
        "norte":  8.0,   # lat > -45
        "sur":    4.0,   # -55 < lat <= -45
        "antartica": 1.0 # lat <= -55
    }

    predicciones = []
    procesados = set()

    for c in datos_clima:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        temp = c.get("temperatura", 999)
        if temp == 999:
            continue

        # Seleccionar promedio histórico de referencia
        if c["lat"] > -45:
            ref = PROMEDIOS["norte"]
        elif c["lat"] > -55:
            ref = PROMEDIOS["sur"]
        else:
            ref = PROMEDIOS["antartica"]

        anomalia = temp - ref  # positiva = más caliente que lo normal

        # Solo generar predicción si hay anomalía significativa
        if abs(anomalia) < 2.5:
            continue

        for dias in [1, 3, 5]:
            # La anomalía tiende a persistir 70% por cada 2 días
            decay = 0.85 ** (dias / 2)
            anomalia_pred = round(anomalia * decay, 1)

            if abs(anomalia_pred) < 1.5:
                continue

            temp_pred = round(ref + anomalia_pred, 1)
            intensidad = _clip(abs(anomalia_pred) * 10)

            if anomalia_pred > 0:
                color = "#f97316" if anomalia_pred > 5 else "#fb923c"
                es_alerta = anomalia_pred > 7
                signo = "+"
            else:
                color = "#3b82f6" if anomalia_pred < -5 else "#60a5fa"
                es_alerta = anomalia_pred < -7
                signo = ""

            predicciones.append({
                "tipo": "temperatura_anomalia",
                "lat": round(c["lat"], 4),
                "lon": round(c["lon"], 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": (
                    f"🤖 Mirofish Térmico — Anomalía {signo}{anomalia_pred}°C "
                    f"(ref. histórica: {ref}°C). T° estimada: {temp_pred}°C. "
                    f"{'⚠️ Anomalía severa.' if es_alerta else 'Monitoreo recomendado.'}"
                ),
                "color_hex": color,
                "es_alerta": es_alerta,
                "temperatura_pred": temp_pred,
                "anomalia": anomalia_pred,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 4 — Deshielo Acelerado (Mirofish)
# Alimenta el filtro: Deshielo Marítimo
# ---------------------------------------------------------------------------
def agente_deshielo_pred(datos_clima: list) -> list:
    """
    Proyecta aceleración del deshielo marítimo cuando:
    - Temperatura > 0°C en zonas subantárticas
    - Temperatura en ascenso vs. promedio del período
    - Viento < 20 km/h (ausencia de mezcla = calentamiento superficial)
    """
    predicciones = []
    mar, _ = _split_clima(datos_clima)
    procesados = set()

    for c in mar:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        temp = c.get("temperatura", -10)
        deshielo_actual = c.get("deshielo_maritimo", 0)
        viento = c.get("viento", 20)

        if deshielo_actual <= 0 and temp <= -1:
            continue

        # Factor de aceleración térmica
        factor_temp = max(0, (temp + 2) * 0.08)
        # Calma superficial aumenta fusión
        factor_calma = 1.0 if viento > 20 else 1.3
        # Retroalimentación: más deshielo = más agua oscura = más absorción solar
        factor_albedo = 1.0 + (deshielo_actual / 200)

        for dias in [2, 4, 6]:
            deshielo_pred = _clip(
                deshielo_actual * (1 + factor_temp * factor_calma * factor_albedo) ** (dias / 2),
                0, 200
            )
            delta = round(deshielo_pred - deshielo_actual, 1)
            intensidad = _clip((deshielo_pred / 120) * 100)

            if delta < 2 and deshielo_pred < 5:
                continue

            es_alerta = deshielo_pred > 50 or delta > 20

            predicciones.append({
                "tipo": "deshielo_pred",
                "lat": round(c["lat"], 4),
                "lon": round(c["lon"], 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": (
                    f"🤖 Mirofish Deshielo — Proyección +{dias}d: {deshielo_pred:.0f} "
                    f"(actual {deshielo_actual:.0f}, Δ{'+' if delta>=0 else ''}{delta}). "
                    f"T°:{temp}°C, Viento:{viento:.0f}km/h. "
                    f"{'🚨 Aceleración significativa.' if es_alerta else 'Tendencia moderada.'}"
                ),
                "color_hex": "#06b6d4" if not es_alerta else "#0284c7",
                "es_alerta": es_alerta,
                "deshielo_pred": deshielo_pred,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 5 — Sequía Hídrica (Mirofish)
# Alimenta el filtro: Pérdida Agua Dulce
# ---------------------------------------------------------------------------
def agente_sequia_pred(datos_clima: list) -> list:
    """
    Proyecta el estrés hídrico combinando:
    - Temperatura en ascenso → mayor evapotranspiración
    - Precipitación baja → sin recarga de acuíferos
    - Viento > 40 km/h → acelera pérdida de humedad superficial
    
    Índice de Sequía Proyectado (ISP):
    ISP = (T_pred * 1.5) - (precip_esperada * 2) + (viento_factor * 5)
    """
    predicciones = []
    _, cont = _split_clima(datos_clima)
    procesados = set()

    for c in cont:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        temp = c.get("temperatura", 0)
        precip = c.get("precipitacion", 5)
        viento = c.get("viento", 0)
        agua_dulce = c.get("agua_dulce", 0)

        if agua_dulce < 5 and temp < 20 and precip > 3:
            continue  # Sin señal de sequía

        for dias in [2, 4, 7]:
            # Temperatura proyectada con leve calentamiento estacional
            temp_pred = temp + (0.2 * dias)
            # Precipitación proyectada: persist 60% de la tendencia actual
            precip_pred = max(0, precip * (0.7 ** (dias / 3)))
            # Viento factor (>40 acelera la sequía)
            viento_factor = max(0, (viento - 40) / 40)

            isp = _clip((temp_pred * 1.5) - (precip_pred * 2) + (viento_factor * 5))

            if isp < 8:
                continue

            es_alerta = isp > 35
            color = "#b45309" if es_alerta else "#d97706"

            predicciones.append({
                "tipo": "sequia_pred",
                "lat": round(c["lat"], 4),
                "lon": round(c["lon"], 4),
                "fecha": _fecha_futura(dias),
                "intensidad": isp,
                "descripcion": (
                    f"🤖 Mirofish Sequía — ISP proyectado: {isp:.1f} (+{dias}d). "
                    f"T°pred: {temp_pred:.1f}°C, Precip.pred: {precip_pred:.1f}mm, "
                    f"Viento: {viento:.0f}km/h. "
                    f"{'🚨 Déficit hídrico crítico.' if es_alerta else 'Estrés hídrico moderado.'}"
                ),
                "color_hex": color,
                "es_alerta": es_alerta,
                "isp": isp,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 6 — Tsunami Compuesto (Mirofish)
# Alimenta el filtro: Riesgo Tsunami
# ---------------------------------------------------------------------------
def agente_tsunami_compuesto(datos_clima: list, sismos_recientes: list) -> list:
    """
    Modelo multi-factor de Mirofish para riesgo de tsunami:
    
    Evento tipo A — Tsunamigénico clásico:
      Sismo M >= 6.0 en profundidad < 80km + zona de subducción conocida
    
    Evento tipo B — Tsunami glaciar (Fjord):
      Deshielo acelerado > 40 + Sismo cercano M >= 4.5 + Viento < 20 km/h
      (masa de hielo se desprende y genera ola en fiordo)
    
    Evento tipo C — Megadeslizamiento submarino:
      Sismo M >= 5.5 + Talud continental (lat entre -38 y -55) + prof < 100km
    """
    predicciones = []
    mar, _ = _split_clima(datos_clima)

    for falla in FALLAS_REGIONALES:
        sismos_cercanos = [
            s for s in sismos_recientes
            if _dist(s["lat"], s["lon"], falla["lat"], falla["lon"]) < 5
        ]

        if not sismos_cercanos:
            continue

        sismo_max = max(sismos_cercanos, key=lambda s: s["magnitud"])
        mag = sismo_max["magnitud"]
        prof = sismo_max.get("profundidad", 50)

        clima_cercano = _nearest(falla["lat"], falla["lon"], mar) if mar else None

        # TIPO A — Tsunamigénico clásico
        tipo_a = mag >= 6.0 and prof < 80
        # TIPO C — Megadeslizamiento
        tipo_c = (mag >= 5.5 and prof < 100 and -55 < falla["lat"] < -38)
        # TIPO B — Glaciar
        deshielo = clima_cercano.get("deshielo_maritimo", 0) if clima_cercano else 0
        viento_local = clima_cercano.get("viento", 30) if clima_cercano else 30
        tipo_b = (mag >= 4.5 and deshielo > 40 and viento_local < 20)

        if not (tipo_a or tipo_b or tipo_c):
            continue

        tipo_str = []
        if tipo_a: tipo_str.append("Tsunamigénico M≥6")
        if tipo_b: tipo_str.append("Tsunami Glaciar")
        if tipo_c: tipo_str.append("Megadeslizamiento Submarino")

        intensidad = _clip(
            (50 if tipo_a else 0) +
            (40 if tipo_b else 0) +
            (35 if tipo_c else 0) +
            (mag - 5) * 15
        )
        es_alerta = tipo_a or (tipo_b and tipo_c)

        for dias in [0, 1, 2]:
            predicciones.append({
                "tipo": "tsunami_compuesto",
                "lat": round(falla["lat"] + 0.1 * dias, 4),
                "lon": round(falla["lon"] - 0.05 * dias, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": (
                    f"🤖 Mirofish Tsunami — {falla['name']}: "
                    f"{', '.join(tipo_str)}. M{mag} prof.{prof:.0f}km. "
                    f"{'Deshielo: '+str(int(deshielo)) if tipo_b else ''}"
                    f"{'🚨 ALERTA COMPUESTA.' if es_alerta else '⚠️ Monitoreo activo.'}"
                ),
                "color_hex": "#0369a1" if es_alerta else "#0284c7",
                "es_alerta": es_alerta,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 7 — Incendios Proyectados (Mirofish)
# Alimenta el filtro: Riesgo Incendios
# ---------------------------------------------------------------------------
def agente_incendios_pred(datos_clima: list) -> list:
    """
    Proyecta propagación de riesgo de incendio usando el Índice de Peligro
    de Incendio (IPI) de Mirofish:

    IPI = (T° - 15) * 3 + max(0, agua_dulce - 10) * 1.5 + max(0, viento - 30) * 0.8
    
    IPI > 40 → Alerta Naranja  
    IPI > 65 → Alerta Roja
    
    Factor de propagación: el viento desplaza el frente de fuego 
    ~2° en dirección E por cada 50km/h.
    """
    predicciones = []
    _, cont = _split_clima(datos_clima)
    procesados = set()

    for c in cont:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        temp = c.get("temperatura", 0)
        agua_dulce = c.get("agua_dulce", 0)
        viento = c.get("viento", 0)
        precip = c.get("precipitacion", 5)

        # Mojedad reciente inhibe incendio
        if precip > 10:
            continue

        ipi = (max(0, temp - 15) * 3 +
               max(0, agua_dulce - 10) * 1.5 +
               max(0, viento - 30) * 0.8)

        if ipi < 20:
            continue

        for dias in [1, 3, 5]:
            # La sequía se profundiza y el riesgo aumenta
            temp_pred = temp + 0.3 * dias
            agua_pred = agua_dulce + 2 * dias
            ipi_pred = _clip(
                max(0, temp_pred - 15) * 3 +
                max(0, agua_pred - 10) * 1.5 +
                max(0, viento - 30) * 0.8
            )

            # Desplazamiento del frente de riesgo en dirección del viento (E)
            lon_shift = (viento / 50) * 0.3 * dias

            if ipi_pred < 25:
                continue

            if ipi_pred > 65:
                color = "#dc2626"
                es_alerta = True
                nivel = "ROJA 🔥"
            elif ipi_pred > 40:
                color = "#ea580c"
                es_alerta = True
                nivel = "NARANJA 🔥"
            else:
                color = "#f59e0b"
                es_alerta = False
                nivel = "AMARILLA ⚡"

            predicciones.append({
                "tipo": "incendios_pred",
                "lat": round(c["lat"], 4),
                "lon": round(c["lon"] + lon_shift, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": _clip(ipi_pred),
                "descripcion": (
                    f"🤖 Mirofish Incendio — Alerta {nivel}: IPI {ipi_pred:.1f}. "
                    f"T°pred:{temp_pred:.1f}°C, Sequía:{agua_pred:.1f}, "
                    f"Viento:{viento:.0f}km/h (+{dias}d)."
                ),
                "color_hex": color,
                "es_alerta": es_alerta,
                "ipi": ipi_pred,
            })

    return predicciones


# ===========================================================================
# AGENTES PROPIOS MIROFISH (pesca / marina)
# ===========================================================================

# ---------------------------------------------------------------------------
# AGENTE 8 — Cardumen
# ---------------------------------------------------------------------------
def agente_cardumen(datos_clima: list) -> list:
    predicciones = []
    mar, _ = _split_clima(datos_clima)
    procesados = set()

    for c in mar:
        clave = (round(c["lat"], 1), round(c["lon"], 1))
        if clave in procesados:
            continue
        procesados.add(clave)

        temp = c.get("temperatura", 999)
        viento = c.get("viento", 0)

        factor_viento = max(0.0, 1.0 - (max(0, viento - 40) / 60))

        if -2 <= temp <= 8:
            intensidad = _clip((8 - temp) * 10 * factor_viento)
            especie = "Merluza / Calamar (Aguas Frías)"
            color = "#22d3ee"
        elif 8 < temp <= 14:
            intensidad = _clip((temp - 8) * 12 * factor_viento)
            especie = "Langostino Patagónico (Zona Convergencia)"
            color = "#f59e0b"
        else:
            continue

        if intensidad < 15:
            continue

        for dias in [1, 3, 5]:
            lat_adj = c["lat"] - (0.1 * dias)
            lon_adj = c["lon"] + (0.05 * dias)

            predicciones.append({
                "tipo": "cardumen",
                "lat": round(lat_adj, 4),
                "lon": round(lon_adj, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": f"Zona probable: {especie} — Densidad estimada {intensidad:.0f}%",
                "color_hex": color,
                "es_alerta": False,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 9 — Corrientes (Malvinas)
# ---------------------------------------------------------------------------
def agente_corrientes(datos_clima: list) -> list:
    predicciones = []
    mar, _ = _split_clima(datos_clima)

    temp_norte, temp_sur = None, None
    for c in mar:
        if c["lat"] > -46 and temp_norte is None:
            temp_norte = c.get("temperatura", 10)
        if c["lat"] < -58 and temp_sur is None:
            temp_sur = c.get("temperatura", 0)

    temp_norte = temp_norte or 10.0
    temp_sur = temp_sur or 1.0
    gradiente = abs(temp_norte - temp_sur)
    velocidad_base = _clip(gradiente * 5, 10, 80)

    for i, nodo in enumerate(CORRIENTE_MALVINAS):
        for dias in [1, 3, 5]:
            lat_adj = nodo["lat"] + (0.33 * dias)
            lon_adj = nodo["lon"] + (0.1 * dias)
            vel_local = _clip(velocidad_base + (i * 3))

            predicciones.append({
                "tipo": "corriente",
                "lat": round(lat_adj, 4),
                "lon": round(lon_adj, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": vel_local,
                "descripcion": (
                    f"Corriente de Malvinas — Nodo {i+1}/6 — "
                    f"Vel. est.: {vel_local:.0f} km/h — "
                    f"Gradiente: {gradiente:.1f}°C"
                ),
                "color_hex": "#818cf8",
                "es_alerta": vel_local > 65,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 10 — Alerta Pesca
# ---------------------------------------------------------------------------
def agente_alerta_pesca(datos_clima: list, sismos_recientes: list) -> list:
    predicciones = []
    sismos_fuertes = [s for s in sismos_recientes if s.get("magnitud", 0) >= 5.0]

    for punto in PUNTOS_MARITIMOS:
        clim = _nearest(punto["lat"], punto["lon"], datos_clima)
        if not clim:
            continue

        viento = clim.get("viento", 0)
        deshielo = clim.get("deshielo_maritimo", 0)
        sismo_cercano = any(
            _dist(s["lat"], s["lon"], punto["lat"], punto["lon"]) < 5
            for s in sismos_fuertes
        )

        if viento > 70 and (deshielo > 30 or sismo_cercano):
            color = "#ef4444"; es_alerta = True
            descripcion = (
                f"⛔ ALERTA ROJA PESCA: Viento {viento:.0f}km/h + "
                f"{'Sismo + ' if sismo_cercano else ''}"
                f"Deshielo {deshielo:.0f} — NO NAVEGAR — {punto['name']}"
            )
        elif viento > 55:
            color = "#f97316"; es_alerta = True
            descripcion = f"⚠️ ALERTA NARANJA: Viento {viento:.0f}km/h — Precaución en {punto['name']}"
        elif viento > 40:
            color = "#eab308"; es_alerta = False
            descripcion = f"⚡ Precaución: Viento {viento:.0f}km/h — {punto['name']}"
        else:
            continue

        intensidad = _clip((viento / 80) * 100)
        for dias in [0, 1, 2, 3]:
            predicciones.append({
                "tipo": "alerta_pesca",
                "lat": round(punto["lat"] + 0.05 * dias, 4),
                "lon": round(punto["lon"] + 0.05 * dias, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": descripcion,
                "color_hex": color,
                "es_alerta": es_alerta,
            })

    return predicciones


# ---------------------------------------------------------------------------
# AGENTE 11 — Bio-Riesgo Marino (Marea Roja)
# ---------------------------------------------------------------------------
def agente_bio_riesgo(datos_clima: list) -> list:
    predicciones = []
    zonas = [
        {"name": "Canal Beagle",           "lat": -55.0, "lon": -68.0},
        {"name": "Estrecho de Magallanes", "lat": -53.5, "lon": -70.5},
        {"name": "Bahía Ushuaia",          "lat": -54.8, "lon": -68.3},
        {"name": "Bahía San Sebastián",    "lat": -53.2, "lon": -68.5},
        {"name": "Canal Beagle Oeste",     "lat": -55.0, "lon": -70.5},
        {"name": "Mar Argentino Austral",  "lat": -53.0, "lon": -62.0},
    ]

    for zona in zonas:
        clim = _nearest(zona["lat"], zona["lon"], datos_clima)
        if not clim:
            continue

        temp = clim.get("temperatura", 0)
        deshielo = clim.get("deshielo_maritimo", 0)
        viento = clim.get("viento", 999)
        precip = clim.get("precipitacion", 999)

        score = sum([
            8 <= temp <= 18,
            deshielo > 5,
            viento < 30,
            precip < 3,
        ])

        if score < 2:
            continue

        intensidad = _clip(score * 25)
        if score >= 4:
            color = "#10b981"; es_alerta = True
            descripcion = (
                f"🟢 MAREA ROJA CRÍTICA — {zona['name']}: "
                f"T°{temp:.1f}°C, Deshielo {deshielo:.0f}. Prohibición mariscos recomendada."
            )
        elif score == 3:
            color = "#34d399"; es_alerta = True
            descripcion = f"⚠️ Riesgo Marea Roja — {zona['name']}: T°{temp:.1f}°C — Monitoreo activo."
        else:
            color = "#6ee7b7"; es_alerta = False
            descripcion = f"Condición HAB baja — {zona['name']}: T°{temp:.1f}°C — Sin alerta."

        for dias in [0, 2, 4, 6]:
            predicciones.append({
                "tipo": "bio_riesgo",
                "lat": round(zona["lat"] + 0.03 * dias, 4),
                "lon": round(zona["lon"] + 0.02 * dias, 4),
                "fecha": _fecha_futura(dias),
                "intensidad": intensidad,
                "descripcion": descripcion,
                "color_hex": color,
                "es_alerta": es_alerta,
            })

    return predicciones


# ===========================================================================
# Punto de entrada — ejecuta los 11 agentes
# ===========================================================================

def generar_predicciones_mirofish(datos_clima: list, sismos_recientes: list) -> list:
    """
    Ejecuta los 11 agentes Mirofish y devuelve lista unificada.
    datos_clima debe incluir puntos continentales Y marítimos.
    """
    resultados = []

    # Agentes para capas existentes
    resultados += agente_sismico_pred(sismos_recientes)
    resultados += agente_viento_extremo(datos_clima)
    resultados += agente_temperatura_anomalia(datos_clima)
    resultados += agente_deshielo_pred(datos_clima)
    resultados += agente_sequia_pred(datos_clima)
    resultados += agente_tsunami_compuesto(datos_clima, sismos_recientes)
    resultados += agente_incendios_pred(datos_clima)

    # Agentes propios Mirofish (pesca/marina)
    resultados += agente_cardumen(datos_clima)
    resultados += agente_corrientes(datos_clima)
    resultados += agente_alerta_pesca(datos_clima, sismos_recientes)
    resultados += agente_bio_riesgo(datos_clima)

    return resultados
