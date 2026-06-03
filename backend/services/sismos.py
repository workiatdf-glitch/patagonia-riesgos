import requests
from datetime import datetime, timedelta

def clasificar_sismo(mag: float) -> str:
    if mag < 4:
        return 'Bajo'
    elif mag < 6:
        return 'Moderado'
    return 'Fuerte'

def fetch_sismos_usgs():
    """
    Descarga sismos de los últimos 7 días en el área de Sudamérica y Patagonia.
    """
    now = datetime.utcnow()
    past = now - timedelta(days=7)
    
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": past.strftime("%Y-%m-%d"),
        "endtime": now.strftime("%Y-%m-%d"),
        "minlatitude": -75,
        "maxlatitude": -15,
        "minlongitude": -85,
        "maxlongitude": -35
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Error fetching USGS: {e}")
        return []
        
    resultados = []
    for feature in data.get('features', []):
        props = feature['properties']
        geom = feature['geometry']
        mag = props.get('mag', 0)
        
        # Clasificar sismo: <4 Bajo, 4-6 Moderado, >6 Fuerte / Alerta
        if mag is None:
            continue
            
        if mag < 4:
            clasificacion = 'Bajo'
        elif mag < 6:
            clasificacion = 'Moderado'
        else:
            clasificacion = 'Fuerte'
        
        depth = geom['coordinates'][2]
        lon = geom['coordinates'][0]
        lat = geom['coordinates'][1]
        fecha_iso = datetime.utcfromtimestamp(props['time'] / 1000.0).isoformat() + "Z"
            
        # Evaluar Tsunami Oficial
        tsunami_flag = bool(props.get("tsunami", 0))

        resultados.append({
            "origen": "USGS Oficial",
            "lat": lat,
            "lon": lon,
            "magnitud": round(mag, 1),
            "profundidad": round(depth, 2),
            "fecha": fecha_iso,
            "clasificacion": clasificacion,
            "alerta_tsunami": tsunami_flag
        })
        
    return resultados

def generar_predicciones_sismicas(sismos_recientes):
    """
    Motor heurístico que lee eventos fuertes (>5.0) en los últimos 7 días y proyecta 
    posibles 'réplicas' o transferencias de tensión en extremidades de la placa para los próximos 7 días.
    """
    predicciones = []
    fuertes = [s for s in sismos_recientes if s['magnitud'] >= 5.0]
    
    hoy = datetime.utcnow()
    
    for s in fuertes:
        # Heurística: Réplica estimativa a 3 días
        nueva_fecha = hoy + timedelta(days=3)
        nueva_mag = s['magnitud'] - 0.5
        
        # Desplazamiento heurístico leve de lat/lon (tensión de falla)
        nuevo_lat = s['lat'] + 0.2
        nuevo_lon = s['lon'] - 0.4
        
        # Predicción de tsunami basado en réplica superficial
        pred_tsunami = nueva_mag >= 6.5 and s['profundidad'] < 50
        
        predicciones.append({
            "origen": "Alg. Predictivo Placas",
            "lat": nuevo_lat,
            "lon": nuevo_lon,
            "magnitud": round(nueva_mag, 1),
            "profundidad": s['profundidad'],
            "fecha": nueva_fecha.isoformat() + "Z",
            "clasificacion": clasificar_sismo(nueva_mag),
            "alerta_tsunami": pred_tsunami
        })
        
    return predicciones
