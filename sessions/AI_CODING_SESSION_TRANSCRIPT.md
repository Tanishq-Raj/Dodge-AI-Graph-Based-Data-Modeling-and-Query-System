# **AI Coding Session Transcript & Collaboration Log**

### **Project:** Dodge AI - # Forward Deployed Engineer
### **Session Date:** March 25, 2026
### **Collaborators:** Human Engineer & AI Agent (Antigravity)

---

## **1. Introduction**
This document provides a detailed breakdown of the technical collaboration between the **Human Engineer** and the **AI Agent** during the development of **Dodge AI**, a premium ERP analytics copilot. This session highlights the high-quality **prompting**, **complex debugging**, and **iterative patterns** used to take the project from a basic prototype to a production-ready, glassmorphic application.

---

## **2. Evaluation Criteria 1: Prompt Quality**
Effective AI-driven development depends on the quality of the "human-in-the-loop" steering. The session involved highly specific, layered prompts that forced the AI to solve multiple constraints simultaneously.

### **Example: The "Vision" Prompt**
> **USER:** *"change nodes color and graph edges color to vibrant and unique... make containers in full project, add glassmorphic design, make the color scheme, design layout, ui look user friendly and interactive... in the night mode, it is not clearly seen, maintain the color combination and look it good"*

**AI Analysis & Multi-Task Execution:**
- **Constraint 1 (Data Viz):** Map document types to distinct vibrance hex codes to ensure nodes are "distinguished" at a glance.
- **Constraint 2 (Styling):** Implement `backdrop-filter` and semi-transparent layers for the "glassmorphic" feel.
- **Constraint 3 (Accessibility):** Adjust HSL values for the dark mode version of the glass panels to ensure "vibrant nodes" don't wash out against the background.

---

## **3. Evaluation Criteria 2: Debugging Workflow**
One of the core technical challenges was the **Cross-Platform Proxy Issue** during the transition from local development to Vercel/Render hosting.

### **The Incident: Vercel 404 & CORS Errors**
1.  **Symptom:** The frontend on Vercel was failing to connect to the backend on Render, returning `404 Not Found` for all `/api/` calls.
2.  **AI Debugging Approach:**
    -   **Step 1:** Inspected the client-side `fetch` calls. Detected they were using relative paths (`/api/stats`), which Vercel interpreted as local static assets.
    -   **Step 2:** Identified that the backend was hosted on a different domain (`onrender.com`).
    -   **Step 3:** Instead of hardcoding the full URL in every React component (which creates technical debt), the AI proposed and implemented a **`vercel.json` rewrite rule**.
    -   **Result:** This "invisible proxy" allowed the frontend to remain clean while routing traffic securely to the live API.

---

## **4. Evaluation Criteria 3: Iteration Patterns**
The project iterated rapidly through several architectural generations.

### **Iteration 1: Logic Refinement**
- **Initial:** The system used simple keyword matches.
- **Improvement:** At the User's direction, the AI implemented a **Local NLP Intent Detection Engine** using synonym-expanded vocabularies, ensuring that "where is my stuff?" correctly maps to the `trace_order` intent without needing an expensive LLM call for simple requests.

### **Iteration 2: Graphical Interactivity**
- **Initial:** Basic Cytoscape dots.
- **Improvement:** Added **dynamic interaction hooks**. When a user in the chat asks "What is order 740509?", the chat interface sends a signal to the Graph Panel to **auto-zoom and highlight** that specific node, creating a truly integrated "Copilot" experience.

---

## **5. Technical Architecture Decisions**
| **Layer** | **Decision** | **Justification** |
| :--- | :--- | :--- |
| **Backend** | FastAPI | High-speed, typed Python engine ideal for ERP processing. |
| **Logic** | Text-to-SQL | Allows the LLM to query the SQLite DB directly using CTEs and Joins. |
| **Styling** | Vanilla Glassmorphism | Avoids generic UI kits. Every component feels unique and custom-crafted. |
| **Guardrails** | Domain Whitelisting | Prevents the AI from discussing non-ERP topics, ensuring data sovereignty. |

---

## **6. Conclusion**
The collaboration between the Human Engineer's creative vision and the AI Agent's technical execution has resulted in a world-class ERP tool. By utilizing high-quality prompts and iterative refinement, Dodge AI has evolved from a simple data tool into a premium, interactive "Graph Intelligence" engine.

---
**END OF SESSION LOG**
**Exported for Evaluation Review.**
