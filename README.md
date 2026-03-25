<div align="center">
  <img src="https://img.shields.io/badge/Dodge_AI-ERP_Copilot-blue?style=for-the-badge&logo=sap" alt="Dodge AI Logo" />
  <h1>🚀 Dodge AI: # Forward Deployed Engineer - Task Details</h1>
  <h3>Graph-Based Data Modeling and Query System</h3>
  <p><em>A powerful, visual ERP analytics tool combining dynamic graph visualization with a conversational AI Copilot to deliver deep business intelligence into the Order-to-Cash (O2C) pipeline.</em></p>

  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
  [![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
</div>

<br />

## ✨ Features

- **🧠 Intelligent Query Engine:** Ask questions in plain English (e.g., *"Find all stuck deliveries"* or *"Explain order 740509"*). The built-in LLM detects your exact intent, generates structured SQL, and returns human-readable summaries.
- **🕸️ Cytoscape Graph Visualization:** Every transaction is rendered dynamically on a glassmorphic canvas. See the precise relationships between Sales Orders, Deliveries, Billing Docs, and Journals.
- **🎨 Premium UI/UX:** Built with a stunning dark/light glassmorphic mesh UI that makes data analytics visually impressive.
- **🚀 Zero-Config Proxy:** A fully decoupled standard monorepo setup ready for immediate Vercel/Render deployment.

---

## 🏗️ System Architecture & Working Flow

The following sequence diagram outlines how user queries are processed and returned visually.

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React / Vite (UI)
    participant API as FastAPI (Backend)
    participant LLM as Action LLM
    participant DB as SQLite (data.db)

    User->>Frontend: "Track order #740509"
    Frontend->>API: POST /query {"query": ...}
    
    API->>LLM: Identify Intent & Extract Entities
    LLM-->>API: {intent: "trace_order", id: 740509}
    
    API->>DB: Execute Intent-Specific SQL
    DB-->>API: Raw Graph Data (Nodes & Edges)
    
    API->>LLM: Generate Natural Language Summary
    LLM-->>API: Formatted Markdown Explanation
    
    API-->>Frontend: JSON {summary, nodes, edges}
    
    Frontend->>Frontend: Plot Graph (Cytoscape)<br/>Render Chat Bubble (Glassmorphic)
    Frontend-->>User: Visual Graph + Smart Context
```

---

## 📁 Repository Structure (Monorepo)
Your project is now organized for professional deployment:
```
dodge-ai/
 ├── backend/            # FastAPI + SQLite
 │    ├── dodge_ai.py    # Main API
 │    ├── data.db        # Database
 │    └── requirements.txt
 └── frontend/           # React (Vite)
      ├── src/           # UI Components
      └── .env           # Environment config
```

---

## 🛠️ Setup Instructions

### 1. Local Development
#### Backend (Terminal 1)
```bash
cd backend
pip install -r requirements.txt
uvicorn dodge_ai:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```

### 2. Production Deployment
- **Backend:** Deploy on free tier at **Render.com** (Root: `backend`, Command: `uvicorn dodge_ai:app --host 0.0.0.0 --port $PORT`).
- **Frontend:** Deploy on **Vercel** (Root: `frontend`, Framework: `Vite`).
- **API Connectivity:** The provided `vercel.json` automatically proxies `/api/*` network calls securely to the Render backend!

---

## 🔗 Project Links
- [GitHub Repository](https://github.com/Tanishq-Raj/Dodge-AI-Graph-Based-Data-Modeling-and-Query-System.git)

<div align="center">
  <br/>
  <i>Engineered for unparalleled ERP operational intelligence.</i>
</div>
