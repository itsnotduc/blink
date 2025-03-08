import heapq
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection

class TripManager:
    def __init__(self):
        # Updated station_map with station names and IDs
        self.station_map = {
            # Line 1
            "Mien Dong": "S101MD",
            "Suoi Tien Amusement Park": "S102STAP",
            "Saigon Hi-tech Park": "S103SHTP",
            "Thu Duc": "S104TD",
            "Binh Thai": "S105BT",
            "Phuoc Long": "S106PL",
            "Rach Chiec": "S107RC",
            "Anphu": "S108AP",
            "Thao Dien": "S109TD",  # Connects to MR2
            "Saigon Bridge": "S110SB",  # Connects to Line 5
            "Van Thanh": "S111VT",
            "Ba Son": "S112BS",
            "Opera House": "S113OH",
            "Ben Thanh": "S114BT",  # Connects to Lines 2, 3A, 4

            # Line 2
            "Cu Chi": "S201CC",
            "An Suong": "S202AS",
            "Tan Thoi Nhat": "S203TTN",
            "Tan Binh": "S204TB",
            "Pham Van Bach": "S205PVB",
            "Ba Queo": "S206BQ",  # Connects to Line 6
            "Nguyen Hong Dao": "S207NHD",
            "Bay Hien": "S208BH",  # Connects to Line 5
            "Pham Van Hai": "S209PVH",
            "Le Thi Rieng Park": "S210LTRP",
            "Hoa Hung": "S211HH",
            "Dan Chu": "S212DC",
            "Tao Dan": "S213TD",  # Connects to Line 3B
            # "Ben Thanh": "S114BT",  # Already defined, connects to Lines 1, 3A, 4
            "Ham Nghi": "S214HN",
            "Thu Thiem Square": "S215TTS",
            "Mai Chi Tho": "S216MCT",
            "Tran Nao": "S217TN",  # Connects to MR2
            "Binh Khanh": "S218BK",
            "Thu Thiem": "S219TT",

            # Line 3A
            "Tan Kien": "S301TK",
            "Eastern Bus Station": "S302EBS",
            "Phu Lam Park": "S303PLP",
            "Phu Lam": "S304PL",  # Connects to Line 6
            "Cay Go": "S305CG",
            "Cho Lon": "S306CL",
            "Thuan Kieu Plaza": "S307TKP",
            "University of Meds and Pharma": "S308UMP",  # Connects to Line 5
            "Hoa Binh Park": "S309HBP",
            "Cong Hoa": "S310CH",
            "Thai Binh": "S311TB",
            # "Ben Thanh": "S114BT",  # Already defined, connects to Lines 1, 2, 4

            # Line 3B
            "Di An": "S351DA",
            "Ga An Binh": "S352GAB",
            "Tam Binh": "S353TB",
            "Hiep Binh Phuoc": "S354HBP",
            "Binh Trieu": "S355BT",
            "Xo Viet Nghe Tinh": "S356XVNT",
            "Hang Xanh": "S357HX",  # Connects to Line 5
            "Nguyen Cuu Van": "S358NCV",
            "Saigon Zoo": "S359SZ",
            "Hoa Lu": "S360HL",
            "Turtle Lake": "S361TL",  # Connects to Line 4
            "Independence Palace": "S362IP",
            # "Tao Dan": "S213TD",  # Already defined, connects to Line 2
            # "Cong Hoa": "S310CH",  # Already defined, connects to Line 3A

            # Line 4
            "Thanh Xuan": "S401TX",
            "Nga Tu Ga": "S402NTG",
            "An Loc Bridge": "S403ALB",
            "An Nhon": "S404AN",
            "Nguyen Van Luong": "S405NVL",
            "Go Vap": "S406GV",  # Connects to MR3
            "175 Hospital": "S407175H",
            "Gia Dinh Park": "S408GDP",  # Connects to Line 4B
            "Phu Nhuan": "S409PN",  # Connects to Line 5
            "Kieu Bridge": "S410KB",
            "Le Van Tam Park": "S411LVTP",
            # "Turtle Lake": "S361TL",  # Already defined, connects to Line 3B
            # "Ben Thanh": "S114BT",  # Already defined, connects to Lines 1, 2, 3A
            "Ong Lanh Bridge": "S412OLB",
            "Yersin": "S413YS",
            "Khanh Hoa": "S414KH",
            "Tan Hung": "S415TH",
            "Nguyen Huu Tho": "S416NHT",
            "Nguyen Van Linh": "S417NVL",  # Connects to MR2
            "Phuoc Kien": "S418PK",
            "Pham Huu Lau": "S419PHL",
            "Ba Chiem": "S420BC",
            "Long Thoi": "S421LT",
            "Hiep Phuoc": "S422HP",

            # Line 4B
            # "Gia Dinh Park": "S408GDP",  # Already defined, connects to Line 4
            "Tan Son Nhat": "S451TSN",  # Connects to Line 4B1
            "Lang Cha Ca": "S452LCC",  # Connects to Line 5

            # Line 4B1
            # "Tan Son Nhat": "S451TSN",  # Already defined, connects to Line 4B
            "Hoang Van Thu Park": "S461HVTP",  # Connects to Line 5

            # Line 5
            # "Saigon Bridge": "S110SB",  # Already defined, connects to Line 1
            # "Hang Xanh": "S357HX",  # Already defined, connects to Line 3B
            "Ba Chieu": "S501BC",
            "Nguyen Van Dau": "S502NVD",
            # "Phu Nhuan": "S409PN",  # Already defined, connects to Line 4
            # "Hoang Van Thu Park": "S461HVTP",  # Already defined, connects to Line 4B1
            # "Lang Cha Ca": "S452LCC",  # Already defined, connects to Line 4B
            # "Bay Hien": "S208BH",  # Already defined, connects to Line 2
            "Tan Binh Market": "S503TBM",
            "Bac Hai": "S504BH",
            "HCMC Uni of Tech": "S505HUT",
            "Phu Tho": "S506PT",
            # "Uni of Meds and Pharma": "S308UMP",  # Already defined, connects to Line 3A
            "Xom Cui": "S507XC",
            "District 8 Bus Station": "S508D8BS",
            "Binh Hung": "S509BH",  # Connects to MR2
            "Can Giuoc": "S510CG",

            # Line 6
            # "Ba Queo": "S206BQ",  # Already defined, connects to Line 2
            "Au Co": "S601AC",
            "Vuon Lai": "S602VL",
            "Tan Phu": "S603TP",
            "Hoa Binh": "S604HB",
            "Luy Ban Bich": "S605LBB",
            # "Phu Lam": "S304PL",  # Already defined, connects to Line 3A

            # Monorail MR2
            "Thanh Da": "M201TD",
            # "Thao Dien": "S109TD",  # Already defined, connects to Line 1
            "Binh An": "M202BA",
            "Luong Dinh Cua": "M203LDC",
            # "Tran Nao": "S217TN",  # Already defined, connects to Line 2
            "South Thu Thiem": "M204STT",
            "Huynh Tan Phat": "M205HTP",
            "Tan Thuan Tay": "M206TTT",
            "Nguyen Thi Thap": "M207NTT",
            "Phu My Hung": "M208PMH",
            "Nguyen Duc Canh": "M209NDC",
            # "Nguyen Van Linh": "S417NVL",  # Already defined, connects to Line 4
            "RMIT": "M210RMIT",
            "Cau Ong Be": "M211COB",
            "Pham Hung": "M212PH",
            "Rach Hiep An": "M213RHA",
            # "Binh Hung": "S509BH",  # Already defined, connects to Line 5

            # Monorail MR3
            "Tan Chanh Hiep": "M301TCH",
            "Quang Trung Software City": "M302QTSC",
            "Phan Huy Ich": "M303PHI",
            "Tan Son": "M304TS",
            "Hanh Thong Tay": "M305HTT",
            "Thong Nhat": "M306TN",
            "Xom Thuoc": "M307XT",
            # "Go Vap": "S406GV",  # Already defined, connects to Line 4
        }

        # Updated station_graph with connections
        self.station_graph = {
            # Line 1
            "S101MD": [("S102STAP", "Line 1")],
            "S102STAP": [("S101MD", "Line 1"), ("S103SHTP", "Line 1")],
            "S103SHTP": [("S102STAP", "Line 1"), ("S104TD", "Line 1")],
            "S104TD": [("S103SHTP", "Line 1"), ("S105BT", "Line 1")],
            "S105BT": [("S104TD", "Line 1"), ("S106PL", "Line 1")],
            "S106PL": [("S105BT", "Line 1"), ("S107RC", "Line 1")],
            "S107RC": [("S106PL", "Line 1"), ("S108AP", "Line 1")],
            "S108AP": [("S107RC", "Line 1"), ("S109TD", "Line 1")],
            "S109TD": [("S108AP", "Line 1"), ("M201TD", "MR2")],  # Connects to MR2
            "S110SB": [("S109TD", "Line 1"), ("S357HX", "Line 5")],  # Connects to Line 5
            "S111VT": [("S110SB", "Line 1"), ("S112BS", "Line 1")],
            "S112BS": [("S111VT", "Line 1"), ("S113OH", "Line 1")],
            "S113OH": [("S112BS", "Line 1"), ("S114BT", "Line 1")],
            "S114BT": [("S113OH", "Line 1"), ("S214HN", "Line 2"), ("S311TB", "Line 3A"), ("S412OLB", "Line 4")],  # Connects to Lines 2, 3A, 4

            # Line 2
            "S201CC": [("S202AS", "Line 2")],
            "S202AS": [("S201CC", "Line 2"), ("S203TTN", "Line 2")],
            "S203TTN": [("S202AS", "Line 2"), ("S204TB", "Line 2")],
            "S204TB": [("S203TTN", "Line 2"), ("S205PVB", "Line 2")],
            "S205PVB": [("S204TB", "Line 2"), ("S206BQ", "Line 2")],
            "S206BQ": [("S205PVB", "Line 2"), ("S601AC", "Line 6")],  # Connects to Line 6
            "S207NHD": [("S206BQ", "Line 2"), ("S208BH", "Line 2")],
            "S208BH": [("S207NHD", "Line 2"), ("S502NVD", "Line 5")],  # Connects to Line 5
            "S209PVH": [("S208BH", "Line 2"), ("S210LTRP", "Line 2")],
            "S210LTRP": [("S209PVH", "Line 2"), ("S211HH", "Line 2")],
            "S211HH": [("S210LTRP", "Line 2"), ("S212DC", "Line 2")],
            "S212DC": [("S211HH", "Line 2"), ("S213TD", "Line 2")],
            "S213TD": [("S212DC", "Line 2"), ("S362IP", "Line 3B")],  # Connects to Line 3B
            "S114BT": [("S113OH", "Line 1"), ("S214HN", "Line 2"), ("S311TB", "Line 3A"), ("S412OLB", "Line 4")],
            "S214HN": [("S114BT", "Line 2"), ("S215TTS", "Line 2")],
            "S215TTS": [("S214HN", "Line 2"), ("S216MCT", "Line 2")],
            "S216MCT": [("S215TTS", "Line 2"), ("S217TN", "Line 2")],
            "S217TN": [("S216MCT", "Line 2"), ("S218BK", "Line 2"), ("M203LDC", "MR2")],  # Fixed here
            "S218BK": [("S217TN", "Line 2"), ("S219TT", "Line 2")],
            "S219TT": [("S218BK", "Line 2")],

            # Line 3A
            "S301TK": [("S302EBS", "Line 3A")],
            "S302EBS": [("S301TK", "Line 3A"), ("S303PLP", "Line 3A")],
            "S303PLP": [("S302EBS", "Line 3A"), ("S304PL", "Line 3A")],
            "S304PL": [("S303PLP", "Line 3A"), ("S605LBB", "Line 6")],  # Connects to Line 6
            "S305CG": [("S304PL", "Line 3A"), ("S306CL", "Line 3A")],
            "S306CL": [("S305CG", "Line 3A"), ("S307TKP", "Line 3A")],
            "S307TKP": [("S306CL", "Line 3A"), ("S308UMP", "Line 3A")],
            "S308UMP": [("S307TKP", "Line 3A"), ("S506PT", "Line 5")],  # Connects to Line 5
            "S309HBP": [("S308UMP", "Line 3A"), ("S310CH", "Line 3A")],
            "S310CH": [("S309HBP", "Line 3A"), ("S362IP", "Line 3B")],  # Connects to Line 3B
            "S311TB": [("S310CH", "Line 3A"), ("S114BT", "Line 3A")],
            # "S114BT": Already defined

            # Line 3B
            "S351DA": [("S352GAB", "Line 3B")],
            "S352GAB": [("S351DA", "Line 3B"), ("S353TB", "Line 3B")],
            "S353TB": [("S352GAB", "Line 3B"), ("S354HBP", "Line 3B")],
            "S354HBP": [("S353TB", "Line 3B"), ("S355BT", "Line 3B")],
            "S355BT": [("S354HBP", "Line 3B"), ("S356XVNT", "Line 3B")],
            "S356XVNT": [("S355BT", "Line 3B"), ("S357HX", "Line 3B")],
            "S357HX": [("S356XVNT", "Line 3B"), ("S110SB", "Line 5")],  # Connects to Line 5
            "S358NCV": [("S357HX", "Line 3B"), ("S359SZ", "Line 3B")],
            "S359SZ": [("S358NCV", "Line 3B"), ("S360HL", "Line 3B")],
            "S360HL": [("S359SZ", "Line 3B"), ("S361TL", "Line 3B")],
            "S361TL": [("S360HL", "Line 3B"), ("S411LVTP", "Line 4")],  # Connects to Line 4
            "S362IP": [("S361TL", "Line 3B"), ("S213TD", "Line 2"), ("S310CH", "Line 3A")],  # Connects to Lines 2, 3A
            # "S213TD": Already defined
            # "S310CH": Already defined

            # Line 4
            "S401TX": [("S402NTG", "Line 4")],
            "S402NTG": [("S401TX", "Line 4"), ("S403ALB", "Line 4")],
            "S403ALB": [("S402NTG", "Line 4"), ("S404AN", "Line 4")],
            "S404AN": [("S403ALB", "Line 4"), ("S405NVL", "Line 4")],
            "S405NVL": [("S404AN", "Line 4"), ("S406GV", "Line 4")],
            "S406GV": [("S405NVL", "Line 4"), ("M307XT", "MR3")],  # Connects to MR3
            "S407175H": [("S406GV", "Line 4"), ("S408GDP", "Line 4")],
            "S408GDP": [("S407175H", "Line 4"), ("S451TSN", "Line 4B")],  # Connects to Line 4B
            "S409PN": [("S408GDP", "Line 4"), ("S502NVD", "Line 5")],  # Connects to Line 5
            "S410KB": [("S409PN", "Line 4"), ("S411LVTP", "Line 4")],
            "S411LVTP": [("S410KB", "Line 4"), ("S361TL", "Line 4")],  # Connects to Line 3B
            # "S361TL": Already defined
            # "S114BT": Already defined
            "S412OLB": [("S114BT", "Line 4"), ("S413YS", "Line 4")],
            "S413YS": [("S412OLB", "Line 4"), ("S414KH", "Line 4")],
            "S414KH": [("S413YS", "Line 4"), ("S415TH", "Line 4")],
            "S415TH": [("S414KH", "Line 4"), ("S416NHT", "Line 4")],
            "S416NHT": [("S415TH", "Line 4"), ("S417NVL", "Line 4")],
            "S417NVL": [("S416NHT", "Line 4"), ("M209NDC", "MR2")],  # Connects to MR2
            "S418PK": [("S417NVL", "Line 4"), ("S419PHL", "Line 4")],
            "S419PHL": [("S418PK", "Line 4"), ("S420BC", "Line 4")],
            "S420BC": [("S419PHL", "Line 4"), ("S421LT", "Line 4")],
            "S421LT": [("S420BC", "Line 4"), ("S422HP", "Line 4")],
            "S422HP": [("S421LT", "Line 4")],

            # Line 4B
            # "S408GDP": Already defined
            "S451TSN": [("S408GDP", "Line 4B"), ("S461HVTP", "Line 4B1")],  # Connects to Line 4B1
            "S452LCC": [("S451TSN", "Line 4B"), ("S461HVTP", "Line 5")],  # Connects to Line 5

            # Line 4B1
            # "S451TSN": Already defined
            "S461HVTP": [("S451TSN", "Line 4B1"), ("S409PN", "Line 5")],  # Connects to Line 5

            # Line 5
            # "S110SB": Already defined
            # "S357HX": Already defined
            "S501BC": [("S357HX", "Line 5"), ("S502NVD", "Line 5")],
            "S502NVD": [("S501BC", "Line 5"), ("S409PN", "Line 5")],
            # "S409PN": Already defined
            # "S461HVTP": Already defined
            # "S452LCC": Already defined
            # "S208BH": Already defined
            "S503TBM": [("S208BH", "Line 5"), ("S504BH", "Line 5")],
            "S504BH": [("S503TBM", "Line 5"), ("S505HUT", "Line 5")],
            "S505HUT": [("S504BH", "Line 5"), ("S506PT", "Line 5")],
            "S506PT": [("S505HUT", "Line 5"), ("S308UMP", "Line 5")],
            # "S308UMP": Already defined
            "S507XC": [("S308UMP", "Line 5"), ("S508D8BS", "Line 5")],
            "S508D8BS": [("S507XC", "Line 5"), ("S509BH", "Line 5")],
            "S509BH": [("S508D8BS", "Line 5"), ("M213RHA", "MR2")],  # Connects to MR2
            "S510CG": [("S509BH", "Line 5")],

            # Line 6
            # "S206BQ": Already defined
            "S601AC": [("S206BQ", "Line 6"), ("S602VL", "Line 6")],
            "S602VL": [("S601AC", "Line 6"), ("S603TP", "Line 6")],
            "S603TP": [("S602VL", "Line 6"), ("S604HB", "Line 6")],
            "S604HB": [("S603TP", "Line 6"), ("S605LBB", "Line 6")],
            "S605LBB": [("S604HB", "Line 6"), ("S304PL", "Line 6")],
            # "S304PL": Already defined

            # Monorail MR2
            "M201TD": [("S109TD", "MR2"), ("M202BA", "MR2")],
            "M202BA": [("M201TD", "MR2"), ("M203LDC", "MR2")],
            "M203LDC": [("M202BA", "MR2"), ("S217TN", "MR2")],
            # "S217TN": Already defined
            "M204STT": [("S217TN", "MR2"), ("M205HTP", "MR2")],
            "M205HTP": [("M204STT", "MR2"), ("M206TTT", "MR2")],
            "M206TTT": [("M205HTP", "MR2"), ("M207NTT", "MR2")],
            "M207NTT": [("M206TTT", "MR2"), ("M208PMH", "MR2")],
            "M208PMH": [("M207NTT", "MR2"), ("M209NDC", "MR2")],
            "M209NDC": [("M208PMH", "MR2"), ("S417NVL", "MR2")],
            # "S417NVL": Already defined
            "M210RMIT": [("S417NVL", "MR2"), ("M211COB", "MR2")],
            "M211COB": [("M210RMIT", "MR2"), ("M212PH", "MR2")],
            "M212PH": [("M211COB", "MR2"), ("M213RHA", "MR2")],
            "M213RHA": [("M212PH", "MR2"), ("S509BH", "MR2")],
            # "S509BH": Already defined

            # Monorail MR3
            "M301TCH": [("M302QTSC", "MR3")],
            "M302QTSC": [("M301TCH", "MR3"), ("M303PHI", "MR3")],
            "M303PHI": [("M302QTSC", "MR3"), ("M304TS", "MR3")],
            "M304TS": [("M303PHI", "MR3"), ("M305HTT", "MR3")],
            "M305HTT": [("M304TS", "MR3"), ("M306TN", "MR3")],
            "M306TN": [("M305HTT", "MR3"), ("M307XT", "MR3")],
            "M307XT": [("M306TN", "MR3"), ("S406GV", "MR3")],
            # "S406GV": Already defined
        }

        # Updated valid_lines
        self.valid_lines = {"Line 1", "Line 2", "Line 3A", "Line 3B", "Line 4", "Line 4B", "Line 4B1", "Line 5", "Line 6", "MR2", "MR3"}
        self.route_tree = None

    # Rest of the methods remain unchanged
    def add_trip(self, trip, session_token):
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trips (description) VALUES (%s)", (trip,))
        conn.commit()
        cursor.close()
        release_db_connection(conn)

    def get_trips(self, session_token):
        conn = get_db_connection(session_token)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM trips")
        trips = [row[0] for row in cursor.fetchall()]
        cursor.close()
        release_db_connection(conn)
        return trips

    def get_station_id(self, station_name):
        return self.station_map.get(station_name, "Unknown")

    def find_path(self, start, end):
        if start not in self.station_graph or end not in self.station_graph:
            print(f"Start {start} or end {end} not in station_graph")
            return None
        visited = set()
        queue = [(start, [start])]
        print(f"Starting BFS from {start} to {end}")
        while queue:
            current, path = queue.pop(0)
            print(f"Visiting {current}, Path so far: {path}")
            if current == end:
                print(f"Found path: {path}")
                return path
            if current not in visited:
                visited.add(current)
                for neighbor, line in self.station_graph[current]:
                    if neighbor not in visited:
                        print(f"Adding neighbor {neighbor} via {line}")
                        queue.append((neighbor, path + [neighbor]))
        print(f"No path found from {start} to {end}")
        return None

    def longest_route_no_repeats(self):
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
        return longest_path

    def get_timetable(self, line, station, current_time):
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
        timetable = self.get_timetable(line, station, current_time)
        if timetable == ["Station closed!"] or not timetable:
            return None
        for time_str in timetable:
            dep_time = datetime.strptime(f"{current_time.date()} {time_str}", "%Y-%m-%d %H:%M")
            if dep_time >= current_time:
                return dep_time
        return None

    def find_fastest_path(self, start, end, start_time):
        start_id = self.get_station_id(start)
        end_id = self.get_station_id(end)
        if start_id not in self.station_graph or end_id not in self.station_graph:
            return None

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
                dep_time = self.get_next_departure(line, current_station, current_time)
                if dep_time is None:
                    continue
                travel_time = timedelta(minutes=3)  # Fixed travel time per segment
                arr_time = dep_time + travel_time

                if arr_time < earliest.get(neighbor, datetime.max):
                    earliest[neighbor] = arr_time
                    new_path = path + [self.station_map_inverse()[neighbor]]
                    heapq.heappush(pq, (arr_time, neighbor, new_path))

        return None

    def station_map_inverse(self):
        return {v: k for k, v in self.station_map.items()}