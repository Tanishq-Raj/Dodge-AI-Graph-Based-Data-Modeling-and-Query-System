import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, ChevronDown, ChevronRight, CheckCircle2, Circle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const guardrails = ["who is", "poem", "joke", "weather", "translate"];
const suggestions = [
  "Show all orders",
  "Track order 740509",
  "Explain billing 91150187",
  "Find fraud",
  "Orders without invoice",
  "Customer revenue",
  "Top billed products",
  "Journal entries",
  "Show deliveries",
  "Show customers",
];

const ChatPanel = ({ cyInstance, sendRef, width, isDarkMode }) => {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    // A simple smooth scroll is all that is needed here.
    // document.startViewTransition here freezes the DOM and canvas, causing
    // cytoscape animations to crash with "Cannot read properties of null (reading 'notify')"
    try {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    } catch (e) { }
  }, [messages, isThinking]);

  const getBadgeColor = (intent) => {
    if (intent.includes('Trace')) return '#3b82f6';
    if (intent.includes('Error') || intent.includes('Anomaly')) return '#f87171';
    if (intent.includes('Aggregat')) return '#22c55e';
    if (intent.includes('Lookup')) return '#f59e0b';
    if (intent.includes('Scope')) return '#f87171';
    if (intent.includes('Fraud')) return '#ef4444';
    if (intent.includes('Explain')) return '#8b5cf6';
    return '#1a1a1a';
  };

  // Backend API URL (Dynamic for Vercel/Render)
  const API_BASE = '/api';

  const handleSend = async (overrideQ) => {
    const text = overrideQ || query;
    if (!text.trim() || isThinking) return;

    setQuery("");
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsThinking(true);

    const qlow = text.toLowerCase();

    // Guardrails
    if (guardrails.some(g => qlow.includes(g))) {
      setTimeout(() => {
        setIsThinking(false);
        setMessages(prev => [...prev, {
          role: 'system',
          intent: '🚫 Out of Scope',
          intentColor: '#f87171',
          content: "This system only answers questions about the Order to Cash dataset. Please ask about orders, deliveries, billing, or payments."
        }]);
      }, 800);
      return;
    }

    try {
      const res = await axios.post(`${API_BASE}/query`, { query: text });
      const data = res.data;

      // Update Graph
      if (cyInstance) {
        if (data.highlights && data.highlights.length > 0) {
          cyInstance.elements().addClass('dimmed').removeClass('highlighted');
          let collection = cyInstance.collection();
          data.highlights.forEach(h => {
            cyInstance.nodes().forEach(n => {
              if (n.data('id') === h || n.data('label').toLowerCase().includes(h.toLowerCase().replace('s', ''))) {
                n.removeClass('dimmed').addClass('highlighted');
                collection = collection.union(n);
                n.connectedEdges().removeClass('dimmed');
              }
            });
          });
          if (collection.length > 0) {
            cyInstance.animate({ fit: { eles: collection, padding: 50 } }, { duration: 800 });
          }
        } else {
          // STEP 5: Clear highlights if not a graph intent
          cyInstance.elements().removeClass('dimmed').removeClass('highlighted');
        }
      }

      const botMsg = {
        role: 'system',
        intent: data.intent || "🔍 Lookup",
        intentColor: getBadgeColor(data.intent || ""),
        content: data.answer || "Found matching records from your ERP system.",
        result: data.result,
        type: data.type
      };

      setIsThinking(false);
      setMessages(prev => [...prev, botMsg]);

    } catch (error) {
      // Offline mock data
      setTimeout(() => {
        setIsThinking(false);
        if (qlow.includes("trace") || qlow.includes("91150187")) {
          if (cyInstance) {
            cyInstance.elements().addClass('dimmed').removeClass('highlighted');
            let c = cyInstance.collection();
            ['91150187', '80737721', '740506', '9400635958', '310000108'].forEach(id => {
              const n = cyInstance.getElementById(id);
              if (n.length) { n.removeClass('dimmed').addClass('highlighted'); n.connectedEdges().removeClass('dimmed'); c = c.union(n); }
            });
            cyInstance.animate({ fit: { eles: c, padding: 50 } }, { duration: 800 });
          }
          setMessages(prev => [...prev, {
            role: 'system', intent: '🔗 Flow Trace', intentColor: '#3b82f6',
            content: "Tracing billing document **91150187**. It originates from Sales Order 740506 via Delivery 80737721 and posts to Journal Entry 9400635958.",
            planSteps: ["Lookup BillingDoc 91150187", "Traverse to predecessor (Delivery)", "Traverse to root (Order)"],
            sql: "SELECT * FROM billing_document_headers WHERE billingDocument='91150187'"
          }]);
        } else {
          setMessages(prev => [...prev, {
            role: 'system', intent: '⚠️ API Error', intentColor: '#f87171',
            content: "Backend API is unreachable. Showing mocked offline response."
          }]);
        }
      }, 1000);
    }
  };

  // Expose handleSend to parent via sendRef (for GraphPanel Explain button)
  useEffect(() => {
    if (sendRef) sendRef.current = handleSend;
  }, [sendRef]);

  // Reasoning and Table components removed per user request for a cleaner natural language UI.

  const renderFraudList = (data) => {
    if (!data || data.length === 0) return null;
    return (
      <div className="mt-2 space-y-1.5">
        {data.slice(0, 10).map((item, i) => (
          <div key={i} className="flex items-start gap-2 text-[12px] bg-[#fef2f2] border border-[#fecaca] rounded-md px-2.5 py-1.5">
            <span className="shrink-0 mt-0.5">🔴</span>
            <div>
              <span className="font-semibold">{item.id || item.salesOrder || item.billingDocument || item.journalEntry}</span>
              <span className="text-[#991b1b] ml-1">{item.issue}</span>
            </div>
          </div>
        ))}
        {data.length > 10 && <div className="text-[11px] text-[#8a8a84]">...and {data.length - 10} more</div>}
      </div>
    );
  };

  const renderFlowTrace = (data) => {
    if (!data || data.length === 0) return null;
    const r = data[0]; // Take the first row for the main flow

    const steps = [
      { id: r.salesOrder, label: 'Order', icon: '📦', color: '#3b82f6' },
      { id: r.deliveryDocument, label: 'Delivery', icon: '🚚', color: '#22c55e' },
      { id: r.billingDocument, label: 'Billing', icon: '📄', color: '#f59e0b' },
      { id: r.journalEntry, label: 'Journal', icon: '📒', color: '#8b5cf6' },
      { id: r.paymentDoc, label: 'Payment', icon: '💰', color: '#f87171' }
    ].filter(s => s.id && s.id !== 'nan' && String(s.id).toLowerCase() !== 'null');

    return (
      <div className={`mt-4 flex flex-col gap-3 rounded-xl p-3.5 shadow-sm border transition-all ${isDarkMode ? 'bg-slate-800/40 border-slate-700/50' : 'bg-white/50 border-white/50 backdrop-blur-sm'}`}>
        <div className="text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1 px-1">Transaction Stream</div>
        <div className="flex items-center flex-wrap gap-y-4">
          {steps.map((step, i) => (
            <React.Fragment key={i}>
              <div
                className={`flex items-center gap-2 px-3 py-2 border rounded-lg shadow-sm cursor-pointer transition-all group ${isDarkMode ? 'bg-slate-800/60 border-slate-700 hover:border-blue-500' : 'bg-white/80 border-white hover:border-blue-400'}`}
                onClick={() => {
                  if (cyInstance) {
                    const n = cyInstance.getElementById(String(step.id));
                    if (n.length) {
                      cyInstance.elements().addClass('dimmed').removeClass('highlighted');
                      n.removeClass('dimmed').addClass('highlighted');
                      n.connectedEdges().removeClass('dimmed').addClass('highlighted');
                      cyInstance.animate({ fit: { eles: n.union(n.connectedEdges()), padding: 50 } }, { duration: 600 });
                    }
                  }
                }}
              >
                <span className="text-lg">{step.icon}</span>
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold text-[#94a3b8] uppercase flex items-center gap-1">
                    {step.label}
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: step.color }}></div>
                  </span>
                  <span className="text-[12px] font-mono font-semibold text-[#1e293b] group-hover:text-[#3b82f6]">{step.id}</span>
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className="mx-1.5 text-[#cbd5e1] font-bold text-xl animate-pulse">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#f87171', '#8b5cf6'];

  const renderDynamicChart = (type, data) => {
    if (!data || data.length === 0 || type === 'table' || type === 'flow') return null;
    const keys = Object.keys(data[0]);
    if (keys.length < 2) return null;

    const xAxisKey = keys[0];
    const yAxisKey = keys[1];

    if (type === 'bar') {
      return (
        <div className="w-full h-[180px] mt-3 bg-white p-2 rounded border border-[#e2e2dc]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey={xAxisKey} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f5f5f0' }} contentStyle={{ fontSize: '11px', borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
              <Bar dataKey={yAxisKey} fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (type === 'distribution') {
      return (
        <div className="w-full h-[180px] mt-3 bg-white p-2 rounded border border-[#e2e2dc]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey={yAxisKey} nameKey={xAxisKey} cx="50%" cy="50%" outerRadius={60} fill="#3b82f6" label={{ fontSize: 10 }}>
                {data.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }
    return null;
  };
  const renderTableData = (data) => {
    if (!data || data.length === 0) return null;
    const cols = Object.keys(data[0]).filter(k => k !== 'uuid' && k !== 'id' && !k.startsWith('_')).slice(0, 4);
    const rows = data.slice(0, 5);
    return (
      <div className={`mt-4 border rounded-[14px] overflow-hidden shadow-sm ring-1 ring-black/5 transition-colors ${isDarkMode ? 'bg-slate-800/40 border-slate-700/50' : 'bg-white/50 border-white/50 backdrop-blur-sm'}`}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] mb-0 border-collapse" style={{ marginTop: 0 }}>
            <thead className={`border-b transition-colors ${isDarkMode ? 'bg-slate-800/60 border-slate-700' : 'bg-white/60 border-white/50'}`}>
              <tr>
                {cols.map(c => <th key={c} className={`px-3.5 py-2.5 font-bold uppercase tracking-wider text-[10px] whitespace-nowrap ${isDarkMode ? 'text-slate-400' : 'text-[#475569]'}`}>{c.replace(/([A-Z])/g, ' $1').trim()}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className={`border-b last:border-0 transition-colors ${isDarkMode ? 'border-slate-800 hover:bg-slate-700/50' : 'border-[#f1f5f9]/50 hover:bg-white/60'}`}>
                  {cols.map(c => <td key={c} className={`px-3.5 py-3 whitespace-nowrap font-medium ${isDarkMode ? 'text-slate-300' : 'text-[#334155]'}`}>{row[c] == null ? <span className="text-[#94a3b8] italic">—</span> : String(row[c])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.length > 5 && <div className={`px-3 py-2 text-center text-[10.5px] border-t font-semibold tracking-wide transition-colors ${isDarkMode ? 'bg-slate-800/60 text-slate-500 border-slate-700' : 'bg-white/60 text-[#64748b] border-white/50'}`}>+ {data.length - 5} MORE ROWS</div>}
      </div>
    );
  };

  const formatText = (txt) => {
    const parts = txt.split(/(\*\*.*?\*\*)/g);
    return parts.map((p, i) => {
      if (p.startsWith('**') && p.endsWith('**')) return <strong key={i} className="font-semibold text-black">{p.slice(2, -2)}</strong>;
      return p;
    });
  };

  return (
    <div
      className={`flex flex-col h-full w-full shadow-inner ${isDarkMode ? 'bg-slate-900/30' : 'bg-white/30'}`}
      style={{ width }}
    >

      {/* Header */}
      <div className={`px-6 py-5 border-b shrink-0 flex items-center gap-3.5 transition-all duration-300 ${isDarkMode ? 'border-slate-800/40 bg-slate-900/40' : 'border-white/50 bg-white/40'}`}>
        <div className="w-9 h-9 relative">
           <div className="absolute inset-0 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-xl rounded-tr-sm shadow-md animate-pulse opacity-20"></div>
           <div className="absolute inset-0 bg-gradient-to-br from-[#1e293b] to-[#0f172a] text-white rounded-xl rounded-tr-sm flex items-center justify-center font-black text-[15px] shadow-sm ring-1 ring-white/10 overflow-hidden">
             <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent"></div>
             D
           </div>
        </div>
        <div className={`font-extrabold text-[16.5px] tracking-tight ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>Chat with Dodge Ai</div>
      </div>

      {/* Messages */}
      <div id="chat-messages" className="flex-1 overflow-y-auto p-5 flex flex-col gap-7 transition-colors duration-300 bg-transparent">
        {messages.length === 0 && !isThinking && (
          <div className="flex flex-col items-center justify-center m-auto opacity-90 pb-10 animate-slide-up">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg mb-6 ring-4 ${isDarkMode ? 'bg-gradient-to-br from-[#1e293b] to-[#0f172a] shadow-black/40 ring-slate-800/50 text-white' : 'bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-blue-500/20 ring-blue-50 text-white'}`}>
               <span className="font-black text-2xl tracking-tight">D</span>
            </div>
            <h2 className={`text-xl font-bold mb-8 tracking-tight ${isDarkMode ? 'text-white' : 'text-slate-800'}`}>How can I help you today?</h2>
            <div className="flex flex-wrap justify-center gap-2.5 max-w-[90%]">
              {suggestions.map(s => (
                <button key={s} onClick={() => handleSend(s)} className={`px-4 py-2 rounded-full border text-[12px] font-bold tracking-wide transition-all duration-300 hover:-translate-y-[1px] active:translate-y-0 ${
                  isDarkMode 
                    ? 'glass-button border-white/10 text-slate-300 hover:text-white hover:border-white/20 hover:bg-slate-800/80 shadow-sm' 
                    : 'glass-button border-black/10 text-slate-600 hover:text-slate-900 hover:border-black/20 hover:shadow-md shadow-sm bg-white/60'
                }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          m.role === 'user' ? (
            <div key={i} className={`animate-slide-up self-end max-w-[85%] text-white rounded-[24px] rounded-tr-[4px] px-5 py-3.5 text-[14px] leading-relaxed shadow-lg backdrop-blur-md transition-all ${
              isDarkMode ? 'bg-gradient-to-br from-blue-500/80 to-indigo-600/80 shadow-blue-900/40 ring-1 ring-white/10' : 'bg-gradient-to-br from-indigo-500/90 to-blue-600/90 shadow-blue-500/30 ring-1 ring-white/20'
            }`}>
              {m.content}
            </div>
          ) : (
            <div key={i} className="flex gap-4 animate-slide-up max-w-[95%]">
              <div className="w-8 h-8 relative shrink-0 mt-1">
                 <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full blur-[4px] opacity-40"></div>
                 <div className="absolute inset-0 bg-gradient-to-br from-[#1e293b] to-[#0f172a] text-white rounded-full flex items-center justify-center font-bold text-[12px] shadow-sm ring-1 ring-white/10">D</div>
              </div>
              <div className={`flex-1 min-w-0 border rounded-[24px] rounded-tl-[4px] p-5 shadow-lg transition-all ${isDarkMode ? 'glass-panel bg-slate-900/60 shadow-black/20 border-slate-700/50' : 'glass-panel bg-white/70 shadow-slate-300/30 border-white/60'}`}>
                <div className="inline-block px-3 py-1 rounded-full text-[10px] font-extrabold text-white mb-2.5 shadow-sm uppercase tracking-widest" style={{ backgroundColor: m.intentColor }}>{m.intent}</div>
                <div className={`text-[13.5px] mt-0.5 whitespace-pre-wrap leading-relaxed ${isDarkMode ? 'text-slate-200' : 'text-slate-800'}`}>{formatText(m.content)}</div>
                {(m.type === 'flow' || m.type === 'explanation') && m.result && renderFlowTrace(m.result)}
                {m.result && m.result.length > 0 && m.type && renderDynamicChart(m.type, m.result)}
                {m.type === 'table' && m.result && m.result.length > 0 && renderTableData(m.result)}
                {m.type === 'fraud' && m.result && renderFraudList(m.result)}
              </div>
            </div>
          )
        ))}
        {isThinking && (
          <div className="flex gap-3.5 animate-slide-up">
            <div className="w-8 h-8 bg-gradient-to-br from-[#1a1a1a] to-[#3f3f46] text-white rounded-full flex items-center justify-center font-bold text-[13px] shrink-0 mt-1 shadow-md shadow-[#1a1a1a]/10 ring-1 ring-black/5">D</div>
            <div className={`border rounded-[20px] rounded-tl-sm self-start py-3.5 px-4 min-w-[70px] flex items-center justify-center transition-colors ${isDarkMode ? 'glass-panel bg-slate-900/60 border-slate-700/50 shadow-black/20' : 'glass-panel bg-white/70 border-white/60 shadow-slate-300/30'}`}>
              <div className={`dot dot1 ${isDarkMode ? 'bg-slate-400' : 'bg-[#94a3b8]'}`}></div><div className={`dot dot2 ${isDarkMode ? 'bg-slate-400' : 'bg-[#94a3b8]'}`}></div><div className={`dot dot3 ${isDarkMode ? 'bg-slate-400' : 'bg-[#94a3b8]'}`}></div>
            </div>
          </div>
        )}
        <div ref={endRef} className="h-2" />
      </div>

      {/* Footer Input */}
      <div className={`px-5 py-4 border-t shrink-0 z-20 backdrop-blur-2xl transition-colors duration-300 ${isDarkMode ? 'bg-slate-900/50 border-slate-800/50' : 'bg-white/50 border-white/50'}`}>
        <div className="flex gap-2.5 relative">
          <textarea
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask anything about your data..."
            className={`flex-1 pl-5 text-[14px] pr-14 py-3.5 outline-none transition-all resize-none ${
               isDarkMode 
                 ? 'glass-button rounded-3xl bg-slate-800/50 border border-white/10 text-slate-200 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 shadow-inner ring-1 ring-white/5'
                 : 'glass-button rounded-3xl bg-white/60 border border-black/5 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 shadow-inner'
            }`}
            style={{ minHeight: '52px', maxHeight: '120px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={isThinking || !query.trim()}
            className="absolute right-1.5 bottom-1.5 top-1.5 bg-gradient-to-tr from-blue-600 to-indigo-500 text-white rounded-full w-[40px] hover:shadow-lg hover:shadow-blue-500/30 disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed transition-all shadow-md flex items-center justify-center shrink-0 group"
          >
            <Send size={18} strokeWidth={2.5} className="mr-0.5 ml-[-1px] group-active:scale-90 transition-transform" />
          </button>
        </div>
        <div className={`flex items-center justify-center gap-1.5 mt-3.5 text-[10.5px] font-bold tracking-wide uppercase transition-colors ${isDarkMode ? 'text-slate-500' : 'text-slate-400'}`}>
          <div className={`w-1.5 h-1.5 rounded-full shadow-sm ${isThinking ? 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)] animate-pulse' : 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)]'}`}></div>
          <div>{isThinking ? 'Dodge AI is analyzing...' : 'Powered by Dodge AI'}</div>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
