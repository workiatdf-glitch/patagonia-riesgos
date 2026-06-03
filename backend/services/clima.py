import requests
from datetime import datetime, timedelta

def fetch_clima_openmeteo(lat=-52.0, lon=-70.0, is_maritime=False):
    """
    Obtiene el clima histórico reciente (últimos 7 días) y pronóstico (7 días).
    Calcula índices proxy heurísticos diferenciando ecosistemas continentales y marítimos.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "snowfall_sum", "wind_speed_10m_max"],
        "past_days": 7,
        "forecast_days": 8,
        "timezone": "America/Argentina/Ushuaia"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Error fetching Open-Meteo: {e}")
        return []
        
    daily = data.get('daily', {})
    if not daily:
        return []

    fechas = daily.get('time', [])
    temp_max = daily.get('temperature_2m_max', [])
    precip = daily.get('precipitation_sum', [])
    snow = daily.get('snowfall_sum', [])
    wind = daily.get('wind_speed_10m_max', [])

    resultados = []
    hoy_date = datetime.utcnow().date()
    
    for i, f_str in enumerate(fechas):
        fecha_obj = datetime.fromisoformat(f_str).date()
        
        t_max = temp_max[i] if temp_max[i] is not None else 0
        p = precip[i] if precip[i] is not None else 0
        w = wind[i] if wind[i] is not None else 0
        s = snow[i] if snow[i] is not None else 0
        
        if is_maritime:
            # En el mar / zonas glaciares, cualquier temp > 0 castiga el hielo marino
            deshielo_idx = max(0, (t_max + 1) * 6)
            sequia_idx = 0 # No aplica sequía continental en pleno mar
        else:
            deshielo_idx = 0 # Continental no reporta deshielo marítimo masivo
            
            # Heurística para "Agua Dulce / Sequía" continental:
            # Estrés térmico frente a escasez de lluvias.
            sequia_idx = max(0, (t_max * 1.5) - (p * 1.5))
            
        resultados.append({
            "fecha": f_str + "T12:00:00Z",
            "lat": lat,
            "lon": lon,
            "temperatura": round(t_max, 1),
            "precipitacion": round(p, 1),
            "viento": round(w, 1),
            "deshielo_maritimo": round(deshielo_idx, 1),
            "agua_dulce": round(sequia_idx, 1),
            "es_pronostico": fecha_obj > hoy_date
        })
        
    return resultados

def procesar_promedios_historicos(lat, lon):
    """
    Simulación del crón de 25 años troncales.
    """
    return {
        "temp_promedio_historica": 5.0, # Patagónico promedio 
        "precip_promedio_historica": 2.5
    }
