import React, { useState, useEffect, useRef } from 'react';
import GraphPanel from './components/GraphPanel';
import ChatPanel from './components/ChatPanel';
import { Menu, Moon, Sun } from 'lucide-react';

function App() {
  const [cyInstance, setCyInstance] = useState(null);
  const [stats, setStats] = useState({ orders: 0, entities: 8 });
  const [showLoading, setShowLoading] = useState(true);
  const [chatWidth, setChatWidth] = useState(380); // Default width
  const [isResizing, setIsResizing] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const chatSendRef = useRef(null);

  // Backend API URL (Local)
  const API_BASE = '/api';

  useEffect(() => {
     fetch(API_BASE + '/stats')
       .then(r => r.json())
       .then(data => {
          setStats({
            orders: data.orders || 0,
            entities: 8
          })
       }).catch(() => {});
       
     const timer = setTimeout(() => setShowLoading(false), 2700);
     return () => clearTimeout(timer);
  }, []);

  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 300 && newWidth < 800) {
        setChatWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return (
    <div className={`flex flex-col h-screen w-full overflow-hidden font-sans selection:bg-blue-500/30 transition-colors p-3 gap-3 ${isDarkMode ? 'bg-mesh-dark text-slate-200 dark' : 'bg-mesh-light text-slate-800'}`}>
      
      {/* Loading Overlay */}
      {showLoading && (
        <div className="fixed inset-0 bg-gradient-to-br from-[#0f172a] to-[#1e293b] z-[9999] flex flex-col items-center justify-center animate-[fadeOut_0.4s_ease_2.5s_forwards]">
          <div className="w-16 h-16 bg-gradient-to-tr from-blue-500 to-indigo-500 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/20 mb-6 relative">
             <div className="absolute inset-0 bg-white/20 rounded-2xl animate-ping opacity-20"></div>
             <span className="text-white font-bold text-2xl tracking-tighter">D</span>
          </div>
          <h1 className="m-0 text-3xl font-bold text-white tracking-tight mb-2">Dodge AI</h1>
          <p className="text-[#94a3b8] text-[15px] max-w-xs text-center leading-relaxed mb-8">Initializing order to cash graph intelligence engine...</p>
          <div className="w-[280px] h-1.5 bg-white/10 rounded-full overflow-hidden shadow-inner">
             <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-400 rounded-full animate-[fillBar_2.5s_ease-out_forwards]"></div>
          </div>
        </div>
      )}

      {/* TOP NAV */}
      <nav className="h-[68px] glass-panel rounded-2xl flex justify-between items-center px-6 shrink-0 z-20 relative transition-all duration-300">
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-3 text-[14px]">
             <div className={`font-bold tracking-widest uppercase text-[10px] sm:text-[11px] ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Mapping</div>
             <svg width="6" height="10" viewBox="0 0 6 10" fill="none" className={isDarkMode ? "text-slate-600" : "text-slate-400"}><path d="M1 9L5 5L1 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
             <div className="font-extrabold text-[15px] sm:text-[16px] bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-500 tracking-tight">
               Order to Cash
             </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
           <button 
             onClick={() => setIsDarkMode(!isDarkMode)}
             className={`p-2 rounded-full transition-all duration-300 ${isDarkMode ? 'bg-slate-800/50 text-yellow-400 hover:bg-slate-700 hover:shadow-[0_0_15px_rgba(250,204,21,0.3)]' : 'bg-white/80 text-amber-500 hover:bg-white hover:shadow-[0_0_15px_rgba(245,158,11,0.3)] shadow-sm border border-black/5'}`}
           >
             {isDarkMode ? <Sun size={16} /> : <Moon size={16} />}
           </button>
        </div>
      </nav>

      {/* MAIN CONTAINER */}
      <div className={`flex flex-1 overflow-hidden relative gap-3 ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
        
        <div className="flex-1 rounded-2xl overflow-hidden glass-panel flex relative">
          <GraphPanel setCyInstance={setCyInstance} onExplainNode={(q) => { if(chatSendRef.current) chatSendRef.current(q); }} isDarkMode={isDarkMode} />
        </div>
        
        {/* Resize Handle */}
        <div 
          onMouseDown={handleMouseDown}
          className={`w-[6px] h-24 self-center rounded-full cursor-col-resize z-30 flex items-center justify-center transition-all opacity-40 hover:opacity-100 group shrink-0
            ${isResizing ? 'bg-blue-500 opacity-100 shadow-[0_0_10px_rgba(59,130,246,0.6)]' : (isDarkMode ? 'bg-slate-400 hover:bg-white shadow-[0_0_8px_rgba(255,255,255,0.4)]' : 'bg-slate-400 hover:bg-slate-700 text-shadow-sm')}`}
        />

        <div className="rounded-2xl overflow-hidden glass-panel flex flex-col relative transition-all duration-300" style={{ width: `${chatWidth}px` }}>
          <ChatPanel cyInstance={cyInstance} sendRef={chatSendRef} width="100%" isDarkMode={isDarkMode} />
        </div>
      </div>

    </div>
  );
}

export default App;
