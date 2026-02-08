from fastapi import FastAPI, Request, HTTPException
import json
import os
from datetime import datetime

app = FastAPI()

DATA_FILE = "data/locations.jsonl"
os.makedirs("data", exist_ok=True)

@app.get("/")
def health_check():
    return {"status": "running", "message": "Location logger is active"}

@app.post("/pub")
async def receive_location(request: Request):
    try:
        data = await request.json()
        
        data['_server_received_at'] = datetime.utcnow().isoformat()
        
        with open(DATA_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
            
        return []
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")