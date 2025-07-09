# Instruções de Deploy e Correções

## Correções Implementadas

1. **Servir arquivos estáticos sem autenticação**
   - Modificamos o `main.py` para permitir acesso a arquivos estáticos sem autenticação
   - A proteção agora é feita pelo JavaScript que redireciona para login se não autenticado

2. **Correção do URL da API**
   - Atualizamos o `file_loader.js` para usar o domínio correto (engdaniel.org)
   - Antes estava tentando acessar api.engdaniel.org, que não existia

3. **IDs das pastas do Google Drive**
   - Atualizamos os IDs das pastas no arquivo `drive_scanner.py`
   - Disciplinas agora apontam para as pastas corretas

4. **Arquivo .env**
   - Criamos um arquivo `.env` com as configurações necessárias para produção

## Configuração das Variáveis de Ambiente no Render

Configure estas variáveis no painel do Render:

```bash
# 1. GOOGLE_CREDS_JSON - JSON das credenciais de serviço em uma linha
GOOGLE_CREDS_JSON='{"type":"service_account","project_id":"seu-projeto",...}'

# 2. SECRET_KEY - Gere uma chave segura
SECRET_KEY=gere-com-python-c-import-secrets-print-secrets-token-urlsafe-32

# 3. FRONTEND_URL - Seu domínio
FRONTEND_URL=https://engdaniel.org

# 4. RENDER - Indica que está em produção
RENDER=true

# 5. SCAN_INTERVAL - Intervalo de scan em segundos
SCAN_INTERVAL=900
```

## Deploy para o Render

Execute estes comandos para fazer o deploy das alterações:

```bash
git add -A
git commit -m "Fix: autenticação e sincronização"
git push render main
```

## Verificação

Após o deploy, verifique:

1. Se o login está funcionando corretamente
2. Se a sincronização com o Google Drive está ocorrendo
3. Se os arquivos estão sendo exibidos nas respectivas disciplinas

Em caso de problemas, verifique os logs no painel do Render.