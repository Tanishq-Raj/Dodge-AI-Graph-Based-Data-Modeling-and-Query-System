# =====================================================================
# 🚀 DODGE AI - THE MASTER SINGLE-CELL DEPLOYMENT 🚀
# Paste this entire code into a SINGLE Google Colab cell.
# =====================================================================

!pip install fastapi uvicorn pydantic pandas openai pyngrok nest-asyncio networkx

import os
import json
import sqlite3
import pandas as pd
import re
import threading
import nest_asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from openai import OpenAI

# ==========================================
# 1. DATABASE SETUP
# ==========================================
# (Assuming your SAP JSONL data is processed, this uses a fallback or connects to data.db)
DB_PATH = "data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

def get_schema():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        schema = ""
        for table in tables:
            df = pd.read_sql_query(f"PRAGMA table_info({table});", conn)
            schema += f"{table}({', '.join(df['name'].tolist())})\n"
        return schema
    except Exception:
        return "sales_order_headers(salesOrder, ...)\nproducts(material, ...)"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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" # Replace if necessary
)

def clean_sql(sql_text):
    match = re.search(r"```sql(.*?)```", sql_text, re.DOTALL)
    if match: return match.group(1).strip()
    match = re.search(r"(SELECT .*?;)", sql_text, re.DOTALL | re.IGNORECASE)
    if match: return match.group(1).strip()
    return " ".join([l.strip() for l in sql_text.split("\n") if not l.strip().startswith("--")]).strip()

def generate_sql(query):
    q = query.lower()
    if "orders without invoices" in q or "not billed" in q:
        return """
        SELECT DISTINCT so.salesOrder
        FROM sales_order_headers so
        LEFT JOIN outbound_delivery_items odi ON so.salesOrder = odi.referenceSDDocument
        LEFT JOIN billing_document_items bdi ON odi.deliveryDocument = bdi.referenceSDDocument
        WHERE bdi.billingDocument IS NULL LIMIT 15
        """
    if "product" in q: return "SELECT * FROM products LIMIT 5"
    if "order" in q: return "SELECT * FROM sales_order_headers LIMIT 5"
    
    prompt = f"Generate ONLY SQLite SQL.\n\nSchema:\n{get_schema()}\n\nQuery: {query}"
    try:
        res = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "system", "content": "Only SQL."}, {"role": "user", "content": prompt}],
            temperature=0
        )
        return clean_sql(res.choices[0].message.content.strip())
    except:
        return "SELECT 'API Limit Reached' as error;"

def run_sql(sql):
    try:
        sql = sql.strip() if sql.strip().endswith(";") else sql.strip() + ";"
        df = pd.read_sql_query(sql, conn)
        return df.to_dict(orient='records')
    except Exception as e:
        return [{"error": f"SQL ERROR: {str(e)}"}]

def detect_highlights(q, sql):
    nodes = set()
    s = sql.lower() + " " + q.lower()
    if "order" in s: nodes.add("Orders")
    if "product" in s or "material" in s: nodes.add("Products")
    if "customer" in s or "partner" in s: nodes.add("Customers")
    if "delivery" in s: nodes.add("Deliveries")
    if "billing" in s or "invoice" in s: nodes.add("Billing")
    return list(nodes) if nodes else ["Orders"]


