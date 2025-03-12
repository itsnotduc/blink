from collections import defaultdict
import heapq
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection, create_session

class TripManager:
    def __init__(self):
        # Initialize database connection for dynamic data
        conn = get_db_connection(create_session(role="user"))
        cursor = conn.cursor()

        # Fetch station map from stations table
        cursor.execute("SELECT station_id, station_name FROM stations")
        self.station_map = {row[0]: row[1] for row in cursor.fetchall()}
        self.station_map_inv = {v: k for k, v in self.station_map.items()}

        # Fetch lines and build station_graph
        self.station_graph = defaultdict(list)
        cursor.execute("""
            SELECT line_id, line_name FROM lines
        """)
        lines_data = cursor.fetchall()
        self.valid_lines = {row[1] for row in lines_data}
        for line_id, line_name in lines_data:
            cursor.execute("""
                SELECT from_station_id, to_station_id FROM routes WHERE line_id = %s
            """, (line_id,))
            route_segments = cursor.fetchall()
            for from_station, to_station in route_segments:
                self.station_graph[from_station].append((to_station, line_name))
                self.station_graph[to_station].append((from_station, line_name))

        # Fetch transfer stations (simplified for now, could be enhanced with a table)
        transfer_stations = {
            "S114BT": ["Line 1", "Line 2", "Line 3A", "Line 4"],
            "S109TD": ["Line 1", "MR2"],
            "S110SB": ["Line 1", "Line 5"],
            "S208BH": ["Line 2", "Line 5"],
            "S357HX": ["Line 3B", "Line 5"],
            "S409PN": ["Line 4", "Line 5"],
            "S461HVTP": ["Line 4B1", "Line 5"],
            "S452LCC": ["Line 4B", "Line 5"],
            "S308UMP": ["Line 3A", "Line 5"],
            "S361TL": ["Line 3B", "Line 4"],
            "S213TD": ["Line 2", "Line 3B"],
            "S310CH": ["Line 3A", "Line 3B"],
            "S417NVL": ["Line 4", "MR2"],
            "S509BH": ["Line 5", "MR2"],
            "S406GV": ["Line 4", "MR3"],
            "S304PL": ["Line 3A", "Line 6"],
            "S206BQ": ["Line 2", "Line 6"],
            "S217TN": ["Line 2", "MR2"],
        }
        for station, lines_at_station in transfer_stations.items():
            for line1 in lines_at_station:
                for line2 in lines_at_station:
                    if line1 != line2:
                        self.station_graph[station].append((station, line2))

        cursor.close()
        release_db_connection(conn)
        self.build_weighted_graph()

    def build_weighted_graph(self):
        """Builds a weighted graph using travel_time from routes and transfer_times."""
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
                # Fetch travel time for consecutive stations on the same line
                cursor.execute("""
                    SELECT r.to_station_id, r.travel_time
                    FROM routes r
                    WHERE r.from_station_id = %s AND r.line_id = (
                        SELECT line_id FROM lines WHERE line_name = %s
                    )
                """, (station, line))
                route_data = cursor.fetchall()
                for to_station, travel_time in route_data:
                    current_hour = datetime.now().hour
                    is_peak = (7 <= current_hour < 9) or (17 <= current_hour < 19)
                    # Travel time is constant, no peak/off-peak distinction
                    self.weighted_graph[node].append(((to_station, line), travel_time))

                # Add transfer edges using transfer_times table
                for other_line in lines:
                    if other_line != line:
                        cursor.execute("""
                            SELECT transfer_time_peak, transfer_time_offpeak
                            FROM transfer_times tt
                            JOIN routes r ON tt.route_id = r.route_id
                            WHERE r.from_station_id = %s AND r.line_id = (
                                SELECT line_id FROM lines WHERE line_name = %s
                            )
                        """, (station, line))
                        transfer_data = cursor.fetchone()
                        if transfer_data:
                            transfer_time_peak, transfer_time_offpeak = transfer_data
                            transfer_time = transfer_time_peak if is_peak else transfer_time_offpeak
                            self.weighted_graph[node].append(((station, other_line), transfer_time))

        cursor.close()
        release_db_connection(conn)

    # In trip_manager.py
    def find_shortest_path(self, start_station, end_station):
        """Finds the shortest path using Dijkstra's algorithm."""
        if start_station not in self.station_map_inv or end_station not in self.station_map_inv:
            return None, 0
        start_id = self.station_map_inv[start_station]  # Use station_map_inv to get station_id
        end_id = self.station_map_inv[end_station]      # Use station_map_inv to get station_id
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
                station_path = [self.station_map[sid] for sid in path]  # Convert back to station names
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

    # In trip_manager.py
    def add_trip(self, trip, session_token, user_id=None, start_station=None, end_station=None, start_time=None):
        """Adds a trip to the database with optional detailed fields."""
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
            return {"message": f"Trip {trip_id} added successfully", "trip_id": trip_id}  # Include trip_id in response
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error adding trip: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def get_trips(self, session_token):
        """Retrieves all trips from the database."""
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT description FROM trips WHERE description IS NOT NULL")
            trips = [row[0] for row in cursor.fetchall()]
            return {"trips": trips}
        except Exception as e:
            raise Exception(f"Error retrieving trips: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

        # In trip_manager.py
    def get_station_id(self, station_name):
        """Returns the station ID for a given station name."""
        if station_name not in self.station_map_inv:  # Use station_map_inv
            raise ValueError(f"Station {station_name} not found")
        return self.station_map_inv[station_name]  # Use station_map_inv

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
        """Generates a timetable for a given line and station."""
        if line not in self.valid_lines:
            return []
        hour = current_time.hour
        if hour < 6 or hour >= 22:
            return ["Station closed!"]
        is_peak = (7 <= hour < 9) or (17 <= hour < 19)
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
    def get_schedules(self, session_token, line_name, station_name):
        """Retrieves the schedule for a given line and station from the database."""
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
                return {"message": f"No schedules found for {station_name} on {line_name}"}
            
            schedule_list = [{"departure_time": row[0].strftime("%H:%M"), "day_type": row[1]} for row in schedules]
            return {"line": line_name, "station": station_name, "schedules": schedule_list}
        except Exception as e:
            raise Exception(f"Error retrieving schedules: {str(e)}")
        finally:
            cursor.close()
            release_db_connection(conn)

    def get_next_departure(self, line, station, current_time):
        """Finds the next departure time from the timetable."""
        timetable = self.get_timetable(line, station, current_time)
        if timetable == ["Station closed!"] or not timetable:
            return None
        for time_str in timetable:
            dep_time = datetime.strptime(f"{current_time.date()} {time_str}", "%Y-%m-%d %H:%M")
            if dep_time >= current_time:
                return dep_time
        return None

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
                    heapq.heappush(pq, (arr_time, neighbor, new_path))

        return None, 0

from db import create_session  # Import here to avoid circular import