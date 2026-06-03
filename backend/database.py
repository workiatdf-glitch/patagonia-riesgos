import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, DateTime, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from geoalchemy2 import Geometry

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://patagonia_user:patagonia_password@db:5432/patagonia_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class SismoAct(Base):
    __tablename__ = "sismos_act"
    id = Column(Integer, primary_key=True, index=True)
    origen = Column(String, index=True)
    magnitud = Column(Float)
    profundidad = Column(Float)
    fecha = Column(DateTime)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    clasificacion = Column(String)
    es_prediccion = Column(Boolean, default=False)
    alerta_tsunami = Column(Boolean, default=False)

class ClimaAct(Base):
    __tablename__ = "clima_act"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True))
    geom = Column(Geometry('POINT', srid=4326))
    temperatura = Column(Numeric(5, 2))
    precipitacion = Column(Numeric(5, 2))
    viento = Column(Numeric(5, 2))
    deshielo_maritimo = Column(Numeric(5, 2))
    agua_dulce = Column(Numeric(5, 2))
    es_pronostico = Column(Boolean, default=False)

class MirofishAct(Base):
    __tablename__ = "mirofish_act"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True)       # cardumen | corriente | alerta_pesca | bio_riesgo
    descripcion = Column(Text)
    intensidad = Column(Float)
    fecha = Column(DateTime(timezone=True))
    geom = Column(Geometry('POINT', srid=4326))
    es_alerta = Column(Boolean, default=False)
    color_hex = Column(String(10))
