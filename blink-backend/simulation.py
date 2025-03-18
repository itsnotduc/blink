import logging
import time
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection, create_session
from trip_manager import TripManager
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Existing imports and logging setup are fine; enhance logging usage
def schedule_train_update(train_id, scheduler, trip_manager):
    conn = get_db_connection(create_session(role="admin"))
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT line_id, current_station_id, next_station_id
            FROM trains
            WHERE train_id = %s
        """, (train_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Train {train_id} not found")
            return
        line_id, current_station_id, next_station_id = row
        line_name = trip_manager.valid_lines.get(line_id)
        if not line_name:
            logger.error(f"Line ID {line_id} not found for train {train_id}")
            return
        station_name = trip_manager.station_map_inv[current_station_id]
        next_station_name = trip_manager.station_map_inv[next_station_id]
        current_time = datetime.now()

        next_dep = trip_manager.get_next_departure(line_name, station_name, next_station_name, current_time)
        if not next_dep:
            logger.info(f"No departures for train {train_id} at {station_name} on {line_name}")
            return

        scheduler.add_job(
            depart_train,
            'date',
            run_date=next_dep,
            args=[train_id, scheduler, trip_manager],
            id=f"depart_{train_id}",
            replace_existing=True
        )
        logger.info(f"Scheduled departure for train {train_id} at {next_dep}")
    finally:
        cursor.close()
        release_db_connection(conn)

def depart_train(train_id, scheduler, trip_manager):
    conn = get_db_connection(create_session(role="admin"))
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT line_id, current_station_id, next_station_id, current_route_id
            FROM trains
            WHERE train_id = %s
        """, (train_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Train {train_id} not found")
            return
        line_id, current_station_id, next_station_id, current_route_id = row

        cursor.execute("""
            UPDATE trains
            SET status = 'in_transit', last_updated = CURRENT_TIMESTAMP
            WHERE train_id = %s
        """, (train_id,))
        conn.commit()

        cursor.execute("""
            SELECT travel_time
            FROM routes
            WHERE route_id = %s
        """, (current_route_id,))
        travel_time = cursor.fetchone()[0]
        arrival_time = datetime.now() + timedelta(minutes=travel_time)

        scheduler.add_job(
            arrive_at_station,
            'date',
            run_date=arrival_time,
            args=[train_id, scheduler, trip_manager],
            id=f"arrive_{train_id}",
            replace_existing=True
        )
        logger.info(f"Train {train_id} departed from {current_station_id}, arriving at {next_station_id} at {arrival_time}")
    finally:
        cursor.close()
        release_db_connection(conn)

def arrive_at_station(train_id, scheduler, trip_manager):
    conn = get_db_connection(create_session(role="admin"))
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT line_id, current_station_id, next_station_id
            FROM trains
            WHERE train_id = %s
        """, (train_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Train {train_id} not found")
            return
        line_id, current_station_id, next_station_id = row

        cursor.execute("""
            UPDATE trains
            SET current_station_id = %s, status = 'at_station', last_updated = CURRENT_TIMESTAMP
            WHERE train_id = %s
        """, (next_station_id, train_id))

        cursor.execute("""
            SELECT route_id, to_station_id
            FROM routes
            WHERE from_station_id = %s AND line_id = %s
        """, (next_station_id, line_id))
        new_route = cursor.fetchone()
        if new_route:
            new_route_id, new_next_station_id = new_route
            cursor.execute("""
                UPDATE trains
                SET next_station_id = %s, current_route_id = %s
                WHERE train_id = %s
            """, (new_next_station_id, new_route_id, train_id))
        else:
            # Reverse direction at end of line
            cursor.execute("""
                SELECT route_id, from_station_id
                FROM routes
                WHERE to_station_id = %s AND line_id = %s
            """, (next_station_id, line_id))
            reverse_route = cursor.fetchone()
            if reverse_route:
                reverse_route_id, reverse_station_id = reverse_route
                cursor.execute("""
                    UPDATE trains
                    SET next_station_id = %s, current_route_id = %s
                    WHERE train_id = %s
                """, (reverse_station_id, reverse_route_id, train_id))
            else:
                logger.info(f"Train {train_id} reached end of line with no reverse route")

        conn.commit()
        schedule_train_update(train_id, scheduler, trip_manager)
    finally:
        cursor.close()
        release_db_connection(conn)

def run_simulation():
    scheduler = BackgroundScheduler()
    trip_manager = TripManager()
    start_date = datetime.now().date()
    trip_manager.generate_weekly_schedule(start_date)
    conn = get_db_connection(create_session(role="admin"))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT train_id FROM trains")
        train_ids = [row[0] for row in cursor.fetchall()]
        for train_id in train_ids:
            schedule_train_update(train_id, scheduler, trip_manager)
        logger.info("Simulation started")
    finally:
        cursor.close()
        release_db_connection(conn)
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Simulation shut down")

if __name__ == "__main__":
    run_simulation()