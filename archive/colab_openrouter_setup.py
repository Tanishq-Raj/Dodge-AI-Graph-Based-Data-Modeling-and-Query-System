import os
import subprocess
import threading
import time
import nest_asyncio
from pyngrok import ngrok, conf

# ================================
# COLAB OPENROUTER DEPLOYMENT SETUP
# ================================

NGROK_TOKEN    = "apna_ngrok_token"      # GET FROM dashboard.ngrok.com
OPENROUTER_KEY = "sk-or-v1-xxxxx"       # GET FROM openrouter.ai

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_KEY
conf.get_default().auth_token = NGROK_TOKEN

def run_server():
    nest_asyncio.apply()
    # Ensure it's pointing to the FINAL main file
    subprocess.run(['python', '-m', 'uvicorn', 'main_OPENROUTER_FINAL:app', '--host', '0.0.0.0', '--port', '8000'])

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(5)

try:
    tunnel = ngrok.connect(8000, 'http')
    print("=" * 60)
    print("🔥 DODGE AI IS LIVE! 🔥")
    print(f"✅ PUBLIC URL: {tunnel.public_url}")
    print(f"SET THIS IN index.html:\\nconst API_BASE = '{tunnel.public_url}';")
    print("=" * 60)
except Exception as e:
    print("⚠️ Ngrok failed:", e)

while True: 
    time.sleep(100)
