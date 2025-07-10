# Configuração do Sistema de Autenticação - HDAM Control

Este documento explica como configurar o sistema de autenticação com Google OAuth 2.0.

## 1. Configurar Google OAuth 2.0

### Passo 1: Criar um projeto no Google Cloud Console
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google+ (ou Google Identity)

### Passo 2: Criar credenciais OAuth 2.0
1. No Console, vá para "APIs e Serviços" > "Credenciais"
2. Clique em "Criar credenciais" > "ID do cliente OAuth"
3. Escolha "Aplicativo da Web"
4. Configure:
   - Nome: HDAM Control
   - Origens JavaScript autorizadas:
     - `http://localhost:8000` (desenvolvimento)
     - `https://seu-dominio.com` (produção)
   - URIs de redirecionamento autorizados:
     - `http://localhost:8000/login`
     - `https://seu-dominio.com/login`
5. Copie o "ID do cliente" gerado

### Passo 3: Configurar variáveis de ambiente
1. Copie `.env.example` para `.env`
2. Preencha as variáveis:
   ```
   GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
   SECRET_KEY=gere-uma-chave-aleatoria-segura
   ```

## 2. Gerenciar Usuários Autorizados

### Adicionar usuários autorizados
Edite o arquivo `authorized_emails.json`:
```json
{
  "authorized_emails": [
    "daniel.hoss67@gmail.com",
    "daniel.alves@hoss.com.br",
    "slashline15@gmail.com"
  ]
}
```

### Via API (após autenticação)
```bash
# Adicionar email
curl -X POST https://seu-dominio.com/api/admin/authorized-emails \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "novo@email.com"}'

# Remover email
curl -X DELETE https://seu-dominio.com/api/admin/authorized-emails/email@remover.com \
  -H "Authorization: Bearer SEU_TOKEN"
```

## 3. Atualizar o Client ID no Frontend

### Para desenvolvimento local:
1. Edite `login.html`
2. Substitua `YOUR_GOOGLE_CLIENT_ID` pelo seu Client ID real em:
   - `<meta name="google-signin-client_id" content="YOUR_GOOGLE_CLIENT_ID">`
   - `data-client_id="YOUR_GOOGLE_CLIENT_ID"`
   - `const GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID';`

### Para produção:
Considere usar variáveis de ambiente ou um sistema de build para injetar o Client ID.

## 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

As novas dependências incluem:
- `python-jose[cryptography]` - Para JWT tokens
- `passlib[bcrypt]` - Para hash de senhas (expansão futura)

## 5. Fluxo de Autenticação

1. Usuário acessa o sistema
2. Se não autenticado, é redirecionado para `/login`
3. Usuário faz login com Google
4. Sistema verifica se o email está na lista de autorizados
5. Se autorizado, gera um JWT token
6. Token é armazenado no localStorage do navegador
7. Todas as requisições subsequentes incluem o token

## 6. Segurança

### Recomendações:
1. **SECRET_KEY**: Use uma chave forte e única
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **HTTPS**: Sempre use HTTPS em produção

3. **CORS**: Configure corretamente o `FRONTEND_URL` no `.env`

4. **Tokens**: Os tokens expiram em 7 dias por padrão

### Proteção de Rotas:
- Todas as rotas da API estão protegidas
- Arquivos estáticos só são servidos para usuários autenticados
- Exceção: página de login é pública

## 7. Troubleshooting

### Erro "Email não autorizado"
- Verifique se o email está em `authorized_emails.json`
- O email é case-insensitive

### Erro "Token inválido"
- Token pode ter expirado
- Faça logout e login novamente

### Página em branco
- Verifique o console do navegador
- Confirme que o GOOGLE_CLIENT_ID está correto

## 8. Logs e Monitoramento

O sistema registra:
- Tentativas de login
- Tokens inválidos
- Acessos não autorizados

Monitore os logs do servidor para atividades suspeitas.