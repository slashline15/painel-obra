#!/usr/bin/env python3
"""
HDAM File Scanner - Módulo reutilizável
"""

import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileScanner:
    def __init__(self, base_path: Path, config=None):
        self.base_path = Path(base_path)
        self.config = config or {
            "output_file": "file_data.json",
            "notes_file": "file_notes.json",
            "disciplines": {
                "architecture": {"name": "ARQUITETURA", "path": "ARQUITETURA"},
                "structure": {"name": "ESTRUTURA", "path": "ESTRUTURA"},
                "hydraulic": {"name": "HIDRÁULICA", "path": "HIDRAULICA"},
                "metallic": {"name": "METÁLICA", "path": "METALICA"}
            }
        }
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
                return hashlib.md5(f.read(1024 * 1024)).hexdigest()
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
                                "full_path": str(relative_path).replace('\\', '/'),
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
    
    def run_once(self):
        """Executa um scan único e retorna os dados"""
        logger.info("Iniciando scan...")
        start_time = time.time()
        
        data = self.scan_all_disciplines()
        self.save_notes()
        
        elapsed = time.time() - start_time
        logger.info(f"Scan completo em {elapsed:.2f}s")
        
        return data