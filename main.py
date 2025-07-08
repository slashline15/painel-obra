from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import json
import os
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from drive_scanner import DriveScanner

# Carregar variáveis de ambiente
load_dotenv()

# --- Configuração ---
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 900))  # 15 minutos
JSON_PATH = Path("file_data.json")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# --- Validação de Credenciais ---
if not GOOGLE_CREDS_JSON:
    raise ValueError("A variável de ambiente GOOGLE_CREDS_JSON não foi definida.")

try:
    credentials_info = json.loads(GOOGLE_CREDS_JSON)
except json.JSONDecodeError:
    raise ValueError("GOOGLE_CREDS_JSON não é um JSON válido.")

# --- Scanner ---
scanner = DriveScanner(credentials_info)
scheduler = AsyncIOScheduler()

def do_drive_scan():
    """Executa o scan do Google Drive e salva o resultado em JSON."""
    try:
        data = scanner.run_once()
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Scan do Drive salvo com sucesso em {JSON_PATH}")
    except Exception as e:
        print(f"Erro durante o scan do Drive: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    print("Iniciando servidor HDAM Control...")
    
    # Executa o primeiro scan imediatamente
    do_drive_scan()
    
    # Agenda scans recorrentes
    scheduler.add_job(do_drive_scan, 'interval', seconds=SCAN_INTERVAL)
    scheduler.start()
    
    yield
    
    # Desliga o scheduler ao finalizar
    print("Desligando scheduler...")
    scheduler.shutdown()

# --- Aplicação FastAPI ---
app = FastAPI(
    title="HDAM Control API",
    version="2.0.0",
    description="API para servir arquivos de projeto do Google Drive.",
    lifespan=lifespan
)

# --- Middlewares ---
# Em produção, restrinja as origens para o seu domínio
allowed_origins = [os.getenv("FRONTEND_URL", "*")]
app.add_middleware (
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Rotas da API ---
@app.get("/api/files")
async def get_files():
    """Retorna os dados dos arquivos cacheados do Drive."""
    if not JSON_PATH.exists():
        return {"error": "Cache de arquivos ainda não foi criado.", "disciplines": {}}
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler cache: {e}")

@app.post("/api/refresh")
async def refresh_files(background_tasks: BackgroundTasks):
    """Dispara uma nova varredura do Google Drive em segundo plano."""
    background_tasks.add_task(do_drive_scan)
    return {"status": "success", "message": "Atualização iniciada em segundo plano."}

@app.get("/api/status")
async def get_status():
    """Retorna o status do sistema."""
    return {
        "status": "online",
        "service": "Google Drive Mode",
        "scan_interval_seconds": SCAN_INTERVAL,
        "last_scan_timestamp": JSON_PATH.stat().st_mtime if JSON_PATH.exists() else None
    }

# --- Servir Arquivos Estáticos ---
# Deve vir depois das rotas da API para não sobrescrevê-las
@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    """Serve o index.html ou outros arquivos estáticos."""
    path = Path(full_path).as_posix()
    if path == "" or path == "/":
        path = "index.html"
    
    static_file = Path(__file__).parent / path
    if static_file.exists():
        return FileResponse(static_file)
    
    # Fallback para o index.html para rotas de SPA (Single Page Application)
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
        
    raise HTTPException(status_code=404, detail="Arquivo estático não encontrado.")
