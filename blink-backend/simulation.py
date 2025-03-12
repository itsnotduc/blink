import logging
import time
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection, create_session
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

def update_train_position(train_id, scheduler):
    """Updates the position of a train in the database and schedules the next update."""
    session_token = create_session(role="admin")
    conn = get_db_connection(session_token)
    cursor = conn.cursor()
    total_duration_seconds = 0  # To track the total time for this cycle
    try:
        # Fetch current train details
        cursor.execute("""
            SELECT t.train_id, t.line_id, t.current_route_id, t.current_station_id, t.next_station_id, r.travel_time
            FROM trains t
            JOIN routes r ON t.current_route_id = r.route_id
            WHERE t.train_id = %s
        """, (train_id,))
        train = cursor.fetchone()
        if not train:
            logger.error(f"Train {train_id} not found in trains table")
            return None

        train_id, line_id, current_route_id, current_station_id, next_station_id, travel_time = train
        current_time = datetime.now()
        logger.info(f"Train {train_id} (Line {line_id}) at station {current_station_id}, moving to {next_station_id} (Route ID {current_route_id})")

        # Verify the current route matches the expected direction
        cursor.execute("""
            SELECT from_station_id, to_station_id
            FROM routes
            WHERE route_id = %s
        """, (current_route_id,))
        route_data = cursor.fetchone()
        if not route_data:
            logger.error(f"Route ID {current_route_id} not found for train {train_id}")
            return None
        from_station, to_station = route_data
        if from_station != current_station_id or to_station != next_station_id:
            logger.warning(f"Route mismatch for train {train_id}: Route ID {current_route_id} is {from_station} -> {to_station}, but train is at {current_station_id} heading to {next_station_id}")
            cursor.execute("""
                SELECT route_id
                FROM routes
                WHERE from_station_id = %s AND to_station_id = %s AND line_id = %s
            """, (current_station_id, next_station_id, line_id))
            new_route = cursor.fetchone()
            if new_route:
                current_route_id = new_route[0]
                logger.info(f"Updated current_route_id to {current_route_id} for train {train_id}")
            else:
                logger.error(f"No valid route found from {current_station_id} to {next_station_id} on Line {line_id}")
                return None

        # Check if train is at a station (status = 'at_station')
        cursor.execute("SELECT status FROM trains WHERE train_id = %s", (train_id,))
        current_status = cursor.fetchone()[0]
        if current_status != 'at_station':
            logger.info(f"Train {train_id} is not at a station (status: {current_status}), skipping update")
            return None

        # Determine if current time is peak based on peak_times
        cursor.execute("SELECT EXTRACT(DOW FROM %s) AS day_of_week", (current_time,))
        day_of_week = cursor.fetchone()[0]  # 0-6 (Sunday-Saturday)
        day_type = "weekday" if 1 <= day_of_week <= 5 else "weekend"
        cursor.execute("""
            SELECT peak_start_time, peak_end_time
            FROM peak_times pt
            WHERE pt.route_id = %s AND pt.day_type = %s
        """, (current_route_id, day_type))
        peak_periods = cursor.fetchall()
        is_peak = False
        current_time_obj = current_time.time()
        for start_time, end_time in peak_periods:
            if start_time <= current_time_obj <= end_time:
                is_peak = True
                break
        logger.info(f"Peak time check for train {train_id}: Day type {day_type}, Current time {current_time_obj}, Is peak? {is_peak}")

        # Fetch transfer time from transfer_times
        cursor.execute("""
            SELECT transfer_time_peak, transfer_time_offpeak
            FROM transfer_times tt
            WHERE tt.route_id = %s AND tt.station_id = %s
        """, (current_route_id, current_station_id))
        transfer_data = cursor.fetchone()
        transfer_time_minutes = transfer_data[0] if is_peak and transfer_data else transfer_data[1] if transfer_data else 1
        transfer_time_seconds = transfer_time_minutes * 60
        total_duration_seconds += transfer_time_seconds
        logger.info(f"Train {train_id} at {current_station_id} with transfer time {transfer_time_minutes} minutes ({transfer_time_seconds} seconds)")

        # Simulate transfer time in real-time
        time.sleep(transfer_time_seconds)
        cursor.execute("""
            UPDATE trains
            SET status = %s, last_updated = CURRENT_TIMESTAMP
            WHERE train_id = %s
        """, ('departed', train_id))
        conn.commit()
        logger.info(f"Train {train_id} departed from {current_station_id} after transfer")

        # Simulate transit in real-time
        cursor.execute("""
            UPDATE trains
            SET status = %s, last_updated = CURRENT_TIMESTAMP
            WHERE train_id = %s
        """, ('in_transit', train_id))
        conn.commit()
        travel_time_seconds = travel_time * 60
        total_duration_seconds += travel_time_seconds
        logger.info(f"Train {train_id} in transit to {next_station_id} for {travel_time} minutes ({travel_time_seconds} seconds)")
        time.sleep(travel_time_seconds)

        # Update to new station
        cursor.execute("""
            SELECT route_id, to_station_id
            FROM routes
            WHERE from_station_id = %s AND to_station_id = %s AND line_id = %s
        """, (current_station_id, next_station_id, line_id))
        current_route_check = cursor.fetchone()
        if not current_route_check:
            logger.error(f"No route found from {current_station_id} to {next_station_id} on Line {line_id} for train {train_id}")
            return None

        # Find the next segment in the same direction
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
                SET current_station_id = %s, next_station_id = %s, current_route_id = %s, status = %s, last_updated = CURRENT_TIMESTAMP
                WHERE train_id = %s
            """, (next_station_id, new_next_station_id, new_route_id, 'at_station', train_id))
            logger.info(f"Train {train_id} arrived at {next_station_id}, next stop is {new_next_station_id} (Route ID {new_route_id})")
        else:
            # Handle reversal at the end of the line
            cursor.execute("""
                SELECT route_id, from_station_id
                FROM routes
                WHERE to_station_id = %s AND line_id = %s LIMIT 1
            """, (next_station_id, line_id))
            reverse_route = cursor.fetchone()
            if reverse_route:
                reverse_route_id, reverse_from_station_id = reverse_route
                cursor.execute("""
                    UPDATE trains
                    SET current_station_id = %s, next_station_id = %s, current_route_id = %s, status = %s, last_updated = CURRENT_TIMESTAMP
                    WHERE train_id = %s
                """, (next_station_id, reverse_from_station_id, reverse_route_id, 'at_station', train_id))
                logger.info(f"Train {train_id} reached end of line at {next_station_id}, reversing to {reverse_from_station_id} (Route ID {reverse_route_id})")
            else:
                logger.warning(f"Train {train_id} at {next_station_id} has no further routes on Line {line_id}")
        conn.commit()

        # Return the total duration for scheduling the next update
        return total_duration_seconds

    except Exception as e:
        logger.error(f"Error updating train {train_id}: {str(e)}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_db_connection(conn)

def schedule_train_update(train_id, scheduler, start_time=None):
    """Schedules the next update for a train based on its transfer and travel time."""
    # If no start_time is provided, schedule immediately
    if start_time is None:
        start_time = datetime.now()

    # Define a wrapper to handle the scheduling logic
    def job_wrapper():
        duration = update_train_position(train_id, scheduler)
        if duration is not None:
            # Schedule the next run after the duration
            next_run_time = datetime.now() + timedelta(seconds=duration)
            scheduler.add_job(
                job_wrapper,
                'date',
                run_date=next_run_time,
                args=[],
                id=f"train_{train_id}",
                replace_existing=True
            )
            logger.info(f"Scheduled next update for train {train_id} at {next_run_time}")

    # Schedule the first run
    scheduler.add_job(
        job_wrapper,
        'date',
        run_date=start_time,
        args=[],
        id=f"train_{train_id}",
        replace_existing=True
    )

def run_simulation():
    """Runs the train simulation scheduler with dynamic scheduling."""
    scheduler = BackgroundScheduler()
    conn = get_db_connection(create_session(role="admin"))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT train_id FROM trains")
        train_ids = [row[0] for row in cursor.fetchall()]
        # Schedule the first update for each train immediately
        for train_id in train_ids:
            schedule_train_update(train_id, scheduler)
        logger.info("Train simulation scheduler started with dynamic scheduling for all trains")
    except Exception as e:
        logger.error(f"Failed to initialize simulation: {str(e)}")
    finally:
        cursor.close()
        release_db_connection(conn)

    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Simulation scheduler shut down gracefully")

if __name__ == "__main__":
    run_simulation()