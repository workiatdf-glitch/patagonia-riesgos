import { Layers, Thermometer, Wind, Droplets, Activity, Share2, RefreshCw, Snowflake, Flame, Waves, Fish, Navigation, AlertTriangle, Leaf } from 'lucide-react'

export default function Sidebar({ filtros, setFiltros, onRefresh, syncing, onShare }) {
  
  const toggleFilter = (key) => {
    setFiltros(prev => ({...prev, [key]: !prev[key]}))
  }

  const FilterButton = ({ id, label, Icon, colorClass }) => {
    const active = filtros[id];
    return (
      <button 
        onClick={() => toggleFilter(id)}
        className={`flex items-center w-full gap-3 p-3 rounded-xl transition-all duration-300 backdrop-blur-md mb-2
        ${active ? `bg-slate-800/80 border ${colorClass} shadow-lg shadow-${colorClass.split('-')[1]}/20 text-white` : 'bg-slate-900/40 border border-slate-700/50 text-slate-400 hover:bg-slate-800/60'}`}
      >
        <Icon size={20} className={active ? colorClass.replace('border-', 'text-') : ''} />
        <span className="font-medium text-sm">{label}</span>
        <div className={`ml-auto w-3 h-3 rounded-full ${active ? colorClass.replace('border-', 'bg-') : 'bg-slate-700'}`}></div>
      </button>
    )
  }

  return (
    <div className="absolute top-4 left-4 w-72 h-[calc(100vh-32px)] z-[1000] flex flex-col gap-4">
      
      {/* Header Panel */}
      <div className="bg-slate-950/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl">
        <h1 className="text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-1">
          ClimaAhora TDF
        </h1>
        <p className="text-xs text-slate-400 mb-4">Monitor Predictivo Patagonia & Sur</p>
        
        <div className="flex gap-2">
          <button 
            onClick={onRefresh}
            disabled={syncing}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-600/90 hover:bg-blue-500 text-white py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
          >
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Sincronizando...' : 'Actualizar'}
          </button>
          <button 
            onClick={onShare}
            className="flex items-center justify-center w-10 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all"
            title="Compartir vista"
          >
            <Share2 size={16} />
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      <div className="bg-slate-950/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl flex-1 overflow-y-auto custom-scrollbar">
        <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Layers size={16} /> Capas de Riesgo
        </h2>

        <FilterButton id="sismos" label="Actividad Sísmica" Icon={Activity} colorClass="border-red-500" />
        <FilterButton id="temperatura" label="Anomalías de Temp." Icon={Thermometer} colorClass="border-orange-500" />
        <FilterButton id="sequia" label="Pérdida Agua Dulce" Icon={Droplets} colorClass="border-amber-600" />
        <FilterButton id="deshielo" label="Deshielo Marítimo" Icon={Snowflake} colorClass="border-cyan-400" />
        <FilterButton id="viento" label="Ráfagas Extremas" Icon={Wind} colorClass="border-slate-400" />
        
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-6 mb-3 flex items-center gap-2">
          Modelos Compuestos
        </h3>
        <FilterButton id="tsunami" label="Riesgo de Tsunami" Icon={Waves} colorClass="border-blue-500" />
        <FilterButton id="incendios" label="Riesgo de Incendios" Icon={Flame} colorClass="border-rose-500" />

        <h3 className="text-xs font-bold text-teal-400 uppercase tracking-wider mt-6 mb-3 flex items-center gap-2">
          <Fish size={14} /> Agentes IA Mirofish
        </h3>
        <FilterButton id="mirofish_cardumen" label="Zonas de Cardumen" Icon={Fish} colorClass="border-cyan-400" />
        <FilterButton id="mirofish_corrientes" label="Corriente de Malvinas" Icon={Navigation} colorClass="border-indigo-400" />
        <FilterButton id="mirofish_alerta_pesca" label="Alerta Pesca" Icon={AlertTriangle} colorClass="border-orange-400" />
        <FilterButton id="mirofish_bio_riesgo" label="Marea Roja (HAB)" Icon={Leaf} colorClass="border-emerald-400" />

        <div className="mt-8 pt-6 border-t border-slate-800/50">
          <p className="text-xs text-slate-500 leading-relaxed italic">
            * El algoritmo predictivo sísmico estima la disipación de energía de placas. No garantiza certeza. Los registros de 25 años apoyan las alertas climáticas.
          </p>
        </div>
      </div>

    </div>
  )
}
