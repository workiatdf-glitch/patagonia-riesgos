import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import L from 'leaflet'

// Fix default icons if we ever use standard markers
delete L.Icon.Default.prototype._getIconUrl;

const CenterMap = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { animate: true, duration: 1.5 });
  }, [center, zoom, map]);
  return null;
}

export default function MapComponent({ 
  sismos, 
  clima,
  mirofish,
  filtros, 
  timelineIndex, 
  center 
}) {
  
  // Custom pulsing marker logic using Leaflet DivIcon for alerts
  const createPulseIcon = (color) => L.divIcon({
    className: 'custom-pulse-div-icon',
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; box-shadow: 0 0 15px ${color}; animation: pulse 2s infinite;"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  // Calcular la fecha objetivo según el timelineIndex
  const targetDate = new Date();
  targetDate.setDate(targetDate.getDate() + timelineIndex);
  const targetDateString = targetDate.toISOString().split('T')[0];

  // Filtrar eventos por el dia seleccionado en la Linea de Tiempo
  const shownSismos = sismos.filter(s => {
    if (!filtros.sismos) return false;
    // Mostrar sismos de los últimos 30 días si no coinciden con el día específico
    const sismoDate = new Date(s.fecha);
    const daysDiff = Math.floor((new Date() - sismoDate) / (1000 * 60 * 60 * 24));
    return s.fecha.startsWith(targetDateString) || daysDiff <= 30;
  });

  const shownClima = clima.filter(c => {
    // Mostrar clima de los últimos 7 días
    const climaDate = new Date(c.fecha);
    const daysDiff = Math.floor((new Date() - climaDate) / (1000 * 60 * 60 * 24));
    return c.fecha.startsWith(targetDateString) || daysDiff <= 7;
  });

  // Filtrar predicciones Mirofish por día seleccionado
  const shownMirofish = (mirofish || []).filter(m =>
    m.fecha && m.fecha.startsWith(targetDateString)
  );

  // Helper para buscar el nodo climático más cercano a un punto
  const getNearestClima = (lat, lon) => {
    if (!shownClima.length) return null;
    return shownClima.reduce((prev, curr) => {
      const distPrev = Math.abs(prev.lat - lat) + Math.abs(prev.lon - lon);
      const distCurr = Math.abs(curr.lat - lat) + Math.abs(curr.lon - lon);
      return distCurr < distPrev ? curr : prev;
    });
  };

  return (
    <MapContainer 
      center={[-50.0, -70.0]} 
      zoom={5} 
      style={{ height: "100%", width: "100%", zIndex: 0 }}
      zoomControl={false}
    >
      <TileLayer
        url="https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{-y}.png"
        attribution='&copy; <a href="https://www.ign.gob.ar/">Instituto Geográfico Nacional (IGN) - Rep. Argentina</a>'
      />
      <CenterMap center={center} zoom={5} />

      {/* Sismos — Datos USGS reales */}
      {filtros.sismos && shownSismos.map((s, i) => {
        const color = s.clasificacion === 'Fuerte' ? '#ef4444' : s.clasificacion === 'Moderado' ? '#f59e0b' : '#3b82f6';
        const radius = s.magnitud * 3;
        return (
          <CircleMarker
            key={'s'+i}
            center={[s.lat, s.lon]}
            radius={radius}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.6 }}
          >
            <Tooltip permanent direction="right" className="font-bold text-sm bg-white/90 border-0 shadow-lg">
              M{s.magnitud}
            </Tooltip>
            <Popup className="bg-slate-800 text-white border-0 rounded-xl">
              <div className="p-2">
                <h3 className="font-bold text-lg mb-1">{s.es_prediccion ? 'Predicción Sísmica' : 'Sismo Real'}</h3>
                <p><strong>Magnitud:</strong> {s.magnitud}</p>
                <p><strong>Clase:</strong> {s.clasificacion}</p>
                <p><strong>Profundidad:</strong> {s.profundidad} km</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(s.fecha).toLocaleString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
      {/* Sismos — Predicciones Mirofish */}
      {filtros.sismos && shownMirofish
        .filter(m => m.tipo === 'sismico_pred')
        .map((m, i) => {
          const radius = (m.magnitud || 4) * 3;
          return (
            <CircleMarker
              key={'mf_sis'+i}
              center={[m.lat, m.lon]}
              radius={radius}
              pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.35, dashArray: '5 4', weight: 2 }}
            >
              <Tooltip permanent direction="left" className="font-bold text-sm bg-white/90 border border-dashed border-slate-400 rounded shadow p-1">
                🤖 M{m.magnitud?.toFixed(1)}
              </Tooltip>
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-base mb-1 text-purple-700">Mirofish — Predicción Sísmica</h3>
                  <p className="text-sm">{m.descripcion}</p>
                  <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })
      }

      {/* Clima: Temperatura — Datos reales */}
      {filtros.temperatura && shownClima.map((c, i) => {
        const color = c.temperatura > 15 ? '#ef4444' : c.temperatura < 5 ? '#3b82f6' : '#22c55e';
        return (
          <CircleMarker key={'temp'+i} center={[c.lat, c.lon]} radius={15} pathOptions={{ color: 'transparent', fillColor: color, fillOpacity: 0.4 }}>
             <Tooltip permanent direction="bottom" className="font-bold text-sm text-slate-800 border-0 bg-white/70 backdrop-blur-sm rounded p-1 shadow-sm">
                T: {c.temperatura}°C
             </Tooltip>
          </CircleMarker>
        )
      })}
      {/* Temperatura — Predicciones Mirofish */}
      {filtros.temperatura && shownMirofish
        .filter(m => m.tipo === 'temperatura_anomalia')
        .map((m, i) => (
          <CircleMarker
            key={'mf_temp'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(10, m.intensidad * 0.2)}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.3, dashArray: '5 3', weight: 2 }}
          >
            <Tooltip permanent direction="top" className="font-bold text-sm bg-white/90 border border-dashed border-orange-300 rounded shadow p-1">
              🤖 {m.anomalia > 0 ? '+' : ''}{m.anomalia}°C
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-orange-600">Mirofish — Anomalía Térmica</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Deshielo Marítimo — Datos reales */}
      {filtros.deshielo && shownClima.map((c, i) => {
        if(c.deshielo_maritimo <= 0) return null;
        return (
          <CircleMarker key={'hielo'+i} center={[c.lat, c.lon]} radius={c.deshielo_maritimo * 2.5} pathOptions={{ color: '#06b6d4', fillOpacity: 0.5, dashArray: '4' }}>
             <Tooltip permanent direction="right" className="font-bold text-sm text-cyan-800 bg-white/70 backdrop-blur-sm rounded p-1 shadow-sm">Deshielo: {c.deshielo_maritimo}</Tooltip>
          </CircleMarker>
        )
      })}
      {/* Deshielo — Predicciones Mirofish */}
      {filtros.deshielo && shownMirofish
        .filter(m => m.tipo === 'deshielo_pred')
        .map((m, i) => (
          <CircleMarker
            key={'mf_hielo'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(8, m.intensidad * 0.35)}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.35, dashArray: '6 3', weight: 2 }}
          >
            <Tooltip permanent direction="left" className="font-bold text-sm bg-white/90 border border-dashed border-cyan-400 rounded shadow p-1">
              🤖 ↑{m.deshielo_pred?.toFixed(0)}
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-cyan-700">Mirofish — Deshielo Proyectado</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }
      
      {/* Sequía / Agua dulce — Datos reales */}
      {filtros.sequia && shownClima.map((c, i) => {
        if(c.agua_dulce <= 0) return null;
        return (
          <CircleMarker key={'agua'+i} center={[c.lat, c.lon]} radius={c.agua_dulce * 1.5} pathOptions={{ color: '#d97706', fillOpacity: 0.5 }}>
             <Tooltip permanent direction="left" className="font-bold text-sm text-amber-700 bg-white/70 backdrop-blur-sm rounded p-1 shadow-sm">Sequía: {c.agua_dulce}</Tooltip>
          </CircleMarker>
        )
      })}
      {/* Sequía — Predicciones Mirofish */}
      {filtros.sequia && shownMirofish
        .filter(m => m.tipo === 'sequia_pred')
        .map((m, i) => (
          <CircleMarker
            key={'mf_sequia'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(8, m.isp * 0.3)}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.3, dashArray: '5 3', weight: 2 }}
          >
            <Tooltip permanent direction="right" className="font-bold text-sm bg-white/90 border border-dashed border-amber-400 rounded shadow p-1">
              🤖 ISP:{m.isp?.toFixed(0)}
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-amber-700">Mirofish — Sequía Proyectada</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Ráfagas de Viento — Datos reales */}
      {filtros.viento && shownClima.map((c, i) => {
        if(c.viento <= 15) return null;
        return (
          <CircleMarker key={'viento'+i} center={[c.lat + 0.2, c.lon + 0.2]} radius={c.viento} pathOptions={{ color: '#94a3b8', fillOpacity: 0.3 }}>
             <Tooltip permanent direction="bottom" className="font-bold text-sm text-slate-700 bg-white/70 backdrop-blur-sm rounded p-1 shadow-sm">V: {c.viento}km/h</Tooltip>
          </CircleMarker>
        )
      })}
      {/* Viento — Predicciones Mirofish */}
      {filtros.viento && shownMirofish
        .filter(m => m.tipo === 'viento_extremo')
        .map((m, i) => (
          <CircleMarker
            key={'mf_viento'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(10, m.viento_pred * 0.5)}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.25, dashArray: '6 3', weight: 2 }}
          >
            <Tooltip permanent direction="top" className="font-bold text-sm bg-white/90 border border-dashed border-slate-400 rounded shadow p-1">
              🤖 {m.viento_pred?.toFixed(0)}km/h
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-slate-600">Mirofish — Viento Proyectado</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Riesgo de Tsunami (Sismo + Deshielo Marino + Viento) */}
      {filtros.tsunami && shownSismos.map((s, i) => {
        const nearestClima = getNearestClima(s.lat, s.lon);
        let riesgoTsunami = false;
        let motivo = '';
        
        // 1. Tsunami Oficial (Basado en datos fidedignos del observatorio del USGS/NOAA)
        if (s.alerta_tsunami) {
          riesgoTsunami = true;
          motivo = 'ALERTA OFICIAL (USGS)';
        }
        // 1b. Tsunami clásico estimado (Sismo marino muy fuerte y superficial)
        else if (s.magnitud >= 6.5 && s.profundidad < 70) {
          riesgoTsunami = true;
          motivo = 'Estimado: Megasismo Submarino';
        }
        
        // 2. Mega-tsunami glaciar / Fiordos (Sismo moderado + Fuerte Deshielo + Vientos que arrastran masas de agua)
        if (!riesgoTsunami && nearestClima && s.magnitud >= 5.0) {
          if (nearestClima.deshielo_maritimo > 2 && nearestClima.viento > 25) {
            riesgoTsunami = true;
            motivo = 'Sismo + Deshielo + Ráfagas';
          }
        }
        
        if (!riesgoTsunami) return null;
        
        return (
          <CircleMarker key={'tsunami'+i} center={[s.lat, s.lon]} radius={s.magnitud * 6} pathOptions={{ color: '#0284c7', fillColor: '#38bdf8', fillOpacity: 0.8, weight: 3 }}>
             <Tooltip permanent direction="top" className="font-extrabold text-sm text-blue-900 bg-white/90 backdrop-blur-md rounded border-2 border-blue-500 shadow-xl p-1">
                🌊 RIESGO TSUNAMI ({motivo})
             </Tooltip>
          </CircleMarker>
        )
      })}
      {/* Tsunami — Predicciones Mirofish (multi-factor) */}
      {filtros.tsunami && shownMirofish
        .filter(m => m.tipo === 'tsunami_compuesto')
        .map((m, i) => (
          <CircleMarker
            key={'mf_tsu'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(14, m.intensidad * 0.18)}
            pathOptions={{ color: '#0369a1', fillColor: '#38bdf8', fillOpacity: 0.45, dashArray: '7 4', weight: 2 }}
          >
            <Tooltip permanent direction="bottom" className="font-extrabold text-sm text-blue-900 bg-white/90 backdrop-blur-md rounded border-2 border-dashed border-blue-400 shadow-xl p-1">
              🤖🌊 Mirofish Tsunami ({m.intensidad?.toFixed(0)}%)
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-blue-700">Mirofish — Tsunami Compuesto</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Riesgo de Incendios (Temp Alta + Sequía + Ráfagas) */}
      {filtros.incendios && shownClima.map((c, i) => {
        // Sequía y Temp favorecen ignición. Viento propaga.
        const ignicion = c.temperatura > 22 && c.agua_dulce > 10;
        const propagacion = c.viento > 25; 
        
        let riesgoIncendio = false;
        let etiqueta = '';
        
        if (ignicion && propagacion) {
          riesgoIncendio = true;
          etiqueta = 'Alerta ROJA: Incendio Extremo';
        } else if (ignicion && c.viento > 15) {
          riesgoIncendio = true;
          etiqueta = 'Alerta Naranja: Posible Incendio';
        }
        
        if (!riesgoIncendio) return null;
        
        const isRed = etiqueta.includes('ROJA');
        return (
          <CircleMarker key={'fire'+i} center={[c.lat, c.lon]} radius={isRed ? 20 : 15} pathOptions={{ color: isRed ? '#ef4444' : '#f97316', fillColor: isRed ? '#b91c1c' : '#ea580c', fillOpacity: 0.7, weight: 3 }}>
             <Tooltip permanent direction="top" className={`font-extrabold text-sm bg-white/90 backdrop-blur-md rounded border-2 shadow-xl p-1 ${isRed ? 'text-red-700 border-red-500' : 'text-orange-700 border-orange-500'}`}>
                🔥 {etiqueta} (T:{c.temperatura}°, V:{c.viento}km)
             </Tooltip>
          </CircleMarker>
        )
      })}
      {/* Incendios — Predicciones Mirofish */}
      {filtros.incendios && shownMirofish
        .filter(m => m.tipo === 'incendios_pred')
        .map((m, i) => {
          const isRed = m.es_alerta && m.ipi > 65;
          return (
            <CircleMarker
              key={'mf_fire'+i}
              center={[m.lat, m.lon]}
              radius={Math.max(12, m.ipi * 0.22)}
              pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.35, dashArray: '6 4', weight: 2 }}
            >
              <Tooltip permanent direction="right"
                className={`font-extrabold text-sm bg-white/90 backdrop-blur-md rounded border-2 border-dashed shadow-xl p-1
                  ${isRed ? 'text-red-700 border-red-400' : 'text-orange-700 border-orange-400'}`}
              >
                🤖🔥 IPI:{m.ipi?.toFixed(0)}
              </Tooltip>
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-base mb-1 text-red-700">Mirofish — Incendio Proyectado</h3>
                  <p className="text-sm">{m.descripcion}</p>
                  <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })
      }
      {/* === CAPAS MIROFISH PROPIAS === */}

      {/* Mirofish: Cardumen */}
      {filtros.mirofish_cardumen && shownMirofish
        .filter(m => m.tipo === 'cardumen')
        .map((m, i) => (
          <CircleMarker
            key={'mf_card'+i}
            center={[m.lat, m.lon]}
            radius={Math.max(8, m.intensidad * 0.25)}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.55, weight: 2 }}
          >
            <Tooltip permanent direction="right" className="font-bold text-sm bg-cyan-50/90 border-cyan-300 border rounded shadow p-1">
              🐟 {m.intensidad?.toFixed(0)}%
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-cyan-700">Agente Cardumen</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Mirofish: Corrientes (Malvinas) */}
      {filtros.mirofish_corrientes && shownMirofish
        .filter(m => m.tipo === 'corriente')
        .map((m, i) => (
          <CircleMarker
            key={'mf_corr'+i}
            center={[m.lat, m.lon]}
            radius={6}
            pathOptions={{ color: m.color_hex, fillColor: m.color_hex, fillOpacity: 0.7, weight: 3, dashArray: '6 4' }}
          >
            <Tooltip permanent direction="top" className="font-bold text-sm bg-indigo-50/90 border-indigo-300 border rounded shadow p-1">
              🌊 {m.intensidad?.toFixed(0)}km/h
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-indigo-700">Corriente de Malvinas</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Mirofish: Alerta Pesca */}
      {filtros.mirofish_alerta_pesca && shownMirofish
        .filter(m => m.tipo === 'alerta_pesca')
        .map((m, i) => (
          <CircleMarker
            key={'mf_pesca'+i}
            center={[m.lat, m.lon]}
            radius={m.es_alerta ? 16 : 10}
            pathOptions={{
              color: m.color_hex,
              fillColor: m.color_hex,
              fillOpacity: m.es_alerta ? 0.75 : 0.4,
              weight: m.es_alerta ? 3 : 1,
            }}
          >
            <Tooltip
              permanent
              direction="bottom"
              className={`font-extrabold text-sm bg-white/90 backdrop-blur-md rounded border-2 shadow-xl p-1
                ${m.es_alerta ? 'text-orange-700 border-orange-500' : 'text-yellow-700 border-yellow-400'}`}
            >
              {m.es_alerta ? '⛔' : '⚡'} Pesca {m.intensidad?.toFixed(0)}%
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-orange-700">Agente Alerta Pesca</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

      {/* Mirofish: Bio-Riesgo Marino (Marea Roja) */}
      {filtros.mirofish_bio_riesgo && shownMirofish
        .filter(m => m.tipo === 'bio_riesgo')
        .map((m, i) => (
          <CircleMarker
            key={'mf_bio'+i}
            center={[m.lat, m.lon]}
            radius={m.es_alerta ? 18 : 12}
            pathOptions={{
              color: m.color_hex,
              fillColor: m.color_hex,
              fillOpacity: 0.6,
              weight: 2,
              dashArray: m.es_alerta ? undefined : '4 3',
            }}
          >
            <Tooltip
              permanent
              direction="left"
              className={`font-extrabold text-sm bg-white/90 backdrop-blur-md rounded border-2 shadow-xl p-1
                ${m.es_alerta ? 'text-emerald-800 border-emerald-500' : 'text-emerald-600 border-emerald-300'}`}
            >
              🟢 HAB {m.intensidad?.toFixed(0)}%
            </Tooltip>
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base mb-1 text-emerald-700">Agente Bio-Riesgo (Marea Roja)</h3>
                <p className="text-sm">{m.descripcion}</p>
                <p className="text-xs text-slate-400 mt-2">{new Date(m.fecha).toLocaleDateString()}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))
      }

    </MapContainer>
  )
}
