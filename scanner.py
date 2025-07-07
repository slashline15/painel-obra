#!/usr/bin/env python3
"""
HDAM File Scanner - Sincronização de arquivos locais
Escaneia a pasta do projeto e gera um JSON para o painel web
"""

import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
import argparse
import logging

# Configuração
CONFIG = {
    "base_path": r"I:\\Meu Drive\\DRIVE PREDIO ADM",
    "output_file": "file_data.json",
    "notes_file": "file_notes.json",
    "scan_interval": 60,  # segundos
    "disciplines": {
        "architecture": {"name": "ARQUITETURA", "path": "ARQUITETURA"},
        "structure": {"name": "ESTRUTURA", "path": "ESTRUTURA"},
        "hydraulic": {"name": "HIDRÁULICA", "path": "HIDRAULICA"},
        "metallic": {"name": "METÁLICA", "path": "METALICA"}
    }
}

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileScanner:
    def __init__(self, base_path: Path, config):
        self.base_path = Path(base_path)
        self.config = config
        self.base_path = Path(config["base_path"])
        self.notes = self.load_notes()
        
    def load_notes(self):
        """Carrega notas salvas anteriormente"""
        notes_path = Path(self.config["notes_file"])
        if notes_path.exists():
            try:
                with open(notes_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar notas: {e}")
        return {}
    
    def save_notes(self):
        """Salva notas no arquivo"""
        try:
            with open(self.config["notes_file"], 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar notas: {e}")
    
    def get_file_hash(self, filepath):
        """Gera hash MD5 do arquivo para detectar mudanças"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read(1024 * 1024)).hexdigest()  # Lê apenas 1MB
        except:
            return None
    
    def format_size(self, size_bytes):
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def scan_directory(self, directory_path, relative_to=None):
        """Escaneia um diretório e retorna estrutura de arquivos"""
        files = []
        folders = []
        total_size = 0
        
        try:
            dir_path = Path(directory_path)
            if not dir_path.exists():
                logger.warning(f"Diretório não encontrado: {directory_path}")
                return files, folders, total_size
            
            for item in dir_path.iterdir():
                try:
                    if item.is_dir():
                        folders.append(item.name)
                    elif item.is_file():
                        # Filtrar apenas arquivos DWG e PDF
                        ext = item.suffix.lower()
                        if ext in ['.dwg', '.pdf']:
                            stat = item.stat()
                            relative_path = item.relative_to(relative_to) if relative_to else item
                            
                            # Determinar pasta relativa
                            path_parts = list(relative_path.parts[:-1])
                            folder_path = path_parts[1] if len(path_parts) > 1 else ""
                            
                            file_info = {
                                "name": item.name,
                                "type": ext[1:],  # Remove o ponto
                                "size": self.format_size(stat.st_size),
                                "size_bytes": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                                "modified_timestamp": stat.st_mtime,
                                "path": folder_path,
                                "full_path": str(relative_path),
                                "hash": self.get_file_hash(item)
                            }
                            
                            # Adicionar nota se existir
                            note_key = f"{relative_path.parts[0]}_{item.name}"
                            if note_key in self.notes:
                                file_info["notes"] = self.notes[note_key]
                            
                            files.append(file_info)
                            total_size += stat.st_size
                            
                except Exception as e:
                    logger.error(f"Erro ao processar {item}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao escanear diretório {directory_path}: {e}")
            
        return files, folders, total_size
    
    def scan_all_disciplines(self):
        """Escaneia todas as disciplinas"""
        result = {
            "last_scan": datetime.now().isoformat(),
            "disciplines": {}
        }
        
        for disc_key, disc_info in self.config["disciplines"].items():
            logger.info(f"Escaneando {disc_info['name']}...")
            
            disc_path = self.base_path / disc_info["path"]
            files = []
            folders = []
            total_size = 0
            
            if disc_path.exists():
                # Escanear arquivos na raiz da disciplina
                root_files, _, root_size = self.scan_directory(disc_path, self.base_path)
                files.extend(root_files)
                total_size += root_size
                
                # Escanear subpastas
                for subdir in disc_path.iterdir():
                    if subdir.is_dir():
                        folders.append(subdir.name)
                        sub_files, _, sub_size = self.scan_directory(subdir, self.base_path)
                        files.extend(sub_files)
                        total_size += sub_size
            
            result["disciplines"][disc_key] = {
                "name": disc_info["name"],
                "path": disc_info["path"],
                "files": files,
                "folders": folders,
                "total_files": len(files),
                "total_size": self.format_size(total_size),
                "total_size_bytes": total_size
            }
            
            logger.info(f"  → {len(files)} arquivos encontrados ({self.format_size(total_size)})")
        
        return result
    
    def save_results(self, data):
        """Salva resultados em arquivo JSON"""
        output_path = Path(self.config["output_file"])
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Dados salvos em: {output_path.absolute()}")
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
    
    def detect_changes(self, old_data, new_data):
        """Detecta mudanças entre scans"""
        changes = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": []
        }
        
        if not old_data:
            return changes
        
        for disc_key in new_data["disciplines"]:
            old_files = {}
            new_files = {}
            
            if disc_key in old_data.get("disciplines", {}):
                for f in old_data["disciplines"][disc_key].get("files", []):
                    old_files[f["name"]] = f
            
            for f in new_data["disciplines"][disc_key].get("files", []):
                new_files[f["name"]] = f
            
            # Novos arquivos
            for name, file_info in new_files.items():
                if name not in old_files:
                    changes["new_files"].append(f"{disc_key}/{name}")
                elif file_info.get("hash") != old_files[name].get("hash"):
                    changes["modified_files"].append(f"{disc_key}/{name}")
            
            # Arquivos deletados
            for name in old_files:
                if name not in new_files:
                    changes["deleted_files"].append(f"{disc_key}/{name}")
        
        return changes
    
    def run_once(self):
        """Executa um scan único"""
        logger.info("Iniciando scan...")
        start_time = time.time()
        
        # Carregar dados anteriores
        old_data = None
        if Path(self.config["output_file"]).exists():
            try:
                with open(self.config["output_file"], 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
            except:
                pass
        
        # Executar scan
        data = self.scan_all_disciplines()
        
        # Detectar mudanças
        if old_data:
            changes = self.detect_changes(old_data, data)
            if any(changes.values()):
                logger.info("Mudanças detectadas:")
                if changes["new_files"]:
                    logger.info(f"  → Novos: {', '.join(changes['new_files'][:5])}")
                if changes["modified_files"]:
                    logger.info(f"  → Modificados: {', '.join(changes['modified_files'][:5])}")
                if changes["deleted_files"]:
                    logger.info(f"  → Deletados: {', '.join(changes['deleted_files'][:5])}")
        
        # Salvar resultados
        self.save_results(data)
        self.save_notes()
        
        elapsed = time.time() - start_time
        logger.info(f"Scan completo em {elapsed:.2f}s")
        
        return data
    
    def run_continuous(self):
        """Executa scan contínuo"""
        logger.info(f"Modo contínuo - scan a cada {self.config['scan_interval']}s")
        logger.info("Pressione Ctrl+C para parar")
        
        try:
            while True:
                self.run_once()
                time.sleep(self.config["scan_interval"])
        except KeyboardInterrupt:
            logger.info("\nParando scanner...")

def main():
    parser = argparse.ArgumentParser(description="HDAM File Scanner")
    parser.add_argument('--once', action='store_true', help='Executar apenas uma vez')
    parser.add_argument('--path', help='Caminho base alternativo')
    parser.add_argument('--output', help='Arquivo de saída alternativo')
    parser.add_argument('--interval', type=int, help='Intervalo de scan em segundos')
    args = parser.parse_args()
    
    # Aplicar argumentos
    if args.path:
        CONFIG["base_path"] = args.path
    if args.output:
        CONFIG["output_file"] = args.output
    if args.interval:
        CONFIG["scan_interval"] = args.interval
    
    # Criar scanner
    scanner = FileScanner(CONFIG)
    
    # Executar
    if args.once:
        scanner.run_once()
    else:
        scanner.run_continuous()

if __name__ == "__main__":
    main()