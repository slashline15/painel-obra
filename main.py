from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pathlib import Path
import json
import os
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from drive_scanner import DriveScanner
from auth import auth_manager, get_current_user, get_current_user_optional
from pydantic import BaseModel

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

# --- Modelos Pydantic ---
class GoogleAuthRequest(BaseModel):
    token: str

class AuthorizedEmailRequest(BaseModel):
    email: str

# --- Rotas de Autenticação ---
@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Autentica um usuário usando o token do Google."""
    try:
        # Verifica o token do Google e obtém as informações do usuário
        user_info = auth_manager.verify_google_token(request.token)
        
        # Cria um token JWT para o usuário
        access_token = auth_manager.create_access_token(
            data={
                "email": user_info["email"],
                "name": user_info["name"],
                "picture": user_info["picture"]
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_info
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verifica se o token do usuário é válido."""
    return {"valid": True, "user": current_user}

@app.post("/api/auth/logout")
async def logout():
    """Endpoint de logout (o cliente deve remover o token)."""
    return {"message": "Logout realizado com sucesso"}

# --- Rotas de Gerenciamento de Emails Autorizados (apenas para admins) ---
@app.get("/api/admin/authorized-emails")
async def get_authorized_emails(current_user: dict = Depends(get_current_user)):
    """Retorna a lista de emails autorizados (apenas para admins)."""
    # Por enquanto, todos os usuários autenticados podem ver a lista
    # Você pode adicionar uma verificação de admin aqui
    return {"emails": auth_manager.authorized_emails}

@app.post("/api/admin/authorized-emails")
async def add_authorized_email(
    request: AuthorizedEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """Adiciona um email à lista de autorizados."""
    auth_manager.add_authorized_email(request.email)
    return {"message": f"Email {request.email} adicionado com sucesso"}

@app.delete("/api/admin/authorized-emails/{email}")
async def remove_authorized_email(
    email: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove um email da lista de autorizados."""
    auth_manager.remove_authorized_email(email)
    return {"message": f"Email {email} removido com sucesso"}

# --- Rotas da API (Protegidas) ---
@app.get("/api/files")
async def get_files(current_user: dict = Depends(get_current_user)):
    """Retorna os dados dos arquivos cacheados do Drive."""
    if not JSON_PATH.exists():
        return {"error": "Cache de arquivos ainda não foi criado.", "disciplines": {}}
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler cache: {e}")

@app.post("/api/refresh")
async def refresh_files(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Dispara uma nova varredura do Google Drive em segundo plano."""
    background_tasks.add_task(do_drive_scan)
    return {"status": "success", "message": "Atualização iniciada em segundo plano."}

@app.get("/api/status")
async def get_status(current_user: dict = Depends(get_current_user)):
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
async def serve_static(
    full_path: str,
    current_user: dict = Depends(get_current_user_optional)
):
    """Serve o index.html ou outros arquivos estáticos."""
    path = Path(full_path).as_posix()
    
    # Permite acesso à página de login sem autenticação
    if path in ["login", "login.html", "login/"]:
        login_path = Path(__file__).parent / "login.html"
        if login_path.exists():
            return FileResponse(login_path)
    
    # Para todas as outras rotas, verifica autenticação
    if not current_user:
        # Redireciona para a página de login se não estiver autenticado
        if path == "" or path == "/" or path == "index.html":
            return RedirectResponse(url="/login", status_code=302)
        # Para outros arquivos estáticos, retorna 401
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Usuário autenticado - serve os arquivos normalmente
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
