import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
AUTHORIZED_EMAILS_FILE = "authorized_emails.json"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Context para hash de senha (não usado com Google OAuth, mas útil para expansão futura)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthManager:
    def __init__(self):
        self.authorized_emails = self.load_authorized_emails()
        
    def load_authorized_emails(self) -> List[str]:
        """Carrega a lista de emails autorizados do arquivo JSON."""
        if os.path.exists(AUTHORIZED_EMAILS_FILE):
            try:
                with open(AUTHORIZED_EMAILS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get("authorized_emails", [])
            except Exception as e:
                print(f"Erro ao carregar emails autorizados: {e}")
                return []
        return []
    
    def save_authorized_emails(self, emails: List[str]):
        """Salva a lista de emails autorizados."""
        with open(AUTHORIZED_EMAILS_FILE, 'w') as f:
            json.dump({"authorized_emails": emails}, f, indent=2)
        self.authorized_emails = emails
    
    def is_email_authorized(self, email: str) -> bool:
        """Verifica se o email está na lista de autorizados."""
        return email.lower() in [e.lower() for e in self.authorized_emails]
    
    def add_authorized_email(self, email: str):
        """Adiciona um email à lista de autorizados."""
        if email.lower() not in [e.lower() for e in self.authorized_emails]:
            self.authorized_emails.append(email)
            self.save_authorized_emails(self.authorized_emails)
    
    def remove_authorized_email(self, email: str):
        """Remove um email da lista de autorizados."""
        self.authorized_emails = [e for e in self.authorized_emails if e.lower() != email.lower()]
        self.save_authorized_emails(self.authorized_emails)
    
    def verify_google_token(self, token: str) -> dict:
        """Verifica o token do Google e retorna as informações do usuário."""
        try:
            # Verifica o token com o Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Verifica se o email está autorizado
            email = idinfo.get('email')
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email não encontrado no token"
                )
            
            if not self.is_email_authorized(email):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Email {email} não está autorizado a acessar o sistema"
                )
            
            return {
                "email": email,
                "name": idinfo.get('name', ''),
                "picture": idinfo.get('picture', ''),
                "sub": idinfo.get('sub')
            }
            
        except ValueError as e:
            # Token inválido
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token Google inválido: {str(e)}"
            )
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Cria um JWT token para o usuário autenticado."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verifica e decodifica um JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("email")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Verifica novamente se o email ainda está autorizado
            if not self.is_email_authorized(email):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email não está mais autorizado"
                )
                
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )

# Instância global do gerenciador de autenticação
auth_manager = AuthManager()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependência para obter o usuário atual a partir do token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_manager.verify_token(token)

async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Dependência para obter o usuário atual (opcional)."""
    if not token:
        return None
    
    try:
        return auth_manager.verify_token(token)
    except HTTPException:
        return None