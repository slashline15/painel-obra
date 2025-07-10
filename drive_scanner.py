import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriveScanner:
    def __init__(self, credentials_info, config=None):
        # ID da pasta raiz dos projetos (extraído da URL que você passou)
        self.root_folder_id = "19VT84IP7Snl4Kg3HUd5MJoNc1U4sv3Rc"
        
        self.config = config or {
            "notes_file": "file_notes.json",
            "disciplines": {
                "architecture": {"name": "ARQUITETURA", "keywords": ["Arquitetura", "arq", "arch"]},
                "structure": {"name": "ESTRUTURA", "keywords": ["Estrutura", "estrut", "concreto", "armação"]},
                "hydraulic": {"name": "HIDRÁULICA", "keywords": ["Hidráulica", "hidro", "hidr", "água", "esgoto"]},
                "metallic": {"name": "METÁLICA", "keywords": ["Metálica", "metal", "aço", "steel"]},
                "electrical": {"name": "ELÉTRICA", "keywords": ["eletrica", "eletr", "energia", "volt"]},
                "others": {"name": "OUTROS", "keywords": []}  # Categoria padrão
            }
        }
        self.notes = self.load_notes()
        
        try:
            creds = service_account.Credentials.from_service_account_info(
                credentials_info, 
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
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

    def classify_file(self, file_name: str, path_parts: List[str]) -> str:
        """Classifica o arquivo baseado no nome e caminho"""
        # Converte tudo pra lowercase pra comparar
        name_lower = file_name.lower()
        path_lower = " ".join(path_parts).lower()
        full_text = f"{name_lower} {path_lower}"
        
        # Verifica cada disciplina
        for disc_key, disc_info in self.config["disciplines"].items():
            if disc_key == "others":  # Pula a categoria padrão
                continue
            for keyword in disc_info["keywords"]:
                if keyword in full_text:
                    return disc_key
        
        return "others"  # Categoria padrão

    def list_files_recursive(self, folder_id: str, path_parts: List[str] = None) -> Dict[str, List]:
        """Lista arquivos recursivamente, organizando por disciplina"""
        if path_parts is None:
            path_parts = []
            
        files_by_discipline = {k: [] for k in self.config["disciplines"].keys()}
        folders_by_discipline = {k: set() for k in self.config["disciplines"].keys()}
        
        if not self.service:
            return files_by_discipline

        try:
            # Lista todos os itens na pasta atual
            query = f"'{folder_id}' in parents and trashed = false"
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        # É uma pasta - processar recursivamente
                        subfolder_name = item['name']
                        logger.info(f"Processando pasta: {'/'.join(path_parts + [subfolder_name])}")
                        
                        # Busca arquivos na subpasta
                        sub_results = self.list_files_recursive(
                            item['id'], 
                            path_parts + [subfolder_name]
                        )
                        
                        # Mescla os resultados
                        for disc_key in files_by_discipline:
                            files_by_discipline[disc_key].extend(sub_results[disc_key])
                            # Adiciona a pasta se tem arquivos dessa disciplina
                            if sub_results[disc_key]:
                                folders_by_discipline[disc_key].add(subfolder_name)
                    else:
                        # É um arquivo
                        ext = item['name'].split('.')[-1].lower()
                        # Filtra apenas arquivos relevantes
                        if ext in ['dwg', 'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'zip']:
                            # Classifica o arquivo
                            discipline = self.classify_file(item['name'], path_parts)
                            
                            file_info = {
                                "id": item['id'],
                                "name": item['name'],
                                "type": ext,
                                "size": self.format_size(item.get('size')),
                                "size_bytes": int(item.get('size', 0)),
                                "modified": datetime.fromisoformat(
                                    item['modifiedTime'].replace('Z', '+00:00')
                                ).strftime("%Y-%m-%d"),
                                "modified_timestamp": datetime.fromisoformat(
                                    item['modifiedTime'].replace('Z', '+00:00')
                                ).timestamp(),
                                "path": "/".join(path_parts),
                                "full_path": item['webViewLink'],
                                "hash": None  # Drive não fornece hash
                            }
                            
                            # Adiciona nota se existir
                            note_key = f"{discipline}_{item['name']}"
                            if note_key in self.notes:
                                file_info["notes"] = self.notes[note_key]
                            
                            files_by_discipline[discipline].append(file_info)
                            
                            # Adiciona a pasta atual para esta disciplina
                            if path_parts:
                                folders_by_discipline[discipline].add(path_parts[-1])
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
        except Exception as e:
            logger.error(f"Erro ao listar arquivos na pasta {folder_id}: {e}")
        
        # Converte sets para listas
        for disc_key in folders_by_discipline:
            folders_by_discipline[disc_key] = list(folders_by_discipline[disc_key])
            
        return files_by_discipline, folders_by_discipline

    def scan_all_disciplines(self):
        """Escaneia toda a pasta de projetos e organiza por disciplina"""
        result = {
            "last_scan": datetime.now().isoformat(),
            "disciplines": {}
        }
        
        if not self.service:
            logger.error("Serviço do Drive não está disponível. Abortando o scan.")
            return result

        logger.info("Iniciando scan recursivo da pasta de projetos...")
        
        # Faz o scan recursivo começando da pasta raiz
        files_by_disc, folders_by_disc = self.list_files_recursive(self.root_folder_id)
        
        # Organiza os resultados
        for disc_key, disc_info in self.config["disciplines"].items():
            files = files_by_disc[disc_key]
            folders = folders_by_disc[disc_key]
            total_size = sum(f['size_bytes'] for f in files)
            
            result["disciplines"][disc_key] = {
                "name": disc_info["name"],
                "path": self.root_folder_id,  # Pasta raiz
                "files": files,
                "folders": folders,
                "total_files": len(files),
                "total_size": self.format_size(total_size),
                "total_size_bytes": total_size
            }
            
            logger.info(f"{disc_info['name']}: {len(files)} arquivos ({self.format_size(total_size)})")
        
        return result

    def run_once(self):
        logger.info("Iniciando scan do Google Drive...")
        data = self.scan_all_disciplines()
        self.save_notes()
        logger.info("Scan do Google Drive completo.")
        return data


# Para teste local
if __name__ == "__main__":
    # Carrega as credenciais do .env
    from dotenv import load_dotenv
    load_dotenv()
    
    creds_json = os.getenv("GOOGLE_CREDS_JSON")
    if not creds_json:
        print("ERRO: GOOGLE_CREDS_JSON não encontrado no .env")
        exit(1)
        
    try:
        credentials_info = json.loads(creds_json)
        scanner = DriveScanner(credentials_info)
        data = scanner.run_once()
        
        # Salva o resultado
        with open("file_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("\nScan completo! Verifique file_data.json")
        
    except json.JSONDecodeError:
        print("ERRO: GOOGLE_CREDS_JSON não é um JSON válido")
    except Exception as e:
        print(f"ERRO: {e}")