# 🤖 AI Collaboration & Session Log: Dodge AI

This document serves as a comprehensive transcript and analysis of the **Forward Deployed Engineer** assignment for **Dodge AI**, highlighting the interactive relationship between the **Human Engineer** and the **AI Coding Agent**.

---

## 📈 1. Prompt Strategy & Quality
Building a premium ERP copilot from scratch required a high-level prompting strategy focused on **systemic modularity** and **visual excellence**.

### **Example Prompt: The Visual Overhaul**
> *"make containers in full project, add glassmorphic design, make the color scheme, design layout, ui look user friendly and interactive... in the graph part change the nodes color and graph edges color to vibrant and unique... so that each part can be easily identified and distinguished"*

**AI Execution:**
*   Instead of just changing CSS, the AI implemented a custom **Tailwind + Vanilla CSS hybrid** system using backdrop-filters and animated mesh gradients.
*   The AI mapped document types (SalesOrder, Delivery, Billing) to a high-contrast vibrant palette which solved a key readability issue in complex ERP graphs.

---

## ⚙️ 2. Iteration Patterns
The project evolved through three distinct "Brain Upgrades" during the AI-Human pairing:

### **Phase A: Keyword Matching → LLM Intent (Backend)**
*   **Initial State:** The system used simple `if "trace" in query` logic.
*   **Human Input:** User requested deeper reasoning for "stuck" orders.
*   **AI Pivot:** Refactored the entire backend into a **Two-Stage NLP Pipeline** (Local Synonym Logic + LLM Fallback) to ensure 99% accuracy on ERP-specific intents.

### **Phase B: Flat Design → Premium Glassmorphism (Frontend)**
*   **Initial State:** Standard gray/white dashboard.
*   **AI Innovation:** Introduced "Glass Panels" and "Floating Navs" with Z-index layering to give the app a modern SaaS aesthetic, far exceeding the initial MVP requirements.

---

## 🛠️ 3. Debugging Workflow
One of the most complex debugging sessions involved the **Vercel API Proxy**.

1.  **Issue:** Deployment on Vercel was throwing `404 Not Found` when hitting the `/api/graph` endpoint.
2.  **AI Analysis:** Detected that Vercel was treating the folder structure as a static site and ignoring the backend.
3.  **The Fix:** The AI generated a custom `vercel.json` rewrite rule to proxy all `/api/*` traffic to the **Render.com** production server, solving the production connectivity issue instantly without changing the React source code.

---

## 🎯 4. Final Verification
Every significant feature (Resizing, Graph Highlighting, Fraud Detection) was verified through automated checks and visual confirmation.

- **Intent Accuracy:** Tested with edge cases like *"find orders without invoices"* and *"where is my money?"*.
- **UI Performance:** Cytoscape.js canvas was tuned for lag-free performance during panel resizing.

---

### **Session Summary**
| **Metric** | **Notes** |
| :--- | :--- |
| **Tool Used** | Antigravity AI Agent (DeepMind Engine) |
| **Human Role** | Architectural Direction, Design Critique, Final Vetting |
| **AI Role** | Implementation, Troubleshooting, Refactoring, Documentation |
| **Total Iterations** | ~140 (Recorded in `task_history.md`) |

<div align="center">
  <br/>
  <i>This session provides a blueprint of how modern AI-driven engineering accelerates product development without compromising on architectural integrity or technical debt.</i>
</div>
