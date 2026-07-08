import sqlite3
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
import subprocess
import time
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBasic()

# --- CAMINHO NATIVO VPS ---
DB_PATH = os.getenv("DATABASE_URL", "/home/ubuntu/dash-tokens-hermes/tokens.db") 
DOCS_PATH = "/home/ubuntu/documentos"

# --- SEGURANÇA: Valores padrão genéricos para portfólio público ---
DASH_USER = os.getenv("DASH_USER", "admin")
DASH_PASS = os.getenv("DASH_PASS", "password")
N8N_URL = os.getenv("N8N_URL", "https://n8n.example.com")
WEBUI_URL = os.getenv("WEBUI_URL", "https://webui.example.com")
SEARCH_URL = os.getenv("SEARCH_URL", "https://search.example.com")
OLLAMA_URL = os.getenv("OLLAMA_URL", "https://ollama.example.com")
EASYPANEL_URL = os.getenv("EASYPANEL_URL", "https://easypanel.example.com")
PIHOLE_URL = os.getenv("PIHOLE_URL", "https://pihole.example.com/admin/")
HERMES_URL = os.getenv("HERMES_URL", "https://hermes.example.com/")

last_cpu_time = 0
last_idle_time = 0

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != DASH_USER or credentials.password != DASH_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_system_metrics():
    global last_cpu_time, last_idle_time
    metrics = {"cpu": 0, "ram": 0, "disk": 0}
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
            parts = line.split()
            cpu_times = [float(x) for x in parts[1:]]
            idle = cpu_times[3] + cpu_times[4]
            total = sum(cpu_times)
            if last_cpu_time != 0:
                diff_idle = idle - last_idle_time
                diff_total = total - last_cpu_time
                metrics["cpu"] = 100.0 * (1.0 - diff_idle / diff_total) if diff_total > 0 else 0
            last_cpu_time = total
            last_idle_time = idle
    except: pass
    try:
        with open("/proc/meminfo", "r") as f:
            mem_info = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].split()[0])
            total = mem_info.get("MemTotal", 1)
            free = mem_info.get("MemAvailable", mem_info.get("MemFree", 0))
            metrics["ram"] = ((total - free) / total) * 100
    except: pass
    try:
        st = os.statvfs("/")
        metrics["disk"] = (1 - (st.f_bavail / st.f_blocks)) * 100
    except: pass
    return metrics

def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Ajuste para Fuso Horário de Brasília (UTC-3)
        cursor.execute("SELECT SUM(total_tokens), COUNT(*) FROM api_logs WHERE date(timestamp, '-3 hours') = date('now', '-3 hours')")
        today_tokens, today_reqs = cursor.fetchone()
        cursor.execute("SELECT SUM(total_tokens), COUNT(*) FROM api_logs")
        total_tokens, total_reqs = cursor.fetchone()
        cursor.execute('''
            SELECT date(timestamp, '-3 hours') as day, SUM(total_tokens) 
            FROM api_logs 
            WHERE timestamp >= date('now', '-3 hours', '-6 days') 
            GROUP by day 
            ORDER by day ASC
        ''')
        history = cursor.fetchall()
        conn.close()
        labels = [row[0] for row in history]
        values = [row[1] or 0 for row in history]
        if not labels:
            labels = ["Sem dados"]
            values = [0]
        return {
            "today_tokens": today_tokens or 0, 
            "today_reqs": today_reqs or 0, 
            "total_tokens": total_tokens or 0, 
            "total_reqs": total_reqs or 0,
            "chart_labels": labels,
            "chart_values": values
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stats")
async def api_stats(user: str = Depends(authenticate)):
    return JSONResponse(content={"stats": get_stats(), "sys_metrics": get_system_metrics()})

@app.get("/api/files")
async def list_files(user: str = Depends(authenticate)):
    try:
        if not os.path.exists(DOCS_PATH):
            os.makedirs(DOCS_PATH, exist_ok=True)
        files = os.listdir(DOCS_PATH)
        return JSONResponse(content={"files": files})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/download/{filename}")
async def download_file(filename: str, user: str = Depends(authenticate)):
    file_path = os.path.join(DOCS_PATH, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@app.get("/", response_class=HTMLResponse)
async def dashboard(user: str = Depends(authenticate)):
    stats = get_stats()
    sys_metrics = get_system_metrics()
    if "error" in stats:
        return f"<h1>Erro no Banco de Dados</h1><p>{stats['error']}</p>"
    
    try:
        with open("index.html", "r") as f:
            html_template = f.read()
    except FileNotFoundError:
        return HTMLResponse(content="Erro: Arquivo index.html não encontrado.")
    
    # --- INJEÇÃO SEGURA de LINKS ---
    replacements = {
        "{{N8N_URL}}": N8N_URL,
        "{{WEBUI_URL}}": WEBUI_URL,
        "{{SEARCH_URL}}": SEARCH_URL,
        "{{OLLAMA_URL}}": OLLAMA_URL,
        "{{EASYPANEL_URL}}": EASYPANEL_URL,
        "{{PIHOLE_URL}}": PIHOLE_URL,
        "{{HERMES_URL}}": HERMES_URL
    }
    for placeholder, url in replacements.items():
        html_template = html_template.replace(placeholder, url)
    
    return HTMLResponse(content=html_template)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
