#!/usr/bin/env python3
"""
Migration script to import existing JSONL location data into PostgreSQL
Run this after deploying the new architecture: python migrate_data.py
"""

import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Location


def migrate_jsonl_to_db():
    """Migrate data from locations.jsonl to PostgreSQL"""
    
    jsonl_file = "data/locations.jsonl"
    
    # Check if file exists
    if not os.path.exists(jsonl_file):
        print(f"No {jsonl_file} found. Skipping migration.")
        return
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        migrated_count = 0
        error_count = 0
        
        print(f"Reading {jsonl_file}...")
        
        with open(jsonl_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    
                    # Skip non-location records (status messages, etc)
                    if data.get("_type") != "location" and not (data.get("lat") and data.get("lon")):
                        error_count += 1
                        continue
                    tst = data.get("tst")
                    if tst:
                        try:
                            timestamp = datetime.fromtimestamp(tst)
                        except (ValueError, OSError):
                            timestamp = datetime.utcnow()
                    else:
                        timestamp = datetime.utcnow()
                    
                    # Parse server received timestamp if available
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
                    
                    # Commit in batches for better performance
                    if migrated_count % 100 == 0:
                        db.commit()
                        print(f"  Processed {migrated_count} records...")
                
                except Exception as e:
                    error_count += 1
                    print(f"  Error on line {line_num}: {e}")
                    continue
        
        # Final commit
        db.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"  Migrated: {migrated_count} records")
        print(f"  Errors: {error_count} records")
        
        # Verify
        total = db.query(Location).count()
        print(f"  Total in database: {total} records")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_jsonl_to_db()
