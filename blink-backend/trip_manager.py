from collections import defaultdict
import heapq
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection, create_session
from fastapi import HTTPException
import psycopg2
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class TripManager:
    def __init__(self):
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()

        # Fetch station map
        cursor.execute("SELECT station_id, station_name FROM stations")
        stations_data = cursor.fetchall()
        self.station_map = {row[1]: row[0] for row in stations_data}
        self.station_map_inv = {row[0]: row[1] for row in stations_data}

        # Fetch lines
        cursor.execute("SELECT line_id, line_name FROM lines")
        lines_data = cursor.fetchall()
        self.valid_lines = {row[0]: row[1] for row in lines_data}

        # Build station_graph
        self.station_graph = defaultdict(list)
        for line_id, line_name in self.valid_lines.items():
            cursor.execute("""
                SELECT from_station_id, to_station_id FROM routes WHERE line_id = %s
            """, (line_id,))
            route_segments = cursor.fetchall()
            for from_station, to_station in route_segments:
                self.station_graph[from_station].append((to_station, line_name))
                self.station_graph[to_station].append((from_station, line_name))

        # Fetch transfer stations
        cursor.execute("""
            SELECT station_id, line_name 
            FROM transfer_stations 
            JOIN lines ON transfer_stations.line_id = lines.line_id
        """)
        transfer_data = cursor.fetchall()
        transfer_stations = defaultdict(list)
        for station_id, line_name in transfer_data:
            transfer_stations[station_id].append(line_name)
        for station, lines_at_station in transfer_stations.items():
            for line1 in lines_at_station:
                for line2 in lines_at_station:
                    if line1 != line2:
                        self.station_graph[station].append((station, line2))
        cursor.close()
        release_db_connection(conn)
        self.build_weighted_graph()
        logger.info("TripManager initialized")

    def build_weighted_graph(self, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()
        self.lines_per_station = defaultdict(set)
        for station in self.station_graph:
            for neighbor, line in self.station_graph[station]:
                self.lines_per_station[station].add(line)

        self.weighted_graph = {}
        for station in self.station_graph:
            lines = self.lines_per_station[station]
            for line in lines:
                node = (station, line)
                self.weighted_graph[node] = []
                # Fetch travel times between stations on the same line
                cursor.execute("""
                    SELECT r.to_station_id, r.travel_time
                    FROM routes r
                    WHERE r.from_station_id = %s AND r.line_id = (
                        SELECT line_id FROM lines WHERE line_name = %s
                    )
                """, (station, line))
                route_data = cursor.fetchall()
                for to_station, travel_time in route_data:
                    self.weighted_graph[node].append(((to_station, line), travel_time))

                # Fetch transfer times between lines at the same station
                for other_line in lines:
                    if other_line != line:
                        cursor.execute("""
                            SELECT transfer_time_peak, transfer_time_offpeak
                            FROM transfer_times
                            WHERE station_id = %s AND from_line_id = (
                                SELECT line_id FROM lines WHERE line_name = %s
                            ) AND to_line_id = (
                                SELECT line_id FROM lines WHERE line_name = %s
                            )
                        """, (station, line, other_line))
                        transfer_data = cursor.fetchone()
                        if transfer_data:
                            transfer_time_peak, transfer_time_offpeak = transfer_data
                            is_peak = (7 <= current_time.hour < 9) or (17 <= current_time.hour < 19)
                            transfer_time = transfer_time_peak if is_peak else transfer_time_offpeak
                            self.weighted_graph[node].append(((station, other_line), transfer_time))
        cursor.close()
        release_db_connection(conn)

    # In trip_manager.py
    def find_shortest_path(self, start_station, end_station):
        if start_station not in self.station_map_inv or end_station not in self.station_map_inv:
            return None, 0
        start_id = self.station_map[start_station]
        end_id = self.station_map[end_station]
        lines_start = self.lines_per_station[start_id]

        distances = {node: float('inf') for node in self.weighted_graph}
        for line in lines_start:
            distances[(start_id, line)] = 0
        pq = [(0, (start_id, line)) for line in lines_start]
        heapq.heapify(pq)
        parent = {node: None for node in self.weighted_graph}

        while pq:
            dist, current = heapq.heappop(pq)
            if current[0] == end_id:
                path = []
                while current:
                    path.append(current[0])
                    current = parent[current]
                path.reverse()
                station_path = [self.station_map_inv[sid] for sid in path]
                return station_path, dist
            if dist > distances[current]:
                continue
            for neighbor, weight in self.weighted_graph[current]:
                new_dist = dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    parent[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        return None, 0


    def add_trip(self, trip, session_token, user_id=None, start_station=None, end_station=None, start_time=None):
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trips (user_id, start_station_id, end_station_id, start_time, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING trip_id
            """, (user_id, self.station_map.get(start_station), self.station_map.get(end_station), start_time, trip))
            trip_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Trip {trip_id} added: {trip}")
            return {"message": f"Trip {trip_id} added successfully", "trip_id": trip_id}
        except psycopg2.IntegrityError as e:
            conn.rollback()
            logger.error(f"Integrity error adding trip: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid station or user data: {str(e)}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error adding trip: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def get_trips(self, session_token):
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT description FROM trips WHERE description IS NOT NULL")
            trips = [row[0] for row in cursor.fetchall()]
            return {"trips": trips}
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error retrieving trips: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)
            # In trip_manager.py
    def get_station_id(self, station_name):
        """Returns the station ID for a given station name."""
        if station_name not in self.station_map:  # Use station_map
            raise ValueError(f"Station {station_name} not found")
        return self.station_map[station_name]  # Use station_map

    def longest_route_no_repeats(self):
        """Finds the longest route without repeating stations."""
        def dfs(current, visited):
            longest = [current]
            for neighbor, _ in self.station_graph.get(current, []):
                if neighbor not in visited:
                    new_visited = visited | {neighbor}
                    sub_route = dfs(neighbor, new_visited)
                    if len(sub_route) + 1 > len(longest):
                        longest = [current] + sub_route
            return longest

        longest_path = []
        for start in self.station_graph:
            path = dfs(start, {start})
            if len(path) > len(longest_path):
                longest_path = path
        return [self.station_map_inv[sid] for sid in longest_path]

    def get_timetable(self, line, station, current_time):
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT start_time, end_time FROM lines WHERE line_name = %s", (line,))
            row = cursor.fetchone()
            if not row:
                return []
            start_time, end_time = row
            start_hour = start_time.hour
            end_hour = end_time.hour
            if current_time.hour < start_hour or current_time.hour >= end_hour:
                return ["Station closed!"]
            is_peak = current_time.hour < start_hour or current_time.hour >= end_hour
            frequency = 10 if is_peak else 15
            start_hour = 6
            times = []
            for minute in range(0, 60, frequency):
                time = current_time.replace(hour=start_hour, minute=minute, second=0, microsecond=0)
                while time <= current_time.replace(hour=22, minute=0, second=0, microsecond=0):
                    if time >= current_time:
                        times.append(time.strftime("%H:%M"))
                    time += timedelta(minutes=frequency)
                if times:
                    break
            return times if times else []
        finally:
            cursor.close()
            release_db_connection(conn)
    def get_schedules(self, session_token, line_name, station_name):
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        try:
            station_id = self.station_map.get(station_name)
            if not station_id:
                raise ValueError(f"Station {station_name} not found")
            
            cursor.execute("""
                SELECT departure_time, day_type
                FROM schedules
                WHERE line_id = (SELECT line_id FROM lines WHERE line_name = %s)
                AND station_id = %s
                ORDER BY departure_time
            """, (line_name, station_id))
            schedules = cursor.fetchall()
            if not schedules:
                raise ValueError(f"No schedules found for {station_name} on {line_name}")
            
            schedule_list = [{"departure_time": row[0].strftime("%H:%M"), "day_type": row[1]} for row in schedules]
            return {"line": line_name, "station": station_name, "schedules": schedule_list}
        except Exception as e:
            raise Exception(f"Error retrieving schedules: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)



    def get_next_departure(self, line, station, next_station, current_time):
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()
        try:
            station_id = self.station_map[station]
            next_station_id = self.station_map[next_station]
            line_id = next(lid for lid, lname in self.valid_lines.items() if lname == line)
            day_type = "weekend" if current_time.weekday() >= 5 else "weekday"
            cursor.execute("SELECT holiday_date FROM holidays WHERE holiday_date = %s", (current_time.date(),))
            if cursor.fetchone():
                day_type = "holiday"
            cursor.execute("""
                SELECT departure_time FROM schedules
                WHERE line_id = %s AND station_id = %s AND next_station_id = %s AND day_type = %s
                AND departure_time >= %s
                ORDER BY departure_time LIMIT 1
            """, (line_id, station_id, next_station_id, day_type, current_time.time()))
            next_dep = cursor.fetchone()
            if next_dep:
                dep_time = datetime.combine(current_time.date(), next_dep[0])
                if dep_time < current_time:
                    dep_time += timedelta(days=1)
                return dep_time
            return None
        finally:
            cursor.close()
            release_db_connection(conn)

    def find_fastest_path(self, start, end, start_time):
        """Finds the fastest path considering departure times."""
        start_id = self.get_station_id(start)
        end_id = self.get_station_id(end)
        if start_id not in self.station_graph or end_id not in self.station_graph:
            return None, 0

        pq = [(start_time, start_id, [start])]
        earliest = {start_id: start_time}

        while pq:
            current_time, current_station, path = heapq.heappop(pq)
            if current_station == end_id:
                total_time = (current_time - start_time).total_seconds() / 60
                return path, total_time

            if current_time > earliest.get(current_station, datetime.max):
                continue

            for neighbor, line in self.station_graph[current_station]:
                dep_time = self.get_next_departure(line, self.station_map_inv[current_station], current_time)
                if dep_time is None:
                    continue
                # Fetch travel time from routes table
                conn = get_db_connection(create_session(role="user"))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT travel_time
                    FROM routes
                    WHERE from_station_id = %s AND to_station_id = %s AND line_id = (
                        SELECT line_id FROM lines WHERE line_name = %s
                    )
                """, (current_station, neighbor, line))
                route_data = cursor.fetchone()
                cursor.close()
                release_db_connection(conn)
                if route_data:
                    travel_time = route_data[0]
                else:
                    travel_time = 5  # Default travel time if not found

                # Fetch transfer time if applicable (same station, different line)
                if current_station == neighbor:
                    cursor = get_db_connection(create_session(role="user")).cursor()
                    cursor.execute("""
                        SELECT transfer_time_peak, transfer_time_offpeak
                        FROM transfer_times tt
                        JOIN routes r ON tt.route_id = r.route_id
                        WHERE r.from_station_id = %s AND r.line_id = (
                            SELECT line_id FROM lines WHERE line_name = %s
                        )
                    """, (current_station, line))
                    transfer_data = cursor.fetchone()
                    cursor.close()
                    release_db_connection(conn)
                    if transfer_data:
                        transfer_time_peak, transfer_time_offpeak = transfer_data
                        is_peak = (7 <= current_time.hour < 9) or (17 <= current_time.hour < 19)
                        travel_time = transfer_time_peak if is_peak else transfer_time_offpeak
                arr_time = dep_time + timedelta(minutes=travel_time)

                if arr_time < earliest.get(neighbor, datetime.max):
                    earliest[neighbor] = arr_time
                    new_path = path + [self.station_map_inv[neighbor]]
    
    def generate_weekly_schedule(self, start_date):
        conn = get_db_connection(create_session(role="admin"))
        cursor = conn.cursor()
        end_date = start_date + timedelta(days=7)
        current_date = start_date

        while current_date < end_date:
            # Fetch template_name instead of template_id
            cursor.execute("""
                SELECT st.template_name
                FROM annual_calendar ac
                JOIN schedule_templates st ON ac.template_id = st.template_id
                WHERE ac.date_id = %s
            """, (current_date,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"No template found for date {current_date}, skipping")
                current_date += timedelta(days=1)
                continue
            day_type = row[0]  # e.g., 'Weekday' or 'Weekend'

            cursor.execute("SELECT line_id, line_name, start_time, end_time FROM lines")
            lines = cursor.fetchall()

            for line_id, line_name, start_time, end_time in lines:
                cursor.execute("SELECT pattern_id FROM service_patterns WHERE line_id = %s", (line_id,))
                patterns = cursor.fetchall()

                for (pattern_id,) in patterns:
                    cursor.execute("""
                        SELECT station_id, station_sequence, dwell_time
                        FROM service_pattern_details
                        WHERE pattern_id = %s
                        ORDER BY station_sequence
                    """, (pattern_id,))
                    stations = cursor.fetchall()
                    if not stations:
                        logger.warning(f"No stations found for pattern {pattern_id} on line {line_name}")
                        continue

                    cursor.execute("""
                        SELECT start_time, end_time, headway_minutes
                        FROM frequency_rules
                        WHERE template_id = (SELECT template_id FROM schedule_templates WHERE template_name = %s)
                        AND line_id = %s AND pattern_id = %s
                        ORDER BY start_time
                    """, (day_type, line_id, pattern_id))
                    frequency_rules = cursor.fetchall()

                    if not frequency_rules:
                        logger.warning(f"No frequency rules for {day_type}, line {line_name}, pattern {pattern_id}")
                        continue

                    departure_times = []
                    for rule_start, rule_end, headway in frequency_rules:
                        start_dt = datetime.combine(current_date, rule_start)
                        end_dt = datetime.combine(current_date, rule_end)
                        current_time = start_dt
                        while current_time < end_dt:
                            departure_times.append(current_time)
                            current_time += timedelta(minutes=headway)

                    for dep_time in departure_times:
                        current_dt = dep_time
                        for i, (station_id, seq, dwell_time) in enumerate(stations):
                            next_station_id = stations[i + 1][0] if i < len(stations) - 1 else None
                            if next_station_id:
                                cursor.execute("""
                                    SELECT travel_time
                                    FROM routes
                                    WHERE line_id = %s AND from_station_id = %s AND to_station_id = %s
                                """, (line_id, station_id, next_station_id))
                                row = cursor.fetchone()
                                travel_time = row[0] if row else 5

                                cursor.execute("""
                                    INSERT INTO schedules (line_id, station_id, departure_time, day_type, next_station_id)
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT (line_id, station_id, departure_time, day_type) DO NOTHING
                                """, (line_id, station_id, current_dt.time(), day_type, next_station_id))

                                current_dt += timedelta(seconds=dwell_time)
                                current_dt += timedelta(minutes=travel_time)
                            else:
                                cursor.execute("""
                                    INSERT INTO schedules (line_id, station_id, departure_time, day_type, next_station_id)
                                    VALUES (%s, %s, %s, %s, NULL)
                                    ON CONFLICT (line_id, station_id, departure_time, day_type) DO NOTHING
                                """, (line_id, station_id, current_dt.time(), day_type))

                current_date += timedelta(days=1)
        conn.commit()
        cursor.close()
        release_db_connection(conn)
        logger.info(f"Generated weekly schedule from {start_date} to {end_date}")
    def get_next_departure(self, line, station, next_station, current_time):
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()
        try:
            station_id = self.station_map[station]
            next_station_id = self.station_map[next_station]
            line_id = next(lid for lid, lname in self.valid_lines.items() if lname == line)

            cursor.execute("""
                SELECT st.template_name
                FROM annual_calendar ac
                JOIN schedule_templates st ON ac.template_id = st.template_id
                WHERE ac.date_id = %s
            """, (current_time.date(),))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"No template for date {current_time.date()}")
                return None
            day_type = row[0]  # e.g., 'Weekday' or 'Weekend'

            cursor.execute("""
                SELECT departure_time FROM schedules
                WHERE line_id = %s AND station_id = %s AND next_station_id = %s AND day_type = %s
                AND departure_time >= %s
                ORDER BY departure_time LIMIT 1
            """, (line_id, station_id, next_station_id, day_type, current_time.time()))
            next_dep = cursor.fetchone()
            if next_dep:
                dep_time = datetime.combine(current_time.date(), next_dep[0])
                if dep_time < current_time:
                    dep_time += timedelta(days=1)
                return dep_time
            return None
        finally:
            cursor.close()
            release_db_connection(conn)
        
