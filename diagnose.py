#!/usr/bin/env python3
"""
Diagnóstico completo do projeto HDAM
"""

import os
import re
from pathlib import Path

def check_file(filepath, patterns, name):
    """Verifica padrões em um arquivo"""
    print(f"\n{'='*50}")
    print(f"Verificando {name} ({filepath}):")
    print('='*50)
    
    if not Path(filepath).exists():
        print(f"❌ ERRO: Arquivo {filepath} não existe!")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_ok = True
    for pattern, expected, message in patterns:
        if pattern.startswith('REGEX:'):
            match = re.search(pattern[6:], content)
            found = bool(match)
        else:
            found = pattern in content
        
        if found == expected:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            all_ok = False
    
    return all_ok

def diagnose():
    """Executa diagnóstico completo"""
    print("DIAGNÓSTICO HDAM CONTROL")
    
    # 1. Verificar main.py
    main_patterns = [
        ('app.mount("/", StaticFiles(directory=".", html=True)', True, 
         'Static files montados na raiz'),
        ('@app.get("/")', False, 
         'Rota / removida (não deve existir)'),
        ('CORSMiddleware', True, 
         'CORS configurado'),
        ('app.mount("/static"', False, 
         'Mount /static removido (não deve existir)'),
        ('IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT")', True,
         'Detecção de produção Railway')
    ]
    
    main_ok = check_file('main.py', main_patterns, 'Backend FastAPI')
    
    # 2. Verificar index.html
    html_patterns = [
        ('useLocalMode: true', False, 
         'useLocalMode deve ser FALSE'),
        ('useLocalMode: false', True, 
         'useLocalMode configurado como FALSE'),
        ('REGEX:id="arch-files">\\d+</div>', True,
         'Valores dos cards encontrados'),
        ('REGEX:id="arch-files">0</div>', True,
         'Valores dos cards zerados'),
        ('<script src="file_loader.js"></script>', True,
         'file_loader.js incluído'),
        ('8.7MB', False,
         'Dados mock removidos (não deve ter 8.7MB)'),
        ("modified: '2025-03-14'", False,
         'Dados mock removidos (não deve ter data hardcoded)')
    ]
    
    html_ok = check_file('index.html', html_patterns, 'Frontend HTML')
    
    # 3. Verificar file_loader.js
    loader_patterns = [
        ('https://api.dimensaoc137.org', True,
         'URL da API configurada para produção'),
        ('...fileSystem[key]', True,
         'Spread operator correto'),
        ('/api/files', True,
         'Endpoint /api/files configurado'),
        ('updateDisciplineStats', True,
         'Função de atualização de stats existe')
    ]
    
    loader_ok = check_file('file_loader.js', loader_patterns, 'File Loader JS')
    
    # 4. Verificar arquivos críticos
    print(f"\n{'='*50}")
    print("Verificando arquivos críticos:")
    print('='*50)
    
    critical_files = {
        'scanner.py': 'Scanner Python',
        'requirements.txt': 'Dependências',
        '.env': 'Variáveis de ambiente',
        'Procfile': 'Config Railway',
        'file_data.json': 'Cache de dados'
    }
    
    for file, desc in critical_files.items():
        if Path(file).exists():
            print(f"✅ {desc} ({file}) existe")
        else:
            print(f"⚠️  {desc} ({file}) não encontrado")
    
    # 5. Verificar duplicatas
    print(f"\n{'='*50}")
    print("Verificando arquivos duplicados:")
    print('='*50)
    
    js_files = list(Path('.').glob('**/file_loader*.js'))
    if len(js_files) > 1:
        print(f"❌ ERRO: Múltiplos file_loader.js encontrados:")
        for f in js_files:
            print(f"   - {f}")
        print("   SOLUÇÃO: Delete as versões antigas!")
    else:
        print("✅ Apenas um file_loader.js encontrado")
    
    # 6. Verificar .env
    if Path('.env').exists():
        print(f"\n{'='*50}")
        print("Verificando .env:")
        print('='*50)
        
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'BASE_PATH' in env_content:
            print("✅ BASE_PATH configurado")
        else:
            print("❌ BASE_PATH não encontrado no .env")
        
        if 'SCAN_INTERVAL' in env_content:
            print("✅ SCAN_INTERVAL configurado")
        else:
            print("⚠️  SCAN_INTERVAL não configurado (usando padrão 300)")
    
    # Resumo final
    print(f"\n{'='*50}")
    print("RESUMO:")
    print('='*50)
    
    if main_ok and html_ok and loader_ok:
        print("✅ Configuração principal OK!")
        print("\nPróximos passos:")
        print("1. uvicorn main:app --reload")
        print("2. Teste em http://localhost:8000")
        print("3. Se OK → railway up")
    else:
        print("❌ Correções necessárias acima!")
        print("\nExecute as correções e rode o diagnóstico novamente.")

if __name__ == "__main__":
    diagnose()