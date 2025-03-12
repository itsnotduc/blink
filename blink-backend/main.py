# blink-backend/main.py
import bcrypt
from fastapi import FastAPI, HTTPException
from datetime import datetime
from trip_manager import TripManager
from db import close_db_pool, create_session, get_active_connections, get_max_connections, get_all_sessions, ADMIN_USERNAME, validate_session, session_store,db_pool
app = FastAPI(title="Blink Backend API", description="API for managing trips on the HCMC Metro")

trip_manager = TripManager()

@app.on_event("startup")
async def startup_event():
    print("Blink backend starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    close_db_pool()
    print("Blink backend shutting down...")

@app.get("/")
async def root():
    return {"message": "Blink backend live, fam!"}

@app.get("/login")
async def login():
    """Generate a new session token for a regular user."""
    session_token = create_session(role="user")
    return {"session_token": session_token}

@app.post("/admin/login")
async def admin_login(username: str, password: str):
    """Generate a new session token for an admin user."""
    if username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Fetch the stored hash from the database
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    db_pool.putconn(conn)
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    stored_hash = result[0].encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    session_token = create_session(role="admin")
    return {"session_token": session_token}

@app.post("/trips/add/")
async def add_trip(trip: str, session_token: str):
    try:
        trip_manager.add_trip(trip, session_token)
        return {"message": f"Trip '{trip}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding trip: {str(e)}")

@app.get("/trips/")
async def get_trips(session_token: str):
    try:
        trips = trip_manager.get_trips(session_token)
        return {"trips": trips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trips: {str(e)}")

@app.get("/station/{station}")
async def get_station_id(station: str):
    station_id = trip_manager.get_station_id(station)
    if station_id == "Unknown":
        raise HTTPException(status_code=404, detail=f"Station '{station}' not found")
    return {"station": station, "station_id": station_id}

@app.get("/route/{start}/{end}")
async def find_route(start: str, end: str):
    start_id = trip_manager.get_station_id(start)
    end_id = trip_manager.get_station_id(end)
    if start_id == "Unknown" or end_id == "Unknown":
        raise HTTPException(status_code=404, detail="One or both stations not found")
    
    path = trip_manager.find_path(start_id, end_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No route found from {start} to {end}")
    return {"start": start, "end": end, "path": path}

@app.get("/express_route/{start}/{end}")
async def find_express_route(start: str, end: str):
    start_id = trip_manager.get_station_id(start)
    end_id = trip_manager.get_station_id(end)
    if start_id == "Unknown" or end_id == "Unknown":
        raise HTTPException(status_code=404, detail="One or both stations not found")

    express_stations = {"S014BT", "S012BS", "S009TD", "S002STAP", "S004TDU"}  # Updated codes
    if start_id not in express_stations or end_id not in express_stations:
        raise HTTPException(status_code=400, detail="Express routes only available between Ben Thanh, Ba Son, Thao Dien, Suoi Tien Amusement Park, and Thu Duc")

    path = trip_manager.find_path(start_id, end_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No express route found from {start} to {end}")

    express_path = [station for station in path if station in express_stations]
    return {"start": start, "end": end, "express_path": express_path}

@app.get("/timetable/{line}/{station}")
async def get_timetable(line: str, station: str, current_time: str = None):
    if current_time:
        try:
            current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use 'YYYY-MM-DD HH:MM:SS'")
    
    try:
        timetable = trip_manager.get_timetable(line, station, current_time)
        if not timetable:
            raise HTTPException(status_code=404, detail=f"No timetable found for {station} on {line}")

        service_type = "regular"
        current_hour = current_time.hour if current_time else datetime.now().hour
        if line == "Line 1" and station in ["Ben Thanh", "Ba Son", "Thao Dien", "Suoi Tien Amusement Park", "Thu Duc"] and ((6 <= current_hour < 9) or (16 <= current_hour < 19)):
            service_type = "express"

        return {"line": line, "station": station, "timetable": timetable, "service_type": service_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timetable: {str(e)}")

@app.get("/longest_route/")
async def get_longest_route():
    try:
        longest_route = trip_manager.longest_route_no_repeats()
        if not longest_route:
            raise HTTPException(status_code=404, detail="No route found")
        return {"longest_route": longest_route}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding longest route: {str(e)}")

@app.get("/pool_status/")
async def get_pool_status(session_token: str):
    """Return the current status of the connection pool (admin-only)."""
    if not validate_session(session_token, required_role="admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "active_connections": get_active_connections(),
        "max_connections": get_max_connections()
    }

@app.get("/sessions/")
async def get_sessions(session_token: str):
    """Return all active sessions (admin-only)."""
    if not validate_session(session_token, required_role="admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    sessions = get_all_sessions()
    return {"sessions": sessions}

@app.post("/sessions/invalidate/")
async def invalidate_session(session_token: str, target_session_token: str):
    """Invalidate a specific session (admin-only)."""
    if not validate_session(session_token, required_role="admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if target_session_token in session_store:
        del session_store[target_session_token]
        return {"message": f"Session {target_session_token} invalidated successfully"}
    raise HTTPException(status_code=404, detail="Session not found")