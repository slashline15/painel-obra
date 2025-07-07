# HDAM Control Panel - Instruções de Uso

## 🚀 Instalação Rápida

### 1. Estrutura de Arquivos
```
hdam-control/
├── index.html          # Interface web principal
├── file_scanner.py     # Scanner Python
├── file_loader.js      # Script de integração
├── file_data.json      # Dados dos arquivos (gerado automaticamente)
└── file_notes.json     # Notas dos arquivos (gerado automaticamente)
```

### 2. Configuração Inicial

#### Python Scanner
1. Certifique-se de ter Python 3.6+ instalado
2. Edite o `file_scanner.py` e ajuste o caminho base:
   ```python
   CONFIG = {
       "base_path": r"I:\Meu Drive\DRIVE PREDIO ADM",  # Seu caminho aqui
       ...
   }
   ```

#### Interface Web
1. Adicione o script de integração no final do `index.html`, antes do `</body>`:
   ```html
   <script src="file_loader.js"></script>
   </body>
   </html>
   ```

## 📖 Como Usar

### Modo 1: Execução Local Simples

1. **Iniciar o Scanner Python**
   ```bash
   # Modo contínuo (escaneia a cada 60 segundos)
   python file_scanner.py
   
   # Ou apenas uma vez
   python file_scanner.py --once
   ```

2. **Abrir a Interface**
   - Opção A: Abra o `index.html` direto no navegador
   - Opção B: Use um servidor local:
     ```bash
     # Python
     python -m http.server 8000
     
     # Ou Node.js
     npx http-server
     ```

3. **Sincronizar Arquivos**
   - Clique no botão "SYNC FILES" ou pressione `Ctrl+R`
   - Os arquivos serão atualizados automaticamente a cada 30 segundos

### Modo 2: Scanner em Background

1. **Windows - Criar arquivo .bat**
   ```batch
   @echo off
   cd /d "C:\caminho\para\hdam-control"
   python file_scanner.py
   ```

2. **Linux/Mac - Criar script .sh**
   ```bash
   #!/bin/bash
   cd /path/to/hdam-control
   python3 file_scanner.py
   ```

## 🎯 Funcionalidades

### Navegação
- **Home**: Mostra os 4 cards das disciplinas
- **Click no Card**: Abre a lista de arquivos da disciplina
- **Click no Arquivo**: Abre o arquivo (PDF/DWG) no programa padrão
- **Breadcrumb**: Navegação rápida entre níveis

### Atalhos de Teclado
- `Ctrl+F`: Buscar arquivos
- `Ctrl+R`: Sincronizar arquivos
- `ESC`: Voltar para home

### Notas
- Clique no campo de notas para adicionar observações
- As notas são salvas automaticamente
- Sincronizadas entre sessões

## 🔧 Personalização

### Alterar Intervalo de Scan
```bash
# Scanner a cada 5 minutos (300 segundos)
python file_scanner.py --interval 300
```

### Adicionar Novas Disciplinas
No `file_scanner.py`:
```python
CONFIG = {
    "disciplines": {
        "architecture": {...},
        "electrical": {"name": "ELÉTRICA", "path": "ELETRICA"},  # Nova
    }
}
```

No `index.html`, adicione um novo card na grid.

## 🐛 Solução de Problemas

### Arquivos não abrem
- Verifique se o caminho no CONFIG está correto
- Para arquivos DWG, certifique-se que o AutoCAD está instalado
- Tente usar um navegador diferente (Chrome/Edge recomendados)

### Scanner não encontra arquivos
- Verifique se o caminho existe e tem permissão de leitura
- Execute o scanner com `--once` para ver mensagens de erro

### Sincronização não funciona
- Verifique se o `file_data.json` está sendo criado
- Abra o console do navegador (F12) para ver erros
- Certifique-se que o `file_loader.js` está incluído

## 📋 Próximas Melhorias

- [ ] Integração com Google Drive API
- [ ] Thumbnails de PDFs
- [ ] Sistema de comentários com timestamp
- [ ] Notificações de mudanças
- [ ] Visualização 3D do modelo Revit
- [ ] Dashboard com métricas do projeto

## 💡 Dicas

1. **Performance**: Para pastas muito grandes, aumente o intervalo de scan
2. **Backup**: O scanner não modifica arquivos, apenas lê
3. **Múltiplos Projetos**: Crie diferentes configs para cada projeto

---

**Desenvolvido para HOSS Engineering**  
*Controle eficiente de arquivos de projeto*