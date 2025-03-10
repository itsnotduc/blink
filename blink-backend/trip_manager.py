# blink-backend/trip_manager.py
from collections import defaultdict
import heapq
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection

class TripManager:
    TRAVEL_TIME = 3  # Time between consecutive stations on the same line (minutes)
    TRANSFER_TIME = 5  # Time to transfer between lines at the same station (minutes)

    def __init__(self):
        # Station map with station names to IDs
        self.station_map = {
            "Mien Dong": "S101MD",
            "Suoi Tien Amusement Park": "S102STAP",
            "Saigon Hi-tech Park": "S103SHTP",
            "Thu Duc": "S104TD",
            "Binh Thai": "S105BT",
            "Phuoc Long": "S106PL",
            "Rach Chiec": "S107RC",
            "Anphu": "S108AP",
            "Thao Dien": "S109TD",
            "Saigon Bridge": "S110SB",
            "Van Thanh": "S111VT",
            "Ba Son": "S112BS",
            "Opera House": "S113OH",
            "Ben Thanh": "S114BT",
            "Cu Chi": "S201CC",
            "An Suong": "S202AS",
            "Tan Thoi Nhat": "S203TTN",
            "Tan Binh": "S204TB",
            "Pham Van Bach": "S205PVB",
            "Ba Queo": "S206BQ",
            "Nguyen Hong Dao": "S207NHD",
            "Bay Hien": "S208BH",
            "Pham Van Hai": "S209PVH",
            "Le Thi Rieng Park": "S210LTRP",
            "Hoa Hung": "S211HH",
            "Dan Chu": "S212DC",
            "Tao Dan": "S213TD",
            "Ham Nghi": "S214HN",
            "Thu Thiem Square": "S215TTS",
            "Mai Chi Tho": "S216MCT",
            "Tran Nao": "S217TN",
            "Binh Khanh": "S218BK",
            "Thu Thiem": "S219TT",
            "Tan Kien": "S301TK",
            "Eastern Bus Station": "S302EBS",
            "Phu Lam Park": "S303PLP",
            "Phu Lam": "S304PL",
            "Cay Go": "S305CG",
            "Cho Lon": "S306CL",
            "Thuan Kieu Plaza": "S307TKP",
            "University of Meds and Pharma": "S308UMP",
            "Hoa Binh Park": "S309HBP",
            "Cong Hoa": "S310CH",
            "Thai Binh": "S311TB",
            "Di An": "S351DA",
            "Ga An Binh": "S352GAB",
            "Tam Binh": "S353TB",
            "Hiep Binh Phuoc": "S354HBP",
            "Binh Trieu": "S355BT",
            "Xo Viet Nghe Tinh": "S356XVNT",
            "Hang Xanh": "S357HX",
            "Nguyen Cuu Van": "S358NCV",
            "Saigon Zoo": "S359SZ",
            "Hoa Lu": "S360HL",
            "Turtle Lake": "S361TL",
            "Independence Palace": "S362IP",
            "Thanh Xuan": "S401TX",
            "Nga Tu Ga": "S402NTG",
            "An Loc Bridge": "S403ALB",
            "An Nhon": "S404AN",
            "Nguyen Van Luong": "S405NVL",
            "Go Vap": "S406GV",
            "175 Hospital": "S407175H",
            "Gia Dinh Park": "S408GDP",
            "Phu Nhuan": "S409PN",
            "Kieu Bridge": "S410KB",
            "Le Van Tam Park": "S411LVTP",
            "Ong Lanh Bridge": "S412OLB",
            "Yersin": "S413YS",
            "Khanh Hoa": "S414KH",
            "Tan Hung": "S415TH",
            "Nguyen Huu Tho": "S416NHT",
            "Nguyen Van Linh": "S417NVL",
            "Phuoc Kien": "S418PK",
            "Pham Huu Lau": "S419PHL",
            "Ba Chiem": "S420BC",
            "Long Thoi": "S421LT",
            "Hiep Phuoc": "S422HP",
            "Tan Son Nhat": "S451TSN",
            "Lang Cha Ca": "S452LCC",
            "Hoang Van Thu Park": "S461HVTP",
            "Ba Chieu": "S501BC",
            "Nguyen Van Dau": "S502NVD",
            "Tan Binh Market": "S503TBM",
            "Bac Hai": "S504BH",
            "HCMC Uni of Tech": "S505HUT",
            "Phu Tho": "S506PT",
            "Xom Cui": "S507XC",
            "District 8 Bus Station": "S508D8BS",
            "Binh Hung": "S509BH",
            "Can Giuoc": "S510CG",
            "Au Co": "S601AC",
            "Vuon Lai": "S602VL",
            "Tan Phu": "S603TP",
            "Hoa Binh": "S604HB",
            "Luy Ban Bich": "S605LBB",
            "Thanh Da": "M201TD",
            "Binh An": "M202BA",
            "Luong Dinh Cua": "M203LDC",
            "South Thu Thiem": "M204STT",
            "Huynh Tan Phat": "M205HTP",
            "Tan Thuan Tay": "M206TTT",
            "Nguyen Thi Thap": "M207NTT",
            "Phu My Hung": "M208PMH",
            "Nguyen Duc Canh": "M209NDC",
            "RMIT": "M210RMIT",
            "Cau Ong Be": "M211COB",
            "Pham Hung": "M212PH",
            "Rach Hiep An": "M213RHA",
            "Tan Chanh Hiep": "M301TCH",
            "Quang Trung Software City": "M302QTSC",
            "Phan Huy Ich": "M303PHI",
            "Tan Son": "M304TS",
            "Hanh Thong Tay": "M305HTT",
            "Thong Nhat": "M306TN",
            "Xom Thuoc": "M307XT",
        }

        # Define line sequences
        line1 = ["S101MD", "S102STAP", "S103SHTP", "S104TD", "S105BT", "S106PL", "S107RC",
                 "S108AP", "S109TD", "S110SB", "S111VT", "S112BS", "S113OH", "S114BT"]
        line2 = ["S201CC", "S202AS", "S203TTN", "S204TB", "S205PVB", "S206BQ", "S207NHD",
                 "S208BH", "S209PVH", "S210LTRP", "S211HH", "S212DC", "S213TD", "S114BT",
                 "S214HN", "S215TTS", "S216MCT", "S217TN", "S218BK", "S219TT"]
        line3a = ["S301TK", "S302EBS", "S303PLP", "S304PL", "S305CG", "S306CL", "S307TKP",
                  "S308UMP", "S309HBP", "S310CH", "S311TB", "S114BT"]
        line3b = ["S351DA", "S352GAB", "S353TB", "S354HBP", "S355BT", "S356XVNT", "S357HX",
                  "S358NCV", "S359SZ", "S360HL", "S361TL", "S362IP", "S213TD", "S310CH"]
        line4 = ["S401TX", "S402NTG", "S403ALB", "S404AN", "S405NVL", "S406GV", "S407175H",
                 "S408GDP", "S409PN", "S410KB", "S411LVTP", "S361TL", "S114BT", "S412OLB",
                 "S413YS", "S414KH", "S415TH", "S416NHT", "S417NVL", "S418PK", "S419PHL",
                 "S420BC", "S421LT", "S422HP"]
        line4b = ["S408GDP", "S451TSN", "S452LCC"]
        line4b1 = ["S451TSN", "S461HVTP"]
        line5 = ["S110SB", "S357HX", "S501BC", "S502NVD", "S409PN", "S461HVTP", "S452LCC",
                 "S208BH", "S503TBM", "S504BH", "S505HUT", "S506PT", "S308UMP", "S507XC",
                 "S508D8BS", "S509BH", "S510CG"]
        line6 = ["S206BQ", "S601AC", "S602VL", "S603TP", "S604HB", "S605LBB", "S304PL"]
        mr2 = ["M201TD", "S109TD", "M202BA", "M203LDC", "S217TN", "M204STT", "M205HTP",
               "M206TTT", "M207NTT", "M208PMH", "M209NDC", "S417NVL", "M210RMIT", "M211COB",
               "M212PH", "M213RHA", "S509BH"]
        mr3 = ["M301TCH", "M302QTSC", "M303PHI", "M304TS", "M305HTT", "M306TN", "M307XT",
               "S406GV"]

        # Dictionary of all lines
        lines = {
            "Line 1": line1,
            "Line 2": line2,
            "Line 3A": line3a,
            "Line 3B": line3b,
            "Line 4": line4,
            "Line 4B": line4b,
            "Line 4B1": line4b1,
            "Line 5": line5,
            "Line 6": line6,
            "MR2": mr2,
            "MR3": mr3
        }

        # Build station_graph
        self.station_graph = defaultdict(list)
        for line_name, stations in lines.items():
            for i in range(len(stations) - 1):
                self.station_graph[stations[i]].append((stations[i + 1], line_name))
                self.station_graph[stations[i + 1]].append((stations[i], line_name))

        # Add transfer connections explicitly (e.g., S114BT connects to multiple lines)
        transfer_stations = {
            "S114BT": ["Line 1", "Line 2", "Line 3A", "Line 4"],  # Ben Thanh
            "S109TD": ["Line 1", "MR2"],  # Thao Dien
            "S110SB": ["Line 1", "Line 5"],  # Saigon Bridge
            "S208BH": ["Line 2", "Line 5"],  # Bay Hien
            "S357HX": ["Line 3B", "Line 5"],  # Hang Xanh
            "S409PN": ["Line 4", "Line 5"],  # Phu Nhuan
            "S461HVTP": ["Line 4B1", "Line 5"],  # Hoang Van Thu Park
            "S452LCC": ["Line 4B", "Line 5"],  # Lang Cha Ca
            "S308UMP": ["Line 3A", "Line 5"],  # University of Meds and Pharma
            "S361TL": ["Line 3B", "Line 4"],  # Turtle Lake
            "S213TD": ["Line 2", "Line 3B"],  # Tao Dan
            "S310CH": ["Line 3A", "Line 3B"],  # Cong Hoa
            "S417NVL": ["Line 4", "MR2"],  # Nguyen Van Linh
            "S509BH": ["Line 5", "MR2"],  # Binh Hung
            "S406GV": ["Line 4", "MR3"],  # Go Vap
            "S304PL": ["Line 3A", "Line 6"],  # Phu Lam
            "S206BQ": ["Line 2", "Line 6"],  # Ba Queo
            "S217TN": ["Line 2", "MR2"],  # Tran Nao
        }
        for station, lines_at_station in transfer_stations.items():
            for line1 in lines_at_station:
                for line2 in lines_at_station:
                    if line1 != line2:
                        self.station_graph[station].append((station, line2))

        self.valid_lines = {"Line 1", "Line 2", "Line 3A", "Line 3B", "Line 4", "Line 4B",
                            "Line 4B1", "Line 5", "Line 6", "MR2", "MR3"}
        self.route_tree = None
        self.station_map_inv = {v: k for k, v in self.station_map.items()}
        self.build_weighted_graph()
    def build_weighted_graph(self):
        """
        Constructs a weighted graph where nodes are (station_id, line) tuples.
        - Travel edges: between consecutive stations on the same line (weight = TRAVEL_TIME).
        - Transfer edges: between different lines at the same station (weight = TRANSFER_TIME).
        """
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
                for neighbor, l in self.station_graph[station]:
                    if l == line:
                        self.weighted_graph[node].append(((neighbor, line), self.TRAVEL_TIME))
                for other_line in lines:
                    if other_line != line:
                        self.weighted_graph[node].append(((station, other_line), self.TRANSFER_TIME))

    def find_shortest_path(self, start_station, end_station):
        """
        Finds the shortest path from start_station to end_station using Dijkstra's algorithm.
        Returns: (path, total_time) where path is a list of station names and total_time is in minutes.
        """
        if start_station not in self.station_map or end_station not in self.station_map:
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

    def add_trip(self, trip, session_token):
        """Adds a trip description to the database."""
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trips (description) VALUES (%s)", (trip,))
        conn.commit()
        cursor.close()
        release_db_connection(conn)

    def get_trips(self, session_token):
        """Retrieves all trip descriptions from the database."""
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM trips")
        trips = [row[0] for row in cursor.fetchall()]
        cursor.close()
        release_db_connection(conn)
        return trips

    def get_station_id(self, station_name):
        """Returns the station ID for a given station name."""
        if station_name not in self.station_map:
            raise ValueError(f"Station {station_name} not found")
        return self.station_map[station_name]

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
        """
        Finds the fastest path considering departure times.
        Returns: (path, total_time) where total_time is in minutes.
        """
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
                # Use TRANSFER_TIME if staying at the same station (transfer), else TRAVEL_TIME
                time_to_neighbor = self.TRANSFER_TIME if neighbor == current_station else self.TRAVEL_TIME
                arr_time = dep_time + timedelta(minutes=time_to_neighbor)

                if arr_time < earliest.get(neighbor, datetime.max):
                    earliest[neighbor] = arr_time
                    new_path = path + [self.station_map_inv[neighbor]]
                    heapq.heappush(pq, (arr_time, neighbor, new_path))

        return None, 0