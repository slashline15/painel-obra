
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriveScanner:
    def __init__(self, credentials_info, config=None):
        self.config = config or {
            "notes_file": "file_notes.json",
            "disciplines": {
                "architecture": {"name": "ARQUITETURA", "folder_id": "1ERp2VogX3C-Xh_pOfORRvXRN-_twFoZq"},
                "structure": {"name": "ESTRUTURA", "folder_id": "YOUR_STRUCTURE_FOLDER_ID"},
                "hydraulic": {"name": "HIDRÁULICA", "folder_id": "YOUR_HYDRAULIC_FOLDER_ID"},
                "metallic": {"name": "METÁLICA", "folder_id": "YOUR_METALLIC_FOLDER_ID"}
            }
        }
        self.notes = self.load_notes()
        
        try:
            creds = service_account.Credentials.from_service_account_info(credentials_info, scopes=['https://www.googleapis.com/auth/drive.readonly'])
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Serviço do Google Drive conectado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao conectar com o Google Drive: {e}")
            self.service = None

    def load_notes(self):
        notes_path = Path(self.config["notes_file"])
        if notes_path.exists():
            try:
                with open(notes_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar notas: {e}")
        return {}

    def save_notes(self):
        try:
            with open(self.config["notes_file"], 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar notas: {e}")

    def format_size(self, size_bytes):
        if size_bytes is None:
            return "0.0B"
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def list_files_in_folder(self, folder_id):
        files = []
        folders = []
        if not self.service:
            return files, folders

        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)"
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folders.append(item['name'])
                else:
                    ext = item['name'].split('.')[-1].lower()
                    if ext in ['dwg', 'pdf']:
                        file_info = {
                            "id": item['id'],
                            "name": item['name'],
                            "type": ext,
                            "size": self.format_size(item.get('size')),
                            "size_bytes": int(item.get('size', 0)),
                            "modified": datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00')).strftime("%Y-%m-%d"),
                            "modified_timestamp": datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00')).timestamp(),
                            "path": "", 
                            "full_path": item['webViewLink'],
                            "hash": None 
                        }
                        files.append(file_info)

        except Exception as e:
            logger.error(f"Erro ao listar arquivos no Drive para a pasta {folder_id}: {e}")
            
        return files, folders

    def scan_all_disciplines(self):
        result = {
            "last_scan": datetime.now().isoformat(),
            "disciplines": {}
        }
        
        if not self.service:
            logger.error("Serviço do Drive não está disponível. Abortando o scan.")
            return result

        for disc_key, disc_info in self.config["disciplines"].items():
            logger.info(f"Escaneando {disc_info['name']} no Drive...")
            
            files, folders = self.list_files_in_folder(disc_info["folder_id"])
            total_size = sum(f['size_bytes'] for f in files)
            
            result["disciplines"][disc_key] = {
                "name": disc_info["name"],
                "path": disc_info["folder_id"],
                "files": files,
                "folders": folders,
                "total_files": len(files),
                "total_size": self.format_size(total_size),
                "total_size_bytes": total_size
            }
            logger.info(f"  → {len(files)} arquivos encontrados ({self.format_size(total_size)})")
            
        return result

    def run_once(self):
        logger.info("Iniciando scan do Google Drive...")
        data = self.scan_all_disciplines()
        self.save_notes()
        logger.info("Scan do Google Drive completo.")
        return data
