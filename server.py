from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

PLACEHOLDER_DB = []

class BatteryLog(BaseModel):
    device_id: str
    timestamp: str
    plugged: int
    level: int
    localisation: str
    event_type: str
    event_chargelevel: int

@app.post("/upload-logs")
async def upload_logs(logs: List[BatteryLog]):
    for log in logs:
        PLACEHOLDER_DB.append(log.dict())

    return {"status": "ok", "received": len(logs)}