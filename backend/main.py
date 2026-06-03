from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import database as db
from services.sismos import fetch_sismos_usgs, generar_predicciones_sismicas
from services.clima import fetch_clima_openmeteo
from services.mirofish import generar_predicciones_mirofish

app = FastAPI(title="Patagonia Riesgos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db.Base.metadata.create_all(bind=db.engine)
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/sync")
def sync_data(session: Session = Depends(get_db)):
    """
    Endpoint de actualización general a demanda (Botón Refresh)
    """
    # Try dynamic schema upgrade for Tsunami Flag
    try:
        session.execute(text("ALTER TABLE sismos_act ADD COLUMN alerta_tsunami BOOLEAN DEFAULT FALSE"))
        session.commit()
    except Exception:
        session.rollback()
        
    sismos_recientes = fetch_sismos_usgs()
    predicciones = generar_predicciones_sismicas(sismos_recientes)
    CITIES = [
        # Patagonia & Antártida (Foco principal)
        {"name": "Ushuaia", "lat": -54.8019, "lon": -68.3030},
        {"name": "Río Grande", "lat": -53.7833, "lon": -67.7000},
        {"name": "Tolhuin", "lat": -54.5111, "lon": -67.1883},
        {"name": "Puerto Argentino", "lat": -51.6921, "lon": -57.8589},
        {"name": "Río Gallegos", "lat": -51.6226, "lon": -69.2181},
        {"name": "Rawson", "lat": -43.3002, "lon": -65.1023},
        {"name": "Viedma", "lat": -40.8135, "lon": -62.9967},
        {"name": "Neuquén", "lat": -38.9516, "lon": -68.0591},
        {"name": "Santa Rosa", "lat": -36.6167, "lon": -64.2833},
        
        # Referencias Nacionales Adicionales (Mesopotamia, NOA, Centro, Cuyo)
        {"name": "Posadas", "lat": -27.3671, "lon": -55.8961},
        {"name": "Corrientes", "lat": -27.4692, "lon": -58.8306},
        {"name": "Paraná", "lat": -31.7319, "lon": -60.5288},
        {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816},
        {"name": "Córdoba", "lat": -31.4201, "lon": -64.1888},
        {"name": "Mendoza", "lat": -32.8908, "lon": -68.8272},
        {"name": "Salta", "lat": -24.7821, "lon": -65.4232}
    ]
    
    session.query(db.SismoAct).delete()
    session.query(db.ClimaAct).delete()
    session.query(db.MirofishAct).delete()
    
    for s in sismos_recientes + predicciones:
        nuevo = db.SismoAct(
            origen=s['origen'],
            magnitud=s['magnitud'],
            profundidad=s['profundidad'],
            fecha=datetime.fromisoformat(s['fecha'].replace('Z', '+00:00')),
            clasificacion=s['clasificacion'],
            geom=f"SRID=4326;POINT({s['lon']} {s['lat']})",
            es_prediccion=(s['origen'] != "USGS Oficial"),
            alerta_tsunami=s['alerta_tsunami']
        )
        session.add(nuevo)
        
    for city in CITIES:
        clima = fetch_clima_openmeteo(lat=city['lat'], lon=city['lon'], is_maritime=False)
        for c in clima:
            nuevo_c = db.ClimaAct(
                fecha=c['fecha'],
                geom=f"SRID=4326;POINT({c['lon']} {c['lat']})",
                temperatura=c['temperatura'],
                precipitacion=c['precipitacion'],
                viento=c['viento'],
                deshielo_maritimo=c['deshielo_maritimo'],
                agua_dulce=c['agua_dulce'],
                es_pronostico=c['es_pronostico']
            )
            session.add(nuevo_c)
            
    SEA_POINTS = [
        {"name": "Pasaje de Drake", "lat": -59.5, "lon": -64.0},
        {"name": "Mar Argentino Austral", "lat": -53.0, "lon": -62.0},
        {"name": "Islas Orcadas del Sur", "lat": -60.7, "lon": -45.0},
        {"name": "Estrecho de Magallanes", "lat": -53.5, "lon": -70.5},
        {"name": "Mar de Weddell", "lat": -64.0, "lon": -45.0},
        {"name": "Península Antártica", "lat": -65.0, "lon": -60.0}
    ]
            
    for sea in SEA_POINTS:
        clima_mar = fetch_clima_openmeteo(lat=sea['lat'], lon=sea['lon'], is_maritime=True)
        for c in clima_mar:
            nuevo_c = db.ClimaAct(
                fecha=c['fecha'],
                geom=f"SRID=4326;POINT({c['lon']} {c['lat']})",
                temperatura=c['temperatura'],
                precipitacion=c['precipitacion'],
                viento=c['viento'],
                deshielo_maritimo=c['deshielo_maritimo'],
                agua_dulce=c['agua_dulce'],
                es_pronostico=c['es_pronostico']
            )
            session.add(nuevo_c)
            
    session.commit()

    # --- Agentes Mirofish ---
    # Recolectar datos climáticos: marítimos + continentales para todos los agentes
    todos_clima = []

    # Puntos marítimos
    for sea in [
        {"lat": -59.5, "lon": -64.0}, {"lat": -53.0, "lon": -62.0},
        {"lat": -60.7, "lon": -45.0}, {"lat": -53.5, "lon": -70.5},
        {"lat": -64.0, "lon": -45.0}, {"lat": -65.0, "lon": -60.0},
        {"lat": -54.5, "lon": -59.0}, {"lat": -55.0, "lon": -68.0},
    ]:
        todos_clima += fetch_clima_openmeteo(lat=sea["lat"], lon=sea["lon"], is_maritime=True)

    # Puntos continentales (para agentes de viento, temperatura, sequía, incendios)
    for city in [
        {"lat": -54.8,  "lon": -68.3},
        {"lat": -53.78, "lon": -67.7},
        {"lat": -51.62, "lon": -69.22},
        {"lat": -43.3,  "lon": -65.1},
        {"lat": -40.81, "lon": -62.99},
        {"lat": -38.95, "lon": -68.06},
        {"lat": -36.62, "lon": -64.28},
        {"lat": -32.89, "lon": -68.83},
        {"lat": -31.42, "lon": -64.19},
        {"lat": -24.78, "lon": -65.42},
    ]:
        todos_clima += fetch_clima_openmeteo(lat=city["lat"], lon=city["lon"], is_maritime=False)

    predicciones_mirofish = generar_predicciones_mirofish(todos_clima, sismos_recientes)

    for m in predicciones_mirofish:
        nuevo_m = db.MirofishAct(
            tipo=m["tipo"],
            descripcion=m["descripcion"],
            intensidad=m["intensidad"],
            fecha=datetime.fromisoformat(m["fecha"].replace("Z", "+00:00")),
            geom=f"SRID=4326;POINT({m['lon']} {m['lat']})",
            es_alerta=m["es_alerta"],
            color_hex=m["color_hex"],
        )
        session.add(nuevo_m)

    session.commit()
    return {
        "message": "Sincronización completa",
        "sismos_count": len(sismos_recientes),
        "pred_sismos": len(predicciones),
        "pred_mirofish": len(predicciones_mirofish),
    }

@app.get("/api/sismos")
def get_sismos(session: Session = Depends(get_db)):
    query = session.execute(
        text("SELECT id, origen, magnitud, profundidad, fecha, clasificacion, es_prediccion, alerta_tsunami, ST_X(geom) as lon, ST_Y(geom) as lat FROM sismos_act")
    )
    return [dict(row._mapping) for row in query]

@app.get("/api/clima")
def get_clima(session: Session = Depends(get_db)):
    query = session.execute(
        text("SELECT id, fecha, temperatura, precipitacion, viento, deshielo_maritimo, agua_dulce, es_pronostico, ST_X(geom) as lon, ST_Y(geom) as lat FROM clima_act ORDER BY fecha ASC")
    )
    return [dict(row._mapping) for row in query]

@app.get("/api/mirofish")
def get_mirofish(session: Session = Depends(get_db)):
    """
    Retorna todas las predicciones de los agentes Mirofish:
    cardumen, corriente, alerta_pesca, bio_riesgo
    """
    query = session.execute(
        text(
            "SELECT id, tipo, descripcion, intensidad, fecha, es_alerta, color_hex, "
            "ST_X(geom) as lon, ST_Y(geom) as lat FROM mirofish_act ORDER BY fecha ASC"
        )
    )
    return [dict(row._mapping) for row in query]
