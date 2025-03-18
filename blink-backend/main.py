import bcrypt
from fastapi import FastAPI, HTTPException, Form
from datetime import datetime
from trip_manager import TripManager
from db import close_db_pool, create_session, get_active_connections, get_max_connections, get_all_sessions, ADMIN_USERNAME, validate_session, session_store, db_pool
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Blink Backend API", description="API for managing trips on the HCMC Metro")
trip_manager = TripManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Blink backend starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    close_db_pool()
    logger.info("Blink backend shutting down...")

@app.get("/")
async def root():
    return {"message": "Blink backend live, fam!"}

@app.post("/signin")
async def signin(username_or_email: str = Form(...), password: str = Form(...)):
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, password_hash, role FROM users 
            WHERE username = %s OR email = %s
        """, (username_or_email, username_or_email))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, username, stored_hash, role = result
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user_id,))
        conn.commit()
        session_token = create_session(role=role)
        logger.info(f"User {username} signed in successfully")
        return {"message": f"Welcome back, {username}!", "session_token": session_token, "role": role}
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.post("/admin/login")
async def admin_login(username: str, password: str):
    """Generate a new session token for an admin user."""
    if username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        stored_hash = result[0].encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        session_token = create_session(role="admin")
        logger.info(f"Admin {username} logged in successfully")
        return {"session_token": session_token}
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.post("/trips/add/")
async def add_trip(trip: str, session_token: str):
    if not validate_session(session_token):
        raise HTTPException(status_code=403, detail="Invalid session")
    try:
        result = trip_manager.add_trip(trip, session_token)
        logger.info(f"Trip '{trip}' added by session {session_token}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid trip data: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Other endpoints remain largely unchanged; add logging where appropriate
# Example for /trips/:
@app.get("/trips/")
async def get_trips(session_token: str):
    if not validate_session(session_token):
        raise HTTPException(status_code=403, detail="Invalid session")
    try:
        trips = trip_manager.get_trips(session_token)
        logger.info(f"Trips retrieved for session {session_token}")
        return {"trips": trips}
    except Exception as e:
        logger.error(f"Error retrieving trips: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")