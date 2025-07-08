#!/usr/bin/env python3
"""
Corrige problemas comuns automaticamente
"""

import re
from pathlib import Path
import shutil

def fix_main_py():
    """Corrige main.py"""
    print("Corrigindo main.py...")
    
    if not Path('main.py').exists():
        print("❌ main.py não encontrado!")
        return False
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    shutil.copy('main.py', 'main.py.bak')
    
    # Remover rota / se existir
    content = re.sub(r'@app\.get\("/"\)\s*\n.*?\n.*?return.*?\n', '', content, flags=re.DOTALL)
    
    # Corrigir mount
    content = re.sub(
        r'app\.mount\("/static".*?\)', 
        'app.mount("/", StaticFiles(directory=".", html=True), name="static")',
        content
    )
    
    # Adicionar detecção Railway se não existir
    if 'IS_PRODUCTION' not in content:
        import_section = content.find('from dotenv import load_dotenv')
        if import_section > -1:
            insert_pos = content.find('\n', import_section) + 1
            railway_code = '''import os

# Detectar se está no railway
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") is not None

# Se produção, desabilita reload
if IS_PRODUCTION:
    # Railway vai setar a PORT automaticamente
    port = int(os.environ.get("PORT", 8000))

'''
            content = content[:insert_pos] + railway_code + content[insert_pos:]
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py corrigido!")
    return True

def fix_index_html():
    """Corrige index.html"""
    print("\nCorrigindo index.html...")
    
    if not Path('index.html').exists():
        print("❌ index.html não encontrado!")
        return False
    
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    shutil.copy('index.html', 'index.html.bak')
    
    # Corrigir useLocalMode
    content = re.sub(r'useLocalMode:\s*true', 'useLocalMode: false', content)
    
    # Zerar valores dos cards
    patterns = [
        (r'id="arch-files">\d+</div>', 'id="arch-files">0</div>'),
        (r'id="arch-folders">\d+</div>', 'id="arch-folders">0</div>'),
        (r'id="arch-size">[^<]+</div>', 'id="arch-size">0MB</div>'),
        (r'id="struct-files">\d+</div>', 'id="struct-files">0</div>'),
        (r'id="struct-folders">\d+</div>', 'id="struct-folders">0</div>'),
        (r'id="struct-size">[^<]+</div>', 'id="struct-size">0MB</div>'),
        (r'id="hydro-files">\d+</div>', 'id="hydro-files">0</div>'),
        (r'id="hydro-folders">\d+</div>', 'id="hydro-folders">0</div>'),
        (r'id="hydro-size">[^<]+</div>', 'id="hydro-size">0MB</div>'),
        (r'id="metal-files">\d+</div>', 'id="metal-files">0</div>'),
        (r'id="metal-folders">\d+</div>', 'id="metal-folders">0</div>'),
        (r'id="metal-size">[^<]+</div>', 'id="metal-size">0MB</div>'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ index.html corrigido!")
    return True

def fix_file_loader():
    """Corrige file_loader.js"""
    print("\nCorrigindo file_loader.js...")
    
    if not Path('file_loader.js').exists():
        print("❌ file_loader.js não encontrado!")
        return False
    
    with open('file_loader.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    shutil.copy('file_loader.js', 'file_loader.js.bak')
    
    # Corrigir URL da API
    content = re.sub(
        r"apiUrl:\s*window\.location\.hostname[^,]+,",
        '''apiUrl: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : 'https://api.dimensaoc137.org',''',
        content
    )
    
    with open('file_loader.js', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ file_loader.js corrigido!")
    return True

def create_procfile():
    """Cria Procfile se não existir"""
    if not Path('Procfile').exists():
        print("\nCriando Procfile...")
        with open('Procfile', 'w') as f:
            f.write('web: uvicorn main:app --host 0.0.0.0 --port $PORT\n')
        print("✅ Procfile criado!")
    else:
        print("\n✅ Procfile já existe")

def remove_duplicates():
    """Remove arquivos duplicados"""
    print("\nProcurando arquivos duplicados...")
    
    # Procurar file_loader duplicados
    loaders = list(Path('.').glob('**/file_loader*.js'))
    if len(loaders) > 1:
        print(f"Encontrados {len(loaders)} file_loader:")
        for i, f in enumerate(loaders):
            print(f"  {i+1}. {f}")
        
        # Manter apenas o da raiz
        root_loader = Path('file_loader.js')
        for f in loaders:
            if f != root_loader:
                print(f"  Removendo {f}...")
                f.unlink()
        print("✅ Duplicatas removidas!")
    
    # Remover file-scanner.js se existir
    if Path('file-scanner.js').exists():
        Path('file-scanner.js').unlink()
        print("✅ file-scanner.js (Node) removido")

def main():
    print("=== CORREÇÃO AUTOMÁTICA HDAM ===\n")
    
    # Executar correções
    fix_main_py()
    fix_index_html()
    fix_file_loader()
    create_procfile()
    remove_duplicates()
    
    print("\n=== CORREÇÕES APLICADAS ===")
    print("\nArquivos .bak criados para backup")
    print("\nPróximos passos:")
    print("1. python diagnose.py  # verificar se tudo OK")
    print("2. uvicorn main:app --reload")
    print("3. Teste em http://localhost:8000")
    print("4. Se OK → railway up")

if __name__ == "__main__":
    main()