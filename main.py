from fastapi import FastAPI, Request, HTTPException, Query, Header
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime, date
import hashlib

app = FastAPI()

DATA_FILE = "data/locations.jsonl"
API_KEYS_FILE = "data/api_keys.json"
os.makedirs("data", exist_ok=True)

# Initialize API keys file if it doesn't exist
if not os.path.exists(API_KEYS_FILE):
    with open(API_KEYS_FILE, "w") as f:
        json.dump({"keys": {}}, f)

def load_api_keys():
    """Load API keys from file"""
    try:
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"keys": {}}

def save_api_keys(data):
    """Save API keys to file"""
    with open(API_KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def verify_api_key(api_key: str = Header(None)):
    """Verify API key from header"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required", headers={"WWW-Authenticate": "Bearer"})
    
    keys_data = load_api_keys()
    if api_key not in keys_data.get("keys", {}):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return keys_data["keys"][api_key]

def load_locations():
    """Load all locations from file"""
    locations = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            for line in f:
                try:
                    locations.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return locations

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

@app.get("/history")
async def get_all_history(api_key: str = Header(None)):
    """Get all location history (requires API key)"""
    user = verify_api_key(api_key)
    locations = load_locations()
    return {"count": len(locations), "data": locations}

@app.get("/history/date")
async def get_history_by_date(query_date: str = Query(..., description="Date in YYYY-MM-DD format"), api_key: str = Header(None)):
    """Get location history for a specific date (requires API key)"""
    user = verify_api_key(api_key)
    
    try:
        target_date = datetime.strptime(query_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    locations = load_locations()
    filtered = []
    
    for loc in locations:
        try:
            # Try to parse server timestamp first
            ts_str = loc.get("_server_received_at") or loc.get("tst")
            if isinstance(ts_str, str):
                loc_date = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).date()
            else:
                loc_date = datetime.fromtimestamp(ts_str).date()
            
            if loc_date == target_date:
                filtered.append(loc)
        except (ValueError, TypeError):
            continue
    
    return {"date": query_date, "count": len(filtered), "data": filtered}

@app.post("/admin/generate-api-key")
async def generate_api_key(user_name: str = Query(...), basic_auth: str = Header(None)):
    """Generate a new API key for a user (admin endpoint, requires basic auth)"""
    # Simple admin auth: check against a master password
    expected_auth = "Basic " + __import__("base64").b64encode(b"admin:VIVA889").decode()
    
    if not basic_auth or basic_auth != expected_auth:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    # Generate API key (hash of user_name + timestamp)
    api_key = hashlib.sha256(f"{user_name}{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    keys_data = load_api_keys()
    keys_data["keys"][api_key] = {"user": user_name, "created_at": datetime.utcnow().isoformat()}
    save_api_keys(keys_data)
    
    return {"api_key": api_key, "user": user_name, "message": "API key generated successfully"}