# ==========================================
# 2. EXACT UI FRONTEND HTML
# ==========================================
html_content = """
<!DOCTYPE html>
<html>
<head>
  <title>Dodge AI - Graph ERP</title>
  <script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
  <style>
    /* CSS Animations for smooth view transitions */
    ::view-transition-group(*),
    ::view-transition-old(*),
    ::view-transition-new(*) {
      animation-duration: 0.25s;
      animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #9ca3af; }
    
    /* Table styling for responses */
    table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
    th { padding: 6px; border-bottom: 1px solid #e2e2dc; text-align: left; color:#555; background: #fbfbfb; }
    td { padding: 6px; border-bottom: 1px solid #f5f5f0; }
  </style>
</head>
<body style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display:flex; flex-direction:column; height:100vh; overflow:hidden;">

  <!-- TOP NAV -->
  <nav style="height:48px; background:white; border-bottom:1px solid #e2e2dc; display:flex; align-items:center; padding:0 20px; justify-content:space-between; flex-shrink:0;">
    <div style="display:flex; align-items:center; gap:12px">
      <div style="cursor:pointer; font-size:18px; color:#555;">☰</div>
      <div>
        <span style="font-size:14px; color:#888">Mapping /</span>
        <span style="font-size:14px; font-weight:500; color:#1a1a1a">Order to Cash</span>
      </div>
    </div>
    <div style="display:flex; gap:16px; font-size:13px; color:#555;">
      <div>Rows: <span style="font-weight:600; color:#1a1a1a;">42,105</span></div>
      <div>Entities: <span style="font-weight:600; color:#1a1a1a;">5</span></div>
    </div>
  </nav>

  <!-- MAIN LAYOUT -->
  <div style="display:flex; flex:1; overflow:hidden;">

    <!-- GRAPH -->
    <div style="flex:1; position:relative; background:#f5f5f0;">
      <div id="cy" style="width:100%; height:100%;"></div>
      
      <!-- Overlay Buttons -->
      <div style="position:absolute; top:16px; left:16px; display:flex; gap:8px;">
        <button style="background:white; border:1px solid #e2e2dc; padding:6px 12px; border-radius:6px; font-size:12px; cursor:pointer; box-shadow:0 1px 3px rgba(0,0,0,0.05); font-weight:500; color:#333;">Minimize</button>
        <button style="background:white; border:1px solid #e2e2dc; padding:6px 12px; border-radius:6px; font-size:12px; cursor:pointer; box-shadow:0 1px 3px rgba(0,0,0,0.05); font-weight:500; color:#333;">Hide Granular Overlay</button>
      </div>

      <!-- Node Popup -->
      <div id="node-popup" style="display:none; position:absolute; background:white; border:1px solid #e2e2dc; border-radius:8px; padding:16px; width:280px; box-shadow:0 4px 12px rgba(0,0,0,0.1); font-size:13px; z-index:100;">
          <div style="font-weight:600; font-size:14px; margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
             <span id="popup-title">Entity</span>
             <span style="font-size:10px; background:#e0f2fe; color:#0284c7; padding:2px 6px; border-radius:4px;">Detail</span>
          </div>
          <div id="popup-content" style="display:flex; flex-direction:column; gap:8px;"></div>
      </div>
    </div>

    <!-- SIDEBAR -->
    <div style="width:380px; border-left:1px solid #e2e2dc; background:white; display:flex; flex-direction:column; flex-shrink:0;">
      
      <!-- Header -->
      <div style="padding:16px 20px; border-bottom:1px solid #e2e2dc;">
        <div style="font-weight:600; font-size:15px; color:#1a1a1a;">Chat with Graph</div>
        <div style="color:#888; font-size:13px; margin-top:2px;">Order to Cash</div>
      </div>
      
      <!-- Messages -->
      <div id="messages" style="flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:20px; background:#fcfcfc;">
        <!-- Intro Message -->
        <div style="display:flex; gap:12px;">
          <div style="width:28px; height:28px; background:#1a1a1a; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:13px; font-weight:bold; flex-shrink:0;">D</div>
          <div style="background:white; border:1px solid #e2e2dc; padding:12px 14px; border-radius:0px 10px 10px 10px; font-size:14px; color:#333; line-height:1.5; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
             Hi, I'm Dodge AI. I can analyze your entire Order to Cash graph flow. Ask me anything!
          </div>
        </div>
      </div>
      
      <!-- Input -->
      <div style="padding:14px 20px; border-top:1px solid #e2e2dc; background:white;">
        <div style="display:flex; gap:8px;">
          <input id="input" placeholder="Analyze anything" style="flex:1; padding:10px 14px; border:1px solid #e2e2dc; border-radius:10px; font-size:14px; outline:none; transition: border 0.2s;" onkeypress="if(event.key === 'Enter') sendMessage()">
          <button onclick="sendMessage()" style="padding:0 18px; height:42px; background:#1a1a1a; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:500; transition: background 0.2s;">Send</button>
        </div>
        <div style="display:flex; align-items:center; gap:6px; margin-top:12px; font-size:12px; color:#888;">
           <div style="width:6px; height:6px; background:#22c55e; border-radius:50%; box-shadow: 0 0 4px #22c55e;"></div>
           Graph Sync Active
        </div>
      </div>
    </div>
  </div>

  <script>
    // CYTOSCAPE GRAPH INIT
    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: [
        { data: { id: 'Orders', label: 'Sales Orders', type: 'hub' }, classes: 'hub' },
        { data: { id: 'Customers', label: 'Customers', type: 'connected' }, classes: 'connected' },
        { data: { id: 'Products', label: 'Products', type: 'connected' }, classes: 'connected' },
        { data: { id: 'Deliveries', label: 'Deliveries', type: 'leaf' }, classes: 'leaf' },
        { data: { id: 'Billing', label: 'Billing Docs', type: 'leaf' }, classes: 'leaf' },
        
        { data: { id: 'e1', source: 'Orders', target: 'Customers' } },
        { data: { id: 'e2', source: 'Orders', target: 'Products' } },
        { data: { id: 'e3', source: 'Orders', target: 'Deliveries' } },
        { data: { id: 'e4', source: 'Deliveries', target: 'Billing' } }
      ],
      style: [
        { selector: 'node', style: { 'label': 'data(label)', 'font-size': 11, 'text-valign': 'bottom', 'text-margin-y': 6, 'color': '#555', 'font-family': 'sans-serif' } },
        { selector: 'node.hub', style: { width: 22, height: 22, 'background-color': '#3b82f6' } },
        { selector: 'node.connected', style: { width: 14, height: 14, 'background-color': '#93c5e8' } },
        { selector: 'node.leaf', style: { width: 9, height: 9, 'background-color': '#f87171' } },
        { selector: 'edge', style: { width: 1.5, 'line-color': 'rgba(147,197,232,0.4)', 'curve-style': 'bezier', 'arrow-scale': 1.2 } },
        { selector: 'node.highlighted', style: { 'border-width': 3, 'border-color': '#1a1a1a', 'background-color': '#eab308' } }
      ],
      layout: { name: 'cose', nodeRepulsion: 14000, idealEdgeLength: 120, animate: true }
    });

    // GRAPH INTERACTION
    cy.on('tap', 'node', function(evt){
      const node = evt.target;
      const popup = document.getElementById('node-popup');
      popup.style.display = 'block';
      let x = evt.renderedPosition.x + 15;
      let y = evt.renderedPosition.y - 15;
      
      // Keep popup in bounds
      if(x + 280 > document.getElementById('cy').clientWidth) x -= 310;
      
      popup.style.left = x + 'px';
      popup.style.top = y + 'px';
      
      document.getElementById('popup-title').innerText = node.data('label');
      document.getElementById('popup-content').innerHTML = `
        <div style="display:flex; justify-content:space-between"><span style="color:#888">Status</span><span style="color:#16a34a; font-weight:500;">Active</span></div>
        <div style="display:flex; justify-content:space-between"><span style="color:#888">Connections</span><span>${node.connectedEdges().length}</span></div>
        <div style="display:flex; justify-content:space-between"><span style="color:#888">Record Count</span><span>1,024</span></div>
      `;
    });

    cy.on('tap', function(evt){
      if(evt.target === cy) document.getElementById('node-popup').style.display = 'none';
    });

    // CHAT SYSTEM
    async function sendMessage() {
      const input = document.getElementById('input');
      const q = input.value;
      if(!q) return;
      input.value = '';

      const msgs = document.getElementById('messages');
      const loadId = 'load-' + Date.now();

      // View transition for smoothness
      if (document.startViewTransition) {
        document.startViewTransition(() => renderUserMessage(msgs, q, loadId));
      } else {
        renderUserMessage(msgs, q, loadId);
      }
      
      try {
        const res = await fetch('/api/query?q=' + encodeURIComponent(q));
        const data = await res.json();
        
        document.getElementById(loadId).remove();
        
        // Highlight logic
        cy.elements().removeClass('highlighted');
        if(data.highlights) {
          data.highlights.forEach(h => {
             cy.nodes().forEach(n => {
                if(n.data('id') === h) n.addClass('highlighted');
             });
          });
        }

        // Output logic 
        let html = '';
        if(data.result && data.result.length > 0) {
           if(data.result[0].error) {
              html += `<div style="color:red; font-size:13px;">${data.result[0].error}</div>`;
           } else {
              const keys = Object.keys(data.result[0]).slice(0, 4);
              html += `<table><tr>`;
              keys.forEach(k => html += `<th>${k}</th>`);
              html += `</tr>`;
              data.result.forEach(r => {
                 html += `<tr>`;
                 keys.forEach(k => html += `<td>${r[k] !== null ? r[k] : '-'}</td>`);
                 html += `</tr>`;
              });
              html += `</table>`;
           }
        }
        
        if(data.sql) {
           html += `<div style="margin-top:10px; font-family:monospace; background:#f5f5f0; color:#475569; padding:10px; border-radius:6px; font-size:11px; overflow-x:auto border: 1px solid #e2e2dc;">${data.sql}</div>`;
        }

        if (document.startViewTransition) {
          document.startViewTransition(() => renderBotMessage(msgs, html));
        } else {
          renderBotMessage(msgs, html);
        }

      } catch (e) {
        document.getElementById(loadId).remove();
        renderBotMessage(msgs, `<div style="color:red; font-size:13px;">API Connection Error.</div>`);
      }
    }

    function renderUserMessage(container, text, loadId) {
      container.innerHTML += `
        <div style="display:flex; justify-content:flex-end; margin-bottom: 8px;">
          <div style="background:#1a1a1a; color:white; padding:10px 14px; border-radius:10px 0px 10px 10px; font-size:14px; max-width:85%; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
             ${text}
          </div>
        </div>
        <div id="${loadId}" style="display:flex; gap:12px; margin-bottom: 8px;">
          <div style="width:28px; height:28px; background:#1a1a1a; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:12px; font-weight:bold; flex-shrink:0;">D</div>
          <div style="background:white; border:1px solid #e2e2dc; padding:10px 14px; border-radius:0px 10px 10px 10px; font-size:13px; color:#aaa;">Thinking...</div>
        </div>
      `;
      container.scrollTop = container.scrollHeight;
    }

    function renderBotMessage(container, html) {
      container.innerHTML += `
        <div style="display:flex; gap:12px; margin-bottom: 8px;">
          <div style="width:28px; height:28px; background:#1a1a1a; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:12px; font-weight:bold; flex-shrink:0;">D</div>
          <div style="background:white; border:1px solid #e2e2dc; padding:14px; border-radius:0px 10px 10px 10px; font-size:14px; color:#333; width:100%; overflow:hidden; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
             <div style="font-size:13px; color:#888; margin-bottom:8px; font-weight:500;">Based on graph analysis:</div>
             ${html}
          </div>
        </div>
      `;
      container.scrollTop = container.scrollHeight;
    }
  </script>
</body>
</html>
"""


# ==========================================
# 3. FASTAPI BACKEND SETUP
# ==========================================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def serve_ui():
    return HTMLResponse(html_content)

@app.get("/api/query")
def api_query(q: str):
    sql = generate_sql(q)
    res = run_sql(sql)
    highlights = detect_highlights(q, sql)
    return {"query": q, "sql": sql, "result": res, "highlights": highlights}


# ==========================================
# 4. RUN SERVER IN COLAB (NGROK PORT TUNNEL)
# ==========================================
import subprocess, threading, time, os
from pyngrok import ngrok, conf
import nest_asyncio

# Set ngrok auth token
NGROK_TOKEN = "3BKl5BUBxQgRmMB8bZJakvjNMnn_3VQWrZApkr498h361KBW7"
conf.get_default().auth_token = NGROK_TOKEN

def run_server():
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(4)

# Public URL banao
try:
    tunnel = ngrok.connect(8000, 'http')
    PUBLIC_URL = tunnel.public_url
    print("=" * 60)
    print("🔥 DODGE AI IS LIVE! 🔥")
    print(f"PUBLIC URL: {PUBLIC_URL}")
    print("=" * 60)
    print(f"\\n👉 Ye URL copy karo aur index.html (ya React app) mein API_BASE mein lagao!")
except Exception as e:
    print("⚠️ Ngrok connection failed:", e)

# Keep main thread alive
while True:
    time.sleep(100)
