#!/usr/bin/env python3
"""
Script de teste rápido - rode isso antes de fazer deploy
"""

import os
import json
from pathlib import Path
from scanner import FileScanner

def test_scanner():
    """Testa se o scanner funciona"""
    print("1. Testando Scanner...")
    
    # Use o path do .env ou fallback
    base_path = os.getenv("BASE_PATH", r"I:\Meu Drive\DRIVE PREDIO ADM")
    
    if not Path(base_path).exists():
        print(f"❌ ERRO: Caminho não existe: {base_path}")
        print("   Ajuste BASE_PATH no .env")
        return False
    
    scanner = FileScanner(base_path)
    data = scanner.run_once()
    
    # Verificar se encontrou arquivos
    total_files = sum(d["total_files"] for d in data["disciplines"].values())
    print(f"✅ Scanner OK - {total_files} arquivos encontrados")
    
    # Salvar JSON de teste
    with open("file_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True

def test_api():
    """Testa se a API responde"""
    print("\n2. Testando API...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/status")
        if response.status_code == 200:
            print("✅ API respondendo OK")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ API retornou erro: {response.status_code}")
    except:
        print("❌ API não está rodando ou 'requests' não instalado")
        print("   Execute: uvicorn main:app --reload")

def test_frontend():
    """Verifica arquivos do frontend"""
    print("\n3. Verificando Frontend...")
    
    files = ["index.html", "file_loader.js"]
    for f in files:
        if Path(f).exists():
            print(f"✅ {f} existe")
        else:
            print(f"❌ {f} não encontrado")
    
    # Verificar se removeu mock do index.html
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
        if "8.7MB" in content and "modified: '2025-03-14'" in content:
            print("⚠️  AVISO: index.html ainda tem dados mockados!")
            print("   Remova o objeto fileSystem hardcoded")
        else:
            print("✅ index.html sem dados mockados")

if __name__ == "__main__":
    print("=== TESTE HDAM CONTROL ===\n")
    
    # Carregar .env se existir
    from dotenv import load_dotenv
    load_dotenv()
    
    # Executar testes
    if test_scanner():
        test_api()
        test_frontend()
    
    print("\n=== FIM DOS TESTES ===")
    print("\nPróximos passos:")
    print("1. Se tudo OK → railway up")
    print("2. Se API erro → uvicorn main:app --reload")
    print("3. Se Scanner erro → verificar BASE_PATH")