# Complete Free Deployment Guide: Dodge AI ERP Copilot

Deploying this full-stack React + FastAPI application is straightforward and entirely free using **GitHub**, **Render** (for the backend API), and **Vercel** (for the frontend). 

The project is actually already pre-configured for this setup! Notice that your `frontend/vercel.json` file is already set up to proxy API requests to a Render URL.

---

## Step 1: Push Your Code to GitHub
Both Render and Vercel deploy automatically from GitHub repositories.
1. Go to [GitHub.com](https://github.com/) and create a new, private or public repository (e.g., `dodge-ai-erp-copilot`).
2. Open your terminal in the project root (`d:\Dodge-AI-ERP-Copilot-main`) and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit, complete with glassmorphism UI"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/Dodge-AI-Graph-Based-Data-Modeling-and-Query-System.git
   git push -u origin main
   ```

---

## Step 2: Deploy the Backend for Free on Render
Render provides an excellent free tier for Python web services.

1. Create a free account at [Render.com](https://render.com/).
2. Click **New** -> **Web Service**.
3. Connect your GitHub account and select your `dodge-ai-erp-copilot` repository.
4. Fill in the deployment details:
   - **Name:** `dodge-ai-erp-copilot` *(this must match the URL in your `vercel.json` if you want the proxy to work without editing it)*
   - **Language:** Python 3
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn dodge_ai:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables (Important):**
   - Click "Advanced" -> "Add Environment Variable".
   - Key: `GEMINI_API_KEY` | Value: *(Paste your Gemini API key here)*
6. Select the **Free** tier and click **Create Web Service**. 
7. *(Optional)* After deployment finishes, copy the Render URL. If it's different from ``, you'll need to update `frontend/vercel.json` with the new URL and push that change to GitHub.

---

## Step 3: Deploy the Frontend for Free on Vercel
Vercel handles React apps perfectly, and the `vercel.json` is already configured to connect your frontend to the Render backend safely without CORS issues.

1. Create a free account at [Vercel.com](https://vercel.com/signup).
2. Click **Add New** -> **Project**.
3. Connect your GitHub account and import your `dodge-ai-erp-copilot` repository.
4. Fill in the deployment details:
   - **Framework Preset:** Vite
   - **Root Directory:** Edit this and select `frontend` instead of the root.
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Click **Deploy**. Vercel will automatically build the frontend.

---

## Testing Your Live Site
Once Vercel finishes deploying, they will provide you a live URL (e.g., `https://dodge-ai-erp-copilot.vercel.app`). 

1. Visit that URL.
2. The frontend will load and attempt to fetch the graph from `/api/graph`. 
3. Behind the scenes, Vercel routes `/api/*` to your free Render server securely!

> [!NOTE]
> **Free Tier Cold Starts:** Render's free tier automatically "spins down" your backend if no one visits the site for 15 minutes. When you first load the site after a break, it might take 30-50 seconds for the backend to wake up. The frontend loading screen (`Initializing intelligence engine...`) is perfectly designed to cover up this delay gracefully!

> [!WARNING]
> **Ephemeral Disk:** Any uploaded documents or CSVs might be erased when the Render free server restarts. Since this project loads from a static SQLite `data.db`, everything should work perfectly out-of-the-box without issues.
