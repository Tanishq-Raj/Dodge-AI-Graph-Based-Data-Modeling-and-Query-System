# Upgrade: Keyword-Match → LLM Intent Detection

- [x] **Backend: LLM Intent Detector**
  - [x] Add `detect_intent(query)` → calls LLM → returns `{intent, entities}`
  - [x] Define intent types: trace_order, show_orders, billing_analysis, explain, fraud_check, etc.

- [x] **Backend: Intent-Based SQL**
  - [x] Replace keyword `generate_sql()` with `generate_sql_from_intent(intent, entities)`
  - [x] Deterministic SQL per intent, no more `if "trace" in q`

- [x] **Backend: LLM Summary**
  - [x] Add `generate_llm_summary(query, result)` for clean natural language answers
  - [x] Fallback to rule-based if LLM fails

- [x] **Backend: Conditional Highlights**
  - [x] Only return `highlights` for trace/graph intents
  - [x] Empty highlights for show_orders, billing_analysis, etc.

- [x] **Frontend: Smart Graph Control**
  - [x] Only highlight when highlights array is non-empty
  - [x] Clear previous highlights for non-graph queries

- [x] **Verification**
  - [x] curl test all intents
  - [x] Browser demo

- [x] **Feature: Visual Flow Trace in Chat**
  - [x] Add `renderFlowTrace` component to `ChatPanel.jsx`
  - [x] Render document chain with arrows (Order → Delivery → Billing → Journal)
  - [x] Support clicking on IDs in the flow to highlight them in the graph
  - [x] Sync `main.py` and `main_OPENROUTER_FINAL.py` for correct flow data output
- [x] **Feature: Resizable Chat Panel**
  - [x] Add `chatWidth` state to `App.jsx`
  - [x] Implement draggable resize handle between Graph and Chat panels
  - [x] Update `ChatPanel.jsx` to accept and use dynamic width
  - [x] Add min/max width constraints for better UX

- [x] **Feature: Monorepo Refactor for Deployment**
  - [x] Create `backend/` and `frontend/` directories
  - [x] Move backend logic and DB to `backend/`
  - [x] Create `backend/requirements.txt`
  - [x] Update frontend to use `import.meta.env.VITE_API_URL`
  - [x] Create `frontend/.env` for local development
  - [x] Verify local run in browser
  - [x] Commit all changes locally (Monorepo + Updates)
  - [x] Final Push to GitHub (Success 🚀)
  - [x] Fix Vercel 404: Add `frontend/vercel.json` and push
  - [x] Fix API 422: Refactor `/query` from GET to POST
  - [x] Fix Vercel Data: Implementation of Zero-Config API Proxy
  - [x] Fix Node Context: Dynamic `node-explanation` API & NaN cleanup
  - [x] Verify Fixed Application in Browser 🚀

# Upgrade: Premium Glassmorphic Redesign & Graph Enhancements

- [x] **Graph Visualization**
  - [x] Shift colors to vibrant, distinct theme (SalesOrder = Blue, Delivery = Cyan, etc.)
  - [x] Enhance edges (thicker, brighter) for better visibility
  - [x] Verify readability in both Light Mode and Dark Mode

- [x] **Glassmorphic UI Redesign**
  - [x] Add dynamic, animated CSS mesh background in `index.css`
  - [x] Implement `.glass-panel` and `.glass-button` utility classes
  - [x] Wrap `App.jsx` layout panels in frosted glass containers
  - [x] Refactor `ChatPanel.jsx` bubbles and layout
  - [x] Replace fixed suggestion chips with a beautiful "empty state"
  - [x] Refactor `GraphPanel.jsx` overlay components

- [x] **Documentation & Deployment**
  - [x] Create comprehensive `deployment_guide.md` for Vercel + Render
  - [x] Sync all documentation into `DOCS` and `sessions` folders
