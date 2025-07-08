# Cloudflare Setup - Em 5 minutos

## 1. Deploy no Railway primeiro

```bash
# No terminal do projeto
pip install railway
railway login
railway init
railway link  # escolha criar novo projeto

# Adicionar variáveis de ambiente no Railway Dashboard:
# BASE_PATH = I:\Meu Drive\DRIVE PREDIO ADM
# SCAN_INTERVAL = 300

railway up
```

Railway vai te dar uma URL tipo: `hdam-api-production.up.railway.app`

## 2. Configurar Cloudflare

### A) Criar subdomínio para API
1. Login no Cloudflare → Seu domínio → DNS
2. Clique em "Add Record"
3. Preencha:
   - Type: `CNAME`
   - Name: `api` (vai virar api.seudominio.com)
   - Target: `hdam-api-production.up.railway.app` (URL do Railway)
   - Proxy status: **ON** (nuvem laranja)
4. Save

### B) Criar subdomínio para o frontend (opcional)
1. Add Record novamente
2. Preencha:
   - Type: `CNAME`
   - Name: `hdam` (vai virar hdam.seudominio.com)
   - Target: mesma URL do Railway
   - Proxy status: **ON**
3. Save

### C) SSL/TLS Settings
1. Vá em SSL/TLS → Overview
2. Escolha "Full" (não strict)
3. Em Edge Certificates, ative "Always Use HTTPS"

## 3. Ajustar código para produção

### No `main.py`, adicione no início:
```python
import os
# Detectar se está no Railway
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") is not None

# Se produção, desabilita reload
if IS_PRODUCTION:
    # Railway vai setar a PORT automaticamente
    port = int(os.environ.get("PORT", 8000))
```

### No `file_loader.js`, mude a configuração:
```javascript
const FILE_LOADER_CONFIG = {
    apiUrl: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : 'https://api.seudominio.com',  // ← MUDE AQUI
    refreshInterval: 30000,
    autoRefresh: true
};
```

## 4. Arquivo Procfile (criar na raiz)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 5. Testar

1. Acesse `https://api.dimensaoc137.org/api/status` - deve retornar JSON
2. Acesse `https://api.dimensaoc137.org/index.html` - deve abrir o painel
3. Ou se criou subdomínio frontend: `https://hdam.dimensaoc137.org`

## Problemas comuns:

**"502 Bad Gateway"**
- Railway ainda está buildando, espere 2 min
- Verifique logs no Railway Dashboard

**"SSL Error"**
- Espere 5 min para Cloudflare provisionar certificado
- Certifique que Proxy está ON (nuvem laranja)

**"CORS Error"**
- O `main.py` já tem CORS configurado
- Se persistir, adicione seu domínio específico em `allow_origins`

**Arquivos não abrem**
- Normal - em produção não tem acesso ao file:///
- Solução: fazer upload para Google Drive e usar links compartilhados