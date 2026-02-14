from fastapi import FastAPI, Request, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
import os
import logging

from database import init_db, get_db
from service import LocationService, APIKeyService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Manadia Location Logger")


def run_migration():
    """Run data migration from JSONL to PostgreSQL on startup"""
    import json
    from models import Location
    
    jsonl_file = "data/locations.jsonl"
    
    if not os.path.exists(jsonl_file):
        logger.info("No JSONL file found, skipping migration")
        return
    
    try:
        from database import SessionLocal
        db = SessionLocal()
        
        # Check if data already migrated
        existing_count = db.query(Location).count()
        if existing_count > 0:
            logger.info(f"Migration already completed: {existing_count} records in DB")
            db.close()
            return
        
        logger.info("Starting migration from JSONL to PostgreSQL...")
        migrated_count = 0
        skipped_count = 0
        
        with open(jsonl_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    
                    # Skip non-location records (status messages, etc)
                    if data.get("_type") != "location" and not (data.get("lat") and data.get("lon")):
                        skipped_count += 1
                        continue
                    
                    # Parse timestamp
                    tst = data.get("tst")
                    if tst:
                        try:
                            timestamp = datetime.fromtimestamp(tst)
                        except (ValueError, OSError):
                            timestamp = datetime.utcnow()
                    else:
                        timestamp = datetime.utcnow()
                    
                    # Parse server received timestamp
                    server_received_at = data.get("_server_received_at")
                    if server_received_at:
                        try:
                            server_received_at = datetime.fromisoformat(
                                server_received_at.replace('Z', '+00:00')
                            )
                        except (ValueError, AttributeError):
                            server_received_at = datetime.utcnow()
                    else:
                        server_received_at = datetime.utcnow()
                    
                    # Create location record
                    location = Location(
                        latitude=data.get("lat"),
                        longitude=data.get("lon"),
                        altitude=data.get("alt"),
                        accuracy=data.get("acc"),
                        timestamp=timestamp,
                        device_id=data.get("devid") or data.get("deviceId"),
                        tracker_id=data.get("tid"),
                        battery=data.get("batt"),
                        connection=data.get("conn"),
                        user_id=data.get("user"),
                        server_received_at=server_received_at,
                        raw_data=json.dumps(data)
                    )
                    
                    db.add(location)
                    migrated_count += 1
                    
                    # Commit in batches
                    if migrated_count % 100 == 0:
                        db.commit()
                        logger.info(f"  Migrated {migrated_count} records...")
                
                except Exception as e:
                    logger.warning(f"  Error on line {line_num}: {e}")
                    continue
        
        # Final commit
        db.commit()
        db.close()
        
        logger.info(f"Migration complete! Migrated: {migrated_count}, Skipped: {skipped_count}")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")


# Initialize database and run migration on startup
@app.on_event("startup")
def startup():
    init_db()
    run_migration()


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "running", "message": "Location logger is active"}


@app.post("/pub")
async def receive_location(request: Request, db: Session = Depends(get_db)):
    """
    Receive location data from OwnTracks.
    No authentication required (handled by Caddy basicauth).
    """
    try:
        data = await request.json()
        service = LocationService(db)
        location = service.ingest_location(data)
        return []
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def verify_api_key(x_api_key: str = Header(None), db: Session = Depends(get_db)) -> dict:
    """
    Verify API key from header.
    Returns key info if valid.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    service = APIKeyService(db)
    if not service.verify_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return service.get_api_key_info(x_api_key)


@app.get("/history")
async def get_all_history(
    db: Session = Depends(get_db),
    limit: int = Query(None, gt=0, le=10000),
    offset: int = Query(0, ge=0),
    key_info: dict = Depends(verify_api_key)
):
    """
    Get all location history with pagination.
    Requires valid API key.
    """
    service = LocationService(db)
    return service.get_history(limit=limit, offset=offset)


@app.get("/history/date")
async def get_history_by_date(
    query_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    key_info: dict = Depends(verify_api_key)
):
    """
    Get location history for a specific date.
    Requires valid API key.
    """
    try:
        target_date = datetime.strptime(query_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    service = LocationService(db)
    return service.get_history_by_date(target_date)


@app.get("/history/device/{device_id}")
async def get_device_history(
    device_id: str,
    db: Session = Depends(get_db),
    key_info: dict = Depends(verify_api_key)
):
    """
    Get all location history for a specific device.
    Requires valid API key.
    """
    service = LocationService(db)
    return service.get_device_history(device_id)


@app.post("/admin/generate-api-key")
async def generate_api_key(
    user_name: str = Query(...),
    description: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for a user.
    Protected by Caddy basicauth at /admin/* path.
    """
    service = APIKeyService(db)
    result = service.generate_api_key(user_name, description)
    return {**result, "message": "API key generated successfully"}


@app.post("/admin/revoke-api-key")
async def revoke_api_key(
    api_key: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    Protected by Caddy basicauth at /admin/* path.
    """
    service = APIKeyService(db)
    success = service.revoke_api_key(api_key)
    if success:
        return {"message": "API key revoked successfully"}
    else:
        raise HTTPException(status_code=404, detail="API key not found")