import { useState, useEffect } from 'react'
import MapComponent from './components/MapComponent'
import Sidebar from './components/Sidebar'

// Usamos localhost:8002 porque es el puerto expuesto del backend en el host
const API_URL = 'http://localhost:8002/api';

function App() {
  const [fontSize, setFontSize] = useState(() => {
    return localStorage.getItem('fontSize') || '14px';
  });

  const [filtros, setFiltros] = useState({
    sismos: true,
    temperatura: false,
    sequia: false,
    deshielo: false,
    viento: false,
    tsunami: false,
    incendios: false,
    // Agentes Mirofish
    mirofish_cardumen: false,
    mirofish_corrientes: false,
    mirofish_alerta_pesca: false,
    mirofish_bio_riesgo: false,
  });
  
  const [sismos, setSismos] = useState([]);
  const [clima, setClima] = useState([]);
  const [mirofish, setMirofish] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [center, setCenter] = useState([-50.0, -70.0]); // Patagonia
  // timelineDay: 0 is today, -7 is 7 days ago, +7 is 7 days ahead
  const [timelineDay, setTimelineDay] = useState(0); 

  useEffect(() => {
    localStorage.setItem('fontSize', fontSize);
  }, [fontSize]);

  const fetchData = async () => {
    try {
      const pSismos   = fetch(`${API_URL}/sismos`).then(res => res.json());
      const pClima    = fetch(`${API_URL}/clima`).then(res => res.json());
      const pMirofish = fetch(`${API_URL}/mirofish`).then(res => res.json());
      
      const [dataSismos, dataClima, dataMirofish] = await Promise.all([pSismos, pClima, pMirofish]);
      setSismos(Array.isArray(dataSismos) ? dataSismos : []);
      setClima(Array.isArray(dataClima) ? dataClima : []);
      setMirofish(Array.isArray(dataMirofish) ? dataMirofish : []);
    } catch(err) {
      console.error("Error fetching data:", err);
    }
  }

  const handleRefresh = async () => {
    setSyncing(true);
    try {
      await fetch(`${API_URL}/sync`, { method: 'POST' });
      await fetchData();
    } catch(err) {
      console.error(err);
      alert("Error sincronizando. Asegure que el backend esté ejecutándose.");
    }
    setSyncing(false);
  }

  const handleShare = () => {
    // Generate simple shareable string
    const baseUrl = window.location.origin;
    const shareUrl = `${baseUrl}?sismos=${filtros.sismos}&temp=${filtros.temperatura}`;
    navigator.clipboard.writeText(shareUrl);
    alert("¡Enlace copiado al portapapeles! Puedes compartir esta vista.");
  }

  useEffect(() => {
    fetchData();
  }, [])

  return (
    <div 
      className="w-full h-screen bg-slate-900 overflow-hidden relative font-sans text-slate-100"
      style={{ '--tooltip-font-size': fontSize }}
    >
      
      <Sidebar 
        filtros={filtros} 
        setFiltros={setFiltros} 
        onRefresh={handleRefresh} 
        syncing={syncing}
        onShare={handleShare}
        fontSize={fontSize}
        setFontSize={setFontSize}
      />

      <div className="absolute inset-0 z-0">
         <MapComponent 
            sismos={sismos} 
            clima={clima}
            mirofish={mirofish}
            filtros={filtros}
            timelineIndex={timelineDay}
            center={center}
         />
      </div>

      {/* Timeline Controls Bottom */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[800px] bg-slate-950/80 backdrop-blur-xl border border-slate-800 rounded-3xl py-4 px-6 z-[1000] shadow-2xl flex flex-col items-center gap-2">
        <div className="w-full relative px-2">
          <input 
            type="range" 
            min="-7" 
            max="7" 
            value={timelineDay}
            onChange={(e) => setTimelineDay(Number(e.target.value))}
            className="w-full accent-blue-500 hover:accent-blue-400 cursor-pointer mb-2" 
          />
          <div className="flex justify-between w-full px-1 text-xs font-mono text-slate-400 select-none">
            {[-7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7].map(d => (
              <div key={d} className="flex flex-col items-center cursor-pointer transition-all" onClick={() => setTimelineDay(d)}>
                <div className={`h-1.5 w-[2px] mb-1 rounded-full ${d === 0 ? 'bg-emerald-400' : d === timelineDay ? 'bg-blue-400' : 'bg-slate-600'}`}></div>
                <span className={`text-[10px] sm:text-xs ${d === 0 ? 'text-emerald-400 font-extrabold' : d === timelineDay ? 'text-blue-400 font-bold' : ''}`}>
                  {d === 0 ? 'Hoy' : d > 0 ? `+${d}d` : `${d}d`}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Global CSS for animations */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        .leaflet-container { background: #0f172a; }
        .leaflet-tooltip {
          font-size: var(--tooltip-font-size, 14px) !important;
          line-height: 1.2 !important;
        }
      `}} />
    </div>
  )
}

export default App
