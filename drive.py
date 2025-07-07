from google.oauth2 import service_account
from googleapiclient.discovery import build

class DriveSync:
    def __init__(self, key_file):
        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        self.svc = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_recursive(self, folder_id):
        # devolve lista de {name, id, mimeType, size, modifiedTime}
        q = f"'{folder_id}' in parents and trashed = false"
        page_token = None
        while True:
            resp = self.svc.files().list(
                q=q, fields="nextPageToken, files(id,name,mimeType,size,modifiedTime,parents)",
                pageToken=page_token
            ).execute()
            for f in resp["files"]:
                yield f
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
