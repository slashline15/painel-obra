from fastapi import FastAPI, BackgroundTasks
from pathlib import Path
from scanner import FileScanner
from drive import DriveSync
import json, os, asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
BASE = Path(os.getenv("BASE_PATH"))
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 300))
JSON_PATH = Path("file_data.json")

scanner = FileScanner(BASE)
app = FastAPI()

def do_local_scan():
    data = scanner.run_once()
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

@app.get("/api/files")
async def get_files():
    if not JSON_PATH.exists():
        do_local_scan()
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))

@app.post("/api/refresh")
async def refresh(bg: BackgroundTasks):
    bg.add_task(do_local_scan)
    return {"status": "queued"}

# --- Scheduler ---
sched = AsyncIOScheduler()
sched.add_job(do_local_scan, "interval", seconds=SCAN_INTERVAL)
sched.start()
