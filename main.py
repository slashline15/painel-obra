from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from scanner import FileScanner
import json
import os
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

# Detectar se está no railway
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") is not None

# Se produção, desabilita reload
if IS_PRODUCTION:
    # Railway vai setar a PORT automaticamente
    port = int(os.environ.get("PORT", 8000))

# Carregar variáveis de ambiente
load_dotenv()

# Configuração
BASE_PATH = os.getenv("BASE_PATH", r"I:\Meu Drive\DRIVE PREDIO ADM")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 300))
JSON_PATH = Path("file_data.json")

# Criar scanner
scanner = FileScanner(BASE_PATH)

# Scheduler global
scheduler = AsyncIOScheduler()

def do_local_scan():
    """Executa scan local e salva no JSON"""
    try:
        data = scanner.run_once()
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Scan salvo em {JSON_PATH}")
    except Exception as e:
        print(f"Erro no scan: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup
    print("Iniciando servidor HDAM...")
    
    # Faz scan inicial
    do_local_scan()
    
    # Configura scheduler
    scheduler.add_job(do_local_scan, 'interval', seconds=SCAN_INTERVAL)
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()

# Criar app FastAPI
app = FastAPI(
    title="HDAM Control API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - permite acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique seu domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def root():
    """Redireciona para o index.html"""
    return {"message": "HDAM Control API - Use /index.html"}

@app.get("/api/files")
async def get_files():
    """Retorna dados dos arquivos"""
    if not JSON_PATH.exists():
        do_local_scan()
    
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "disciplines": {}}

@app.post("/api/refresh")
async def refresh_files(background_tasks: BackgroundTasks):
    """Força atualização dos arquivos"""
    background_tasks.add_task(do_local_scan)
    return {"status": "refresh iniciado", "message": "Aguarde alguns segundos"}

@app.get("/api/status")
async def get_status():
    """Status do sistema"""
    return {
        "status": "online",
        "base_path": BASE_PATH,
        "scan_interval": SCAN_INTERVAL,
        "last_scan": JSON_PATH.stat().st_mtime if JSON_PATH.exists() else None
    }

@app.post("/api/notes/{discipline}/{filename}")
async def save_note(discipline: str, filename: str, note: dict):
    """Salva nota para um arquivo"""
    try:
        notes = scanner.notes
        note_key = f"{discipline}_{filename}"
        
        if note.get("content"):
            notes[note_key] = note["content"]
        else:
            notes.pop(note_key, None)
        
        scanner.save_notes()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}