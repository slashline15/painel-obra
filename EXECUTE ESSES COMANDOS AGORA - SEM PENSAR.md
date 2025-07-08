# EXECUTE ESSES COMANDOS AGORA - SEM PENSAR

## 1. Preparar ambiente (2 min)
```bash
# Se não tem venv ainda
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Instalar tudo
pip install -r requirements.txt
pip install requests  # pro teste
```

## 2. Criar .env (30 seg)
```bash
echo BASE_PATH="I:\Meu Drive\DRIVE PREDIO ADM" > .env
echo SCAN_INTERVAL=300 >> .env
```

## 3. Testar local (1 min)
```bash
python test_local.py
```

Se der erro no path, ajuste o BASE_PATH no .env

## 4. Rodar servidor local (30 seg)
```bash
# Terminal 1
uvicorn main:app --reload

# Terminal 2 (nova janela)
start http://localhost:8000/index.html
```

## 5. Deploy Railway (3 min)
```bash
# Se primeira vez
pip install railway
railway login

# Deploy
railway init  # escolha 'criar novo projeto'
railway up

# Adicionar variáveis no browser
# Railway vai abrir o dashboard, adicione:
# BASE_PATH = seu_caminho
# SCAN_INTERVAL = 300
```

## 6. Cloudflare (2 min)
1. Copie a URL do Railway (algo como xxx.up.railway.app)
2. Vá no Cloudflare → DNS → Add Record
3. CNAME | api | cole-url-railway | Proxy ON
4. Save e pronto

## 7. Última coisa
No `file_loader.js`, linha 9, mude para:
```javascript
apiUrl: window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://api.SEU-DOMINIO.com',  // ← aqui
```

## PRONTO! 🚀

Total: ~10 minutos se não pensar muito

### Se der merda:
- Path errado → ajusta .env
- Railway erro → olha logs no dashboard
- Cloudflare 502 → espera 2 min
- CORS → já tá configurado, relaxa

### Funcionou?
Abre https://api.seu-dominio.com/index.html