# blink-backend/main.py
from fastapi import FastAPI, HTTPException
from datetime import datetime
from trip_manager import TripManager
from db import close_db_pool

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

@app.post("/trips/add/")
async def add_trip(trip: str):
    try:
        trip_manager.add_trip(trip)
        return {"message": f"Trip '{trip}' added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding trip: {str(e)}")

@app.get("/trips/")
async def get_trips():
    try:
        trips = trip_manager.get_trips()
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

    # Express routes on Line 1: Ben Thanh ↔ Thu Duc, Ben Thanh ↔ Suoi Tien
    express_stations = {"H1BT", "H1BS", "H1TD", "H1ST", "H1TDU"}
    if start_id not in express_stations or end_id not in express_stations:
        raise HTTPException(status_code=400, detail="Express routes only available between Ben Thanh, Ba Son, Thao Dien, Thu Duc, and Suoi Tien")

    path = trip_manager.find_path(start_id, end_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No express route found from {start} to {end}")

    # Filter path to include only express stations
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

        # Determine the type of service (regular or express)
        service_type = "regular"
        current_hour = current_time.hour if current_time else datetime.now().hour
        if line == "Line 1" and station in ["Ben Thanh", "Ba Son", "Thao Dien", "Suoi Tien", "Thu Duc"] and ((6 <= current_hour < 9) or (16 <= current_hour < 19)):
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