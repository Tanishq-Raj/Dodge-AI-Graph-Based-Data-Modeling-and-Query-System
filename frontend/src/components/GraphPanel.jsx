import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { X, Maximize2, Layers } from 'lucide-react';

const demoData = {
  nodes: [
    { data: { id: '740506', label: '740506', type: 'SalesOrder', amount: '17108.25', currency: 'INR', status: 'C' }},
    { data: { id: '740507', label: '740507', type: 'SalesOrder', amount: '19021.27', currency: 'INR', status: 'C' }},
    { data: { id: '80737721', label: '80737721', type: 'Delivery', status: 'Completed' }},
    { data: { id: '80737722', label: '80737722', type: 'Delivery', status: 'Completed' }},
    { data: { id: '91150187', label: '91150187', type: 'BillingDoc', netValue: '17108.25' }},
    { data: { id: '91150188', label: '91150188', type: 'BillingDoc', netValue: '19021.27' }},
    { data: { id: '9400635958', label: '9400635958', type: 'JournalEntry', gl_account: '15500020' }},
    { data: { id: '310000108', label: 'Cardenas Parker', type: 'Customer', region: 'Millerborough' }},
    { data: { id: 'P1', label: 'TXN-9A82B', type: 'Payment', amount: '17108.25', status: 'Cleared' }}
  ],
  edges: [
    { data: { source: '740506', target: '80737721' } },
    { data: { source: '740507', target: '80737722' } },
    { data: { source: '80737721', target: '91150187' } },
    { data: { source: '80737722', target: '91150188' } },
    { data: { source: '91150187', target: '9400635958' } },
    { data: { source: '9400635958', target: 'P1' } },
    { data: { source: '310000108', target: '740506' } },
    { data: { source: '310000108', target: '740507' } }
  ]
};

// Backend API URL (Dynamic for Vercel/Render)
const API_BASE = '/api';

const GraphPanel = ({ setCyInstance, onExplainNode, isDarkMode }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [counts, setCounts] = useState({ nodes: 0, edges: 0 });
  const [popup, setPopup] = useState(null);
  const [filter, setFilter] = useState('All');
  const [labelsVisible, setLabelsVisible] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;
    let ignore = false;
    let localCy = null;

    fetch(API_BASE + '/graph')
      .then(res => res.json())
      .then(data => {
        if (ignore) return; // Unmounted during async fetch

        let nodeIds = new Set(data.nodes.map(n => String(n.data.id)));
        let validEdges = data.edges.filter(e => nodeIds.has(String(e.data.source)) && nodeIds.has(String(e.data.target)));
        let elements = [...data.nodes, ...validEdges];
        elements.forEach(el => {
          if (el.data.source) return;
          const t = el.data.type;
          if (t === 'SalesOrder') el.classes = 'hub';
          else if (t === 'Customer') el.classes = 'customer';
          else if (t === 'Delivery') el.classes = 'connected';
          else if (t === 'BillingDoc') el.classes = 'leaf billing';
          else if (t === 'JournalEntry') el.classes = 'leaf journal';
          else if (t === 'Payment') el.classes = 'leaf payment';
          else if (t === 'SOItem') el.classes = 'soitem';
          else if (t === 'Product') el.classes = 'product';
        });

        const cy = cytoscape({
          container: containerRef.current,
          elements: elements,
          wheelSensitivity: 0.2, // makes scroll zooming buttery smooth
          style: [
            { selector: 'node', style: { 'label': 'data(label)', 'font-size': 11, 'text-valign': 'bottom', 'text-margin-y': 6, 'color': isDarkMode ? '#94a3b8' : '#475569', 'font-family': 'sans-serif', 'font-weight': '600' } },
            { selector: '.hub', style: { width: 24, height: 24, 'background-color': '#2563eb' } },
            { selector: '.customer', style: { width: 20, height: 20, 'background-color': '#10b981' } },
            { selector: '.connected', style: { width: 16, height: 16, 'background-color': '#06b6d4' } },
            { selector: '.leaf.billing', style: { width: 10, height: 10, 'background-color': '#f59e0b' } },
            { selector: '.leaf.journal', style: { width: 10, height: 10, 'background-color': '#8b5cf6' } },
            { selector: '.leaf.payment', style: { width: 10, height: 10, 'background-color': '#ec4899' } },
            { selector: '.soitem', style: { width: 12, height: 12, 'background-color': '#6366f1' } },
            { selector: '.product', style: { width: 14, height: 14, 'background-color': '#f43f5e', 'shape': 'square' } },
            { selector: 'edge', style: { width: 2.5, 'line-color': isDarkMode ? 'rgba(14,165,233,0.5)' : 'rgba(37,99,235,0.6)', 'curve-style': 'bezier', 'target-arrow-color': isDarkMode ? 'rgba(14,165,233,0.5)' : 'rgba(37,99,235,0.6)', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.2 } },
            { selector: '.highlighted', style: { 'border-width': 4, 'border-color': isDarkMode ? '#f8fafc' : '#1a1a1a', 'background-color': '#fcd34d', width: 32, height: 32, 'z-index': 100 } },
            { selector: '.dimmed', style: { 'opacity': isDarkMode ? 0.08 : 0.15 } },
            { selector: '.hide-label', style: { 'text-opacity': 0 } }
          ],
          layout: { 
            name: 'cose', 
            nodeRepulsion: 15000, 
            idealEdgeLength: 100, 
            animate: false // calculate positions instantly, avoiding laggy physics animation 
          }
        });

        localCy = cy;
        cyRef.current = cy;
        setCyInstance(cy);
        setCounts({ nodes: cy.nodes().length, edges: cy.edges().length });

        cy.on('tap', 'node', async (evt) => {
          const node = evt.target;
          const pos = evt.renderedPosition;
          
          cy.elements().addClass('dimmed').removeClass('highlighted');
          node.removeClass('dimmed').addClass('highlighted');
          node.connectedEdges().removeClass('dimmed').addClass('highlighted');
          node.connectedEdges().connectedNodes().removeClass('dimmed').addClass('highlighted');
          
          let x = pos.x + 20;
          let y = pos.y - 40;
          if (x + 270 > cy.width()) x = pos.x - 290;
          
          let liveData = node.data();
          try {
            const resp = await fetch(`${API_BASE}/node-details/${node.data('id')}`);
            const json = await resp.json();
            if (json.data) liveData = { ...node.data(), ...json.data, _detailType: json.type };
          } catch(e) { console.warn('Node details fetch failed:', e); }
          
          if (!ignore) setPopup({ node, data: liveData, conns: node.connectedEdges().length, x, y });
        });

        cy.on('tap', (evt) => {
          if (evt.target === cy) {
            cy.elements().removeClass('dimmed').removeClass('highlighted');
            setPopup(null);
          }
        });

        cy.on('zoom pan', () => setPopup(null));
      })
      .catch(err => console.error("Could not fetch graph:", err));

    return () => {
       ignore = true;
       if (localCy) {
         try {
           localCy.stop(); // Stop any running animations
           localCy.destroy();
         } catch (e) {}
       } else if (cyRef.current) {
         try {
           cyRef.current.stop();
           cyRef.current.destroy();
         } catch (e) {}
       }
    };
  }, [setCyInstance]);

  // Handle dark mode theme switching in cytoscape without full reload
  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.style()
        .selector('node').style({ 'color': isDarkMode ? '#f8fafc' : '#475569' })
        .selector('edge').style({ 
           'line-color': isDarkMode ? 'rgba(56,189,248,0.75)' : 'rgba(37,99,235,0.6)', 
           'target-arrow-color': isDarkMode ? 'rgba(56,189,248,0.75)' : 'rgba(37,99,235,0.6)',
           'width': 2.5
        })
        .selector('.highlighted').style({ 'border-color': isDarkMode ? '#f8fafc' : '#1a1a1a' })
        .selector('.dimmed').style({ 'opacity': isDarkMode ? 0.08 : 0.15 })
        .update();
    }
  }, [isDarkMode]);


  const handleFilter = (type) => {
    setFilter(type);
    cyRef.current.elements().removeClass('dimmed').removeClass('highlighted');
    if (type !== 'All') {
      cyRef.current.nodes().forEach(n => {
        if (n.data('type') !== type) n.addClass('dimmed');
      });
    }
  };

  const toggleLabels = () => {
    const next = !labelsVisible;
    setLabelsVisible(next);
    if (next) cyRef.current.nodes().removeClass('hide-label');
    else cyRef.current.nodes().addClass('hide-label');
  };

  const getBadgeColor = (type) => {
    switch(type) {
      case 'SalesOrder': return '#2563eb';
      case 'Delivery': return '#06b6d4';
      case 'BillingDoc': return '#f59e0b';
      case 'JournalEntry': return '#8b5cf6';
      case 'Payment': return '#ec4899';
      case 'Customer': return '#10b981';
      case 'SOItem': return '#6366f1';
      case 'Product': return '#f43f5e';
      default: return '#64748b';
    }
  };

  const exploreNeighbors = () => {
    if (!popup || !cyRef.current) return;
    const n = cyRef.current.getElementById(popup.data.id);
    const neighbors = n.connectedEdges().connectedNodes();
    neighbors.addClass('highlighted');
    n.removeClass('dimmed').addClass('highlighted');
    cyRef.current.animate({ fit: { eles: neighbors.union(n), padding: 50 } }, { duration: 800 });
  };

  return (
    <div className={`flex-1 relative w-full h-full overflow-hidden transition-colors ${isDarkMode ? 'bg-transparent' : 'bg-transparent'}`}>
      <div ref={containerRef} className="w-full h-full" />

      {/* Controls */}
      <div className="absolute top-5 left-5 flex gap-2.5 z-10">
        <button className={`glass-button px-3.5 py-2 rounded-[14px] text-[13px] font-semibold transition-all flex items-center gap-1.5 ${isDarkMode ? 'text-slate-200 hover:bg-slate-700/60' : 'text-[#334155] hover:bg-white/80'}`} onClick={() => cyRef.current?.fit()}>
           <Maximize2 size={15} /> Minimize
        </button>
        <button className={`px-3.5 py-2 rounded-[14px] text-[13px] font-medium transition-all flex items-center gap-1.5 shadow-md backdrop-blur-md border ${isDarkMode ? 'bg-indigo-500/80 text-white hover:bg-indigo-400/90 border-indigo-400/50' : 'bg-indigo-500/80 text-white hover:bg-indigo-600/90 border-indigo-600/20'}`} onClick={toggleLabels}>
           <Layers size={15} /> {labelsVisible ? 'Hide Granular Overlay' : 'Show Granular Overlay'}
        </button>
      </div>

      {/* Filters */}
      <div className={`absolute top-5 left-1/2 -translate-x-1/2 flex gap-1 glass-panel p-1.5 rounded-full z-10 transition-all ${isDarkMode ? 'shadow-black/20 text-slate-300' : 'shadow-sm text-[#475569]'}`}>
        {['All', 'SalesOrder', 'Delivery', 'BillingDoc', 'JournalEntry', 'Payment'].map(t => {
          const isActive = filter === t;
          let activeStyle = {};
          if (isActive) {
            if (t === 'All') {
              activeStyle = { backgroundImage: 'linear-gradient(to bottom right, #1e293b, #0f172a)', color: 'white' };
            } else {
              activeStyle = { backgroundColor: getBadgeColor(t), color: 'white' };
            }
          }
          return (
            <button 
              key={t}
              onClick={() => handleFilter(t)}
              className={`px-4 py-1.5 text-[13px] font-semibold rounded-full transition-all duration-200 ${isActive ? 'shadow-md shadow-black/10' : (isDarkMode ? 'text-slate-300 hover:text-white hover:bg-white/10' : 'text-[#64748b] hover:text-[#0f172a] hover:bg-black/5')}`}
              style={activeStyle}
            >
              {t === 'SalesOrder' ? 'Orders' : t.replace('Doc', '').replace('Entry', '')}
            </button>
          );
        })}
      </div>

      {/* Popup */}
      {popup && (
        <div className={`absolute rounded-[14px] p-4 min-w-[270px] z-20 animate-[popIn_0.15s_ease-out] glass-panel transition-all ${isDarkMode ? 'bg-slate-900/80 shadow-[0_12px_40px_rgba(0,0,0,0.5)] border-slate-700/50' : 'bg-white/80 shadow-[0_12px_40px_rgba(31,38,135,0.1)] border-white/60'}`} style={{ left: popup.x, top: popup.y }}>
          <div className="flex justify-between items-start mb-3">
            <div>
              <div className="inline-block px-2 py-0.5 rounded-xl text-[10px] font-semibold text-white mb-1.5 shadow-sm" style={{ backgroundColor: getBadgeColor(popup.data.type) }}>
                {popup.data.type}
              </div>
              <div className={`text-[15px] font-bold mb-1 ${isDarkMode ? 'text-white' : 'text-[#1a1a1a]'}`}>{popup.data.id}</div>
            </div>
            <X size={16} className={`cursor-pointer transition-colors ${isDarkMode ? 'text-slate-400 hover:text-white' : 'text-[#8a8a84] hover:text-black'}`} onClick={() => setPopup(null)} />
          </div>
          
          <div className={`flex flex-col gap-1.5 mb-3 pb-3 border-b text-[12px] ${isDarkMode ? 'border-slate-700/50' : 'border-[#e2e2dc]'}`}>
            {Object.entries(popup.data).filter(([k]) => !['id','type','label'].includes(k)).slice(0, 8).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className={`font-medium ${isDarkMode ? 'text-slate-400' : 'text-[#8a8a84]'}`}>{k}</span>
                <span className={`font-medium text-right max-w-[140px] truncate ${isDarkMode ? 'text-slate-200' : ''}`}>{v}</span>
              </div>
            ))}
          </div>
          
          <div className={`text-[10px] mb-3 italic ${isDarkMode ? 'text-slate-500' : 'text-[#8a8a84]'}`}>Additional fields hidden for readability</div>
             <div className="flex justify-between items-center gap-2">
               <div className={`font-medium text-xs ${isDarkMode ? 'text-slate-400' : 'text-[#8a8a84]'}`}>Connections: {popup.conns}</div>
               <div className="flex gap-1.5">
                 <button className="bg-[#8b5cf6] text-white px-2.5 py-1.5 rounded-lg text-xs font-medium hover:opacity-90 shadow-sm" onClick={() => { if(onExplainNode) onExplainNode(`explain ${popup.data.id}`); setPopup(null); }}>Explain</button>
                 <button className={`px-2.5 py-1.5 rounded-lg text-xs font-medium hover:opacity-90 shadow-sm ${isDarkMode ? 'bg-slate-700 text-white' : 'bg-[#1a1a1a] text-white'}`} onClick={exploreNeighbors}>Explore</button>
               </div>
             </div>
        </div>
      )}

      {/* Legend */}
      <div className={`absolute bottom-6 left-5 glass-panel rounded-[14px] p-4 z-10 text-[12px] font-medium grid gap-2.5 transition-all ${isDarkMode ? 'text-slate-300 shadow-black/20' : 'text-[#475569] shadow-sm'}`}>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#2563eb] shadow-sm"></div>Sales Order</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#06b6d4] shadow-sm"></div>Delivery</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#f59e0b] shadow-sm"></div>Billing Doc</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6] shadow-sm"></div>Journal Entry</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ec4899] shadow-sm"></div>Payment</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#10b981] shadow-sm"></div>Customer</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 rounded-full bg-[#6366f1] shadow-sm"></div>SO Item</div>
         <div className="flex items-center gap-2.5"><div className="w-2.5 h-2.5 bg-[#f43f5e] shadow-sm rounded-[3px]"></div>Product/Material</div>
      </div>

      {/* Counts */}
      <div className={`absolute bottom-6 right-5 glass-panel rounded-[14px] px-4 py-2 z-10 font-bold text-[12px] transition-all flex items-center gap-1.5 ${isDarkMode ? 'text-slate-300 shadow-black/20' : 'text-[#64748b] shadow-sm'}`}>
         {counts.nodes} <span className={`font-normal ${isDarkMode ? 'text-slate-500' : 'text-[#94a3b8]'}`}>nodes</span> <span className={`mx-0.5 ${isDarkMode ? 'text-slate-600' : 'text-[#cbd5e1]'}`}>|</span> {counts.edges} <span className={`font-normal ${isDarkMode ? 'text-slate-500' : 'text-[#94a3b8]'}`}>edges</span>
      </div>
    </div>
  );
};

export default GraphPanel;
