# blink-backend/trip_manager.py
from collections import deque
from datetime import datetime, timedelta
from db import get_db_connection, release_db_connection

class Node:
    def __init__(self, stop):
        self.stop = stop
        self.left = None
        self.right = None

class TripManager:
    def __init__(self):
        # Updated station_map with new stations
        self.station_map = {
            # Line 1: Ben Thanh -> Suoi Tien
            "Ben Thanh": "H1BT", "Ba Son": "H1BS", "Van Thanh": "H1VT", "Thao Dien": "H1TD", "An Phu": "H1AP", "Suoi Tien": "H1ST", "Thu Duc": "H1TDU",
            # Line 2: An Suong -> Thu Thiem
            "An Suong": "H2AS", "Tan Chanh Hiep": "H2TC", "Thu Thiem": "H2TT", "Tao Dan": "H2TD", "Le Thi Rieng": "H2LT", "Pham Van Hai": "H2PV", "Ba Queo": "H2BQ",
            # Line 3: Tan Binh -> Thu Duc -> Hiep Phuoc
            "Tan Kien": "H3TK", "Phu Lam": "H3PL", "Cholon": "H3CH", "Cong Hoa": "H3CO", "Hiep Binh Phuoc": "H3HB", "Nguyen Thuong Hien": "H3NT",
            "Tan Binh": "H3TB", "Tan Son Nhat Airport": "H3TS", "Thu Duc": "H1TDU", "Hiep Phuoc": "H3HP",
            # Line 4: Thanh Xuan -> Nguyen Van Linh
            "Thanh Xuan": "H4TX", "Nga Tu Ga": "H4NT", "An Loc": "H4AL", "An Nhon": "H4AN", "Nguyen Van Luc": "H4NL", "Go Vap": "H4GV", "Gia Dinh Park": "H4GD", "Phu Nhuan": "H4PN",
            "Saigon Bridge": "H4SB", "District 7": "H4D7", "Nguyen Van Linh": "H4NV",
            # Line 5: Can Gio -> Tan Phu
            "Bay Hien": "H5BH", "Sai Gon Bridge": "H5SG", "Tan Cang": "H5TC", "Can Gio": "H5CG", "Tan Phu": "H5TP", "Tan Son Nhat Airport": "H3TS", "District 7": "H4D7",
            # Line 6: Ba Queo -> Phuoc Long
            "Phuoc Long": "H6PL"
        }

        # Updated station_graph with new connections
        self.station_graph = {
            # Line 1: Ben Thanh -> Suoi Tien
            "H1BT": ["H1BS"], "H1BS": ["H1BT", "H1VT"], "H1VT": ["H1BS", "H1TD", "H4PN"], "H1TD": ["H1VT", "H1AP"], "H1AP": ["H1TD", "H1ST"], "H1ST": ["H1AP", "H1TDU"], "H1TDU": ["H1ST"],
            # Line 2: An Suong -> Thu Thiem
            "H2AS": ["H2TC"], "H2TC": ["H2AS", "H2BQ"], "H2BQ": ["H2TC", "H2PV"], "H2PV": ["H2BQ", "H2LT"], "H2LT": ["H2PV", "H2TD"], "H2TD": ["H2LT", "H1BT"], "H1BT": ["H2TD", "H2TT"], "H2TT": ["H1BT", "H1TDU"],
            # Line 3: Tan Binh -> Thu Duc -> Hiep Phuoc
            "H3TK": ["H3PL"], "H3PL": ["H3TK", "H3CH"], "H3CH": ["H3PL", "H1BT"], "H1BT": ["H3CH", "H3TB"], "H3TB": ["H1BT", "H3TS"], "H3TS": ["H3TB", "H3NT"], "H3NT": ["H3TS", "H1BS"], "H1BS": ["H3NT", "H3HB"], "H3HB": ["H1BS", "H1TDU"], "H1TDU": ["H3HB", "H3HP"], "H3HP": ["H1TDU"],
            # Line 4: Thanh Xuan -> Nguyen Van Linh
            "H4TX": ["H4NT"], "H4NT": ["H4TX", "H4AL"], "H4AL": ["H4NT", "H4AN"], "H4AN": ["H4AL", "H4NL"], "H4NL": ["H4AN", "H4GV"], "H4GV": ["H4NL", "H4GD"], "H4GD": ["H4GV", "H4PN"], "H4PN": ["H4GD", "H1VT", "H4SB"], "H4SB": ["H4PN", "H4D7"], "H4D7": ["H4SB", "H4NV"], "H4NV": ["H4D7"],
            # Line 5: Can Gio -> Tan Phu
            "H5CG": ["H5BH"], "H5BH": ["H5CG", "H1BT"], "H1BT": ["H5BH", "H5TC"], "H5TC": ["H1BT", "H5SG"], "H5SG": ["H5TC", "H3TS"], "H3TS": ["H5SG", "H4D7"], "H4D7": ["H3TS", "H5TP"], "H5TP": ["H4D7"],
            # Line 6: Ba Queo -> Phuoc Long
            "H2BQ": ["H2TT"], "H2TT": ["H2BQ", "H6PL"], "H6PL": ["H2TT"]
        }

        self.route_tree = None

        # Updated timetable with new frequencies
        self.timetable = {
            "Line 1": {
                "H1BT": {
                    "peak": self.generate_schedule("06:00", "09:00", 4) + self.generate_schedule("16:00", "19:00", 4),
                    "off_peak": self.generate_schedule("09:00", "16:00", 9) + self.generate_schedule("19:00", "23:00", 9),
                    "late": self.generate_schedule("23:00", "00:30", 15),
                    "express": self.generate_schedule("06:00", "09:00", 15) + self.generate_schedule("16:00", "19:00", 15),
                    "closing_time": "00:30"
                },
                "H1BS": {
                    "peak": self.generate_schedule("06:02", "09:02", 4) + self.generate_schedule("16:02", "19:02", 4),
                    "off_peak": self.generate_schedule("09:02", "16:02", 9) + self.generate_schedule("19:02", "23:02", 9),
                    "late": self.generate_schedule("23:02", "00:32", 15),
                    "express": self.generate_schedule("06:02", "09:02", 15) + self.generate_schedule("16:02", "19:02", 15),
                    "closing_time": "00:30"
                },
                "H1VT": {
                    "peak": self.generate_schedule("06:04", "09:04", 4) + self.generate_schedule("16:04", "19:04", 4),
                    "off_peak": self.generate_schedule("09:04", "16:04", 9) + self.generate_schedule("19:04", "23:04", 9),
                    "late": self.generate_schedule("23:04", "00:34", 15),
                    "closing_time": "00:30"
                },
                "H1TD": {
                    "peak": self.generate_schedule("06:06", "09:06", 4) + self.generate_schedule("16:06", "19:06", 4),
                    "off_peak": self.generate_schedule("09:06", "16:06", 9) + self.generate_schedule("19:06", "23:06", 9),
                    "late": self.generate_schedule("23:06", "00:36", 15),
                    "express": self.generate_schedule("06:06", "09:06", 15) + self.generate_schedule("16:06", "19:06", 15),
                    "closing_time": "00:30"
                },
                "H1AP": {
                    "peak": self.generate_schedule("06:08", "09:08", 4) + self.generate_schedule("16:08", "19:08", 4),
                    "off_peak": self.generate_schedule("09:08", "16:08", 9) + self.generate_schedule("19:08", "23:08", 9),
                    "late": self.generate_schedule("23:08", "00:38", 15),
                    "closing_time": "00:30"
                },
                "H1ST": {
                    "peak": self.generate_schedule("06:10", "09:10", 4) + self.generate_schedule("16:10", "19:10", 4),
                    "off_peak": self.generate_schedule("09:10", "16:10", 9) + self.generate_schedule("19:10", "23:10", 9),
                    "late": self.generate_schedule("23:10", "00:40", 15),
                    "express": self.generate_schedule("06:10", "09:10", 15) + self.generate_schedule("16:10", "19:10", 15),
                    "closing_time": "00:30"
                },
                "H1TDU": {
                    "peak": self.generate_schedule("06:12", "09:12", 4) + self.generate_schedule("16:12", "19:12", 4),
                    "off_peak": self.generate_schedule("09:12", "16:12", 9) + self.generate_schedule("19:12", "23:12", 9),
                    "late": self.generate_schedule("23:12", "00:42", 15),
                    "express": self.generate_schedule("06:12", "09:12", 15) + self.generate_schedule("16:12", "19:12", 15),
                    "closing_time": "00:30"
                }
            },
            "Line 2": {
                "H2AS": {
                    "peak": self.generate_schedule("06:00", "09:00", 4) + self.generate_schedule("16:00", "19:00", 4),
                    "off_peak": self.generate_schedule("09:00", "16:00", 9) + self.generate_schedule("19:00", "23:00", 9),
                    "late": self.generate_schedule("23:00", "00:30", 20),
                    "closing_time": "00:30"
                },
                "H2TC": {
                    "peak": self.generate_schedule("06:02", "09:02", 4) + self.generate_schedule("16:02", "19:02", 4),
                    "off_peak": self.generate_schedule("09:02", "16:02", 9) + self.generate_schedule("19:02", "23:02", 9),
                    "late": self.generate_schedule("23:02", "00:32", 20),
                    "closing_time": "00:30"
                },
                "H2BQ": {
                    "peak": self.generate_schedule("06:04", "09:04", 4) + self.generate_schedule("16:04", "19:04", 4),
                    "off_peak": self.generate_schedule("09:04", "16:04", 9) + self.generate_schedule("19:04", "23:04", 9),
                    "late": self.generate_schedule("23:04", "00:34", 20),
                    "closing_time": "00:30"
                },
                "H2PV": {
                    "peak": self.generate_schedule("06:06", "09:06", 4) + self.generate_schedule("16:06", "19:06", 4),
                    "off_peak": self.generate_schedule("09:06", "16:06", 9) + self.generate_schedule("19:06", "23:06", 9),
                    "late": self.generate_schedule("23:06", "00:36", 20),
                    "closing_time": "00:30"
                },
                "H2LT": {
                    "peak": self.generate_schedule("06:08", "09:08", 4) + self.generate_schedule("16:08", "19:08", 4),
                    "off_peak": self.generate_schedule("09:08", "16:08", 9) + self.generate_schedule("19:08", "23:08", 9),
                    "late": self.generate_schedule("23:08", "00:38", 20),
                    "closing_time": "00:30"
                },
                "H2TD": {
                    "peak": self.generate_schedule("06:10", "09:10", 4) + self.generate_schedule("16:10", "19:10", 4),
                    "off_peak": self.generate_schedule("09:10", "16:10", 9) + self.generate_schedule("19:10", "23:10", 9),
                    "late": self.generate_schedule("23:10", "00:40", 20),
                    "closing_time": "00:30"
                },
                "H1BT": {
                    "peak": self.generate_schedule("06:12", "09:12", 4) + self.generate_schedule("16:12", "19:12", 4),
                    "off_peak": self.generate_schedule("09:12", "16:12", 9) + self.generate_schedule("19:12", "23:12", 9),
                    "late": self.generate_schedule("23:12", "00:42", 20),
                    "weekend_night": self.generate_schedule("23:12", "02:00", 20),  # Extended for weekends
                    "closing_time": "02:00"  # Extended on weekends
                },
                "H2TT": {
                    "peak": self.generate_schedule("06:14", "09:14", 4) + self.generate_schedule("16:14", "19:14", 4),
                    "off_peak": self.generate_schedule("09:14", "16:14", 9) + self.generate_schedule("19:14", "23:14", 9),
                    "late": self.generate_schedule("23:14", "00:44", 20),
                    "weekend_night": self.generate_schedule("23:14", "02:00", 20),  # Extended for weekends
                    "closing_time": "02:00"  # Extended on weekends
                }
            },
            "Line 3": {
                "H3TB": {
                    "peak": self.generate_schedule("06:00", "09:00", 5) + self.generate_schedule("16:00", "19:00", 5),
                    "off_peak": self.generate_schedule("09:00", "16:00", 11) + self.generate_schedule("19:00", "23:00", 11),
                    "late": self.generate_schedule("23:00", "00:30", 25),
                    "early_morning": self.generate_schedule("04:00", "06:00", 3),
                    "closing_time": "00:30"
                },
                "H3TS": {
                    "peak": self.generate_schedule("06:02", "09:02", 5) + self.generate_schedule("16:02", "19:02", 5),
                    "off_peak": self.generate_schedule("09:02", "16:02", 11) + self.generate_schedule("19:02", "23:02", 11),
                    "late": self.generate_schedule("23:02", "00:32", 25),
                    "early_morning": self.generate_schedule("04:02", "06:02", 3),
                    "closing_time": "00:30"
                },
                "H3NT": {
                    "peak": self.generate_schedule("06:04", "09:04", 5) + self.generate_schedule("16:04", "19:04", 5),
                    "off_peak": self.generate_schedule("09:04", "16:04", 11) + self.generate_schedule("19:04", "23:04", 11),
                    "late": self.generate_schedule("23:04", "00:34", 25),
                    "early_morning": self.generate_schedule("04:04", "06:04", 3),
                    "closing_time": "00:30"
                },
                "H1BS": {
                    "peak": self.generate_schedule("06:06", "09:06", 5) + self.generate_schedule("16:06", "19:06", 5),
                    "off_peak": self.generate_schedule("09:06", "16:06", 11) + self.generate_schedule("19:06", "23:06", 11),
                    "late": self.generate_schedule("23:06", "00:36", 25),
                    "early_morning": self.generate_schedule("04:06", "06:06", 3),
                    "closing_time": "00:30"
                },
                "H3HB": {
                    "peak": self.generate_schedule("06:08", "09:08", 5) + self.generate_schedule("16:08", "19:08", 5),
                    "off_peak": self.generate_schedule("09:08", "16:08", 11) + self.generate_schedule("19:08", "23:08", 11),
                    "late": self.generate_schedule("23:08", "00:38", 25),
                    "early_morning": self.generate_schedule("04:08", "06:08", 3),
                    "closing_time": "00:30"
                },
                "H1TDU": {
                    "peak": self.generate_schedule("06:10", "09:10", 5) + self.generate_schedule("16:10", "19:10", 5),
                    "off_peak": self.generate_schedule("09:10", "16:10", 11) + self.generate_schedule("19:10", "23:10", 11),
                    "late": self.generate_schedule("23:10", "00:40", 25),
                    "early_morning": self.generate_schedule("04:10", "06:10", 3),
                    "closing_time": "00:30"
                },
                "H3HP": {
                    "peak": self.generate_schedule("06:12", "09:12", 5) + self.generate_schedule("16:12", "19:12", 5),
                    "off_peak": self.generate_schedule("09:12", "16:12", 11) + self.generate_schedule("19:12", "23:12", 11),
                    "early_morning": self.generate_schedule("04:12", "06:12", 3),
                    "closing_time": "00:30"
                }
            },
            "Line 4": {
                "H4TX": {  # Outer station
                    "peak": self.generate_schedule("06:00", "09:00", 6) + self.generate_schedule("16:00", "19:00", 6),
                    "off_peak": self.generate_schedule("09:00", "16:00", 11) + self.generate_schedule("19:00", "22:30", 11),
                    "closing_time": "22:30"
                },
                "H4NT": {  # Outer station
                    "peak": self.generate_schedule("06:02", "09:02", 6) + self.generate_schedule("16:02", "19:02", 6),
                    "off_peak": self.generate_schedule("09:02", "16:02", 11) + self.generate_schedule("19:02", "22:32", 11),
                    "closing_time": "22:30"
                },
                "H4AL": {  # Outer station
                    "peak": self.generate_schedule("06:04", "09:04", 6) + self.generate_schedule("16:04", "19:04", 6),
                    "off_peak": self.generate_schedule("09:04", "16:04", 11) + self.generate_schedule("19:04", "22:34", 11),
                    "closing_time": "22:30"
                },
                "H4AN": {  # Outer station
                    "peak": self.generate_schedule("06:06", "09:06", 6) + self.generate_schedule("16:06", "19:06", 6),
                    "off_peak": self.generate_schedule("09:06", "16:06", 11) + self.generate_schedule("19:06", "22:36", 11),
                    "closing_time": "22:30"
                },
                "H4NL": {  # Outer station
                    "peak": self.generate_schedule("06:08", "09:08", 6) + self.generate_schedule("16:08", "19:08", 6),
                    "off_peak": self.generate_schedule("09:08", "16:08", 11) + self.generate_schedule("19:08", "22:38", 11),
                    "closing_time": "22:30"
                },
                "H4GV": {
                    "peak": self.generate_schedule("06:10", "09:10", 6) + self.generate_schedule("16:10", "19:10", 6),
                    "off_peak": self.generate_schedule("09:10", "16:10", 11) + self.generate_schedule("19:10", "23:00", 11),
                    "closing_time": "23:00"
                },
                "H4GD": {
                    "peak": self.generate_schedule("06:12", "09:12", 6) + self.generate_schedule("16:12", "19:12", 6),
                    "off_peak": self.generate_schedule("09:12", "16:12", 11) + self.generate_schedule("19:12", "23:00", 11),
                    "closing_time": "23:00"
                },
                "H4PN": {
                    "peak": self.generate_schedule("06:14", "09:14", 6) + self.generate_schedule("16:14", "19:14", 6),
                    "off_peak": self.generate_schedule("09:14", "16:14", 11) + self.generate_schedule("19:14", "23:00", 11),
                    "closing_time": "23:00"
                },
                "H4SB": {
                    "peak": self.generate_schedule("06:16", "09:16", 6) + self.generate_schedule("16:16", "19:16", 6),
                    "off_peak": self.generate_schedule("09:16", "16:16", 11) + self.generate_schedule("19:16", "23:00", 11),
                    "closing_time": "23:00"
                },
                "H4D7": {
                    "peak": self.generate_schedule("06:18", "09:18", 6) + self.generate_schedule("16:18", "19:18", 6),
                    "off_peak": self.generate_schedule("09:18", "16:18", 11) + self.generate_schedule("19:18", "23:00", 11),
                    "closing_time": "23:00"
                },
                "H4NV": {
                    "peak": self.generate_schedule("06:20", "09:20", 6) + self.generate_schedule("16:20", "19:20", 6),
                    "off_peak": self.generate_schedule("09:20", "16:20", 11) + self.generate_schedule("19:20", "23:00", 11),
                    "closing_time": "23:00"
                }
            },
            "Line 5": {
                "H5CG": {
                    "peak": self.generate_schedule("06:00", "09:00", 7) + self.generate_schedule("16:00", "19:00", 7),
                    "off_peak": self.generate_schedule("09:00", "16:00", 13) + self.generate_schedule("19:00", "22:30", 13),
                    "early_morning": self.generate_schedule("04:00", "06:00", 3),
                    "closing_time": "22:30"
                },
                "H5BH": {
                    "peak": self.generate_schedule("06:02", "09:02", 7) + self.generate_schedule("16:02", "19:02", 7),
                    "off_peak": self.generate_schedule("09:02", "16:02", 13) + self.generate_schedule("19:02", "22:32", 13),
                    "early_morning": self.generate_schedule("04:02", "06:02", 3),
                    "closing_time": "22:30"
                },
                "H1BT": {
                    "peak": self.generate_schedule("06:04", "09:04", 7) + self.generate_schedule("16:04", "19:04", 7),
                    "off_peak": self.generate_schedule("09:04", "16:04", 13) + self.generate_schedule("19:04", "22:34", 13),
                    "early_morning": self.generate_schedule("04:04", "06:04", 3),
                    "closing_time": "22:30"
                },
                "H5TC": {
                    "peak": self.generate_schedule("06:06", "09:06", 7) + self.generate_schedule("16:06", "19:06", 7),
                    "off_peak": self.generate_schedule("09:06", "16:06", 13) + self.generate_schedule("19:06", "22:36", 13),
                    "early_morning": self.generate_schedule("04:06", "06:06", 3),
                    "closing_time": "22:30"
                },
                "H5SG": {
                    "peak": self.generate_schedule("06:08", "09:08", 7) + self.generate_schedule("16:08", "19:08", 7),
                    "off_peak": self.generate_schedule("09:08", "16:08", 13) + self.generate_schedule("19:08", "22:38", 13),
                    "early_morning": self.generate_schedule("04:08", "06:08", 3),
                    "closing_time": "22:30"
                },
                "H3TS": {
                    "peak": self.generate_schedule("06:10", "09:10", 7) + self.generate_schedule("16:10", "19:10", 7),
                    "off_peak": self.generate_schedule("09:10", "16:10", 13) + self.generate_schedule("19:10", "22:40", 13),
                    "early_morning": self.generate_schedule("04:10", "06:10", 3),
                    "closing_time": "22:30"
                },
                "H4D7": {
                    "peak": self.generate_schedule("06:12", "09:12", 7) + self.generate_schedule("16:12", "19:12", 7),
                    "off_peak": self.generate_schedule("09:12", "16:12", 13) + self.generate_schedule("19:12", "22:42", 13),
                    "early_morning": self.generate_schedule("04:12", "06:12", 3),
                    "closing_time": "22:30"
                },
                "H5TP": {
                    "peak": self.generate_schedule("06:14", "09:14", 7) + self.generate_schedule("16:14", "19:14", 7),
                    "off_peak": self.generate_schedule("09:14", "16:14", 13) + self.generate_schedule("19:14", "22:44", 13),
                    "early_morning": self.generate_schedule("04:14", "06:14", 3),
                    "closing_time": "22:30"
                }
            }
        }

        # Create the trips table
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id SERIAL PRIMARY KEY,
                    start_station VARCHAR(100),
                    end_station VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            cursor.close()
            release_db_connection(conn)

    def generate_schedule(self, start_time, end_time, interval_minutes):
        """Generate a timetable from start_time to end_time with given interval in minutes."""
        schedule = []
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        if end_time == "00:30":
            end = end.replace(day=end.day + 1)
        if end_time == "02:00":
            end = end.replace(day=end.day + 1)
        current = start
        while current <= end:
            schedule.append(current.strftime("%H:%M"))
            current += timedelta(minutes=interval_minutes)
        return schedule

    def add_trip(self, trip):
        """Add a trip to the database and route tree."""
        start_station, end_station = trip.split(" to ")
        start_id = self.station_map.get(start_station, "Unknown")
        end_id = self.station_map.get(end_station, "Unknown")

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trips (start_station, end_station) VALUES (%s, %s)",
                (start_id, end_id)
            )
            conn.commit()
        finally:
            cursor.close()
            release_db_connection(conn)

        if not self.route_tree:
            self.route_tree = Node(start_id)
        self._add_to_tree(self.route_tree, end_id)

    def _add_to_tree(self, node, stop):
        if stop < node.stop:
            if node.left is None:
                node.left = Node(stop)
            else:
                self._add_to_tree(node.left, stop)
        else:
            if node.right is None:
                node.right = Node(stop)
            else:
                self._add_to_tree(node.right, stop)

    def print_route_tree(self):
        self._print_tree(self.route_tree)

    def _print_tree(self, node):
        if node:
            self._print_tree(node.left)
            print(node.stop)
            self._print_tree(node.right)

    def get_trips(self):
        """Fetch all trips from the database."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT start_station, end_station FROM trips")
            trips = cursor.fetchall()
            return [f"{start} to {end}" for start, end in trips]
        finally:
            cursor.close()
            release_db_connection(conn)

    def get_station_id(self, station):
        return self.station_map.get(station, "Unknown")

    def find_path(self, start, end):
        visited = set()
        queue = deque([(start, [start])])
        while queue:
            station, path = queue.popleft()
            if station == end:
                return path
            if station not in visited:
                visited.add(station)
                for next_station in self.station_graph.get(station, []):
                    queue.append((next_station, path + [next_station]))
        return None

    def longest_route_no_repeats(self):
        longest_path = []
        for start in self.station_graph:
            for end in self.station_graph:
                path = self.find_path(start, end)
                if path and len(path) > len(longest_path):
                    seen = set()
                    repeat = False
                    for station in path:
                        if station in seen:
                            repeat = True
                            break
                        seen.add(station)
                    if not repeat:
                        longest_path = path
        return longest_path

    def get_timetable(self, line, station, current_time=None):
        if current_time is None:
            current_time = datetime.now()

        current_time_str = current_time.strftime("%H:%M")
        current_hour = int(current_time_str.split(":")[0])
        current_minute = int(current_time_str.split(":")[1])
        day_of_week = current_time.weekday()  # 0 = Monday, 4 = Friday, 5 = Saturday

        station_id = self.station_map.get(station, "Unknown")
        if line not in self.timetable or station_id not in self.timetable[line]:
            return []

        timetable_data = self.timetable[line][station_id]
        closing_time = timetable_data["closing_time"]

        # Check if the station is closed
        closing_hour, closing_minute = map(int, closing_time.split(":"))
        if closing_time == "02:00" and (day_of_week == 4 or day_of_week == 5):  # Friday or Saturday
            if current_hour > 2 or (current_hour == 2 and current_minute > 0):
                return ["Station closed!"]
        else:
            if (current_hour > closing_hour) or (current_hour == closing_hour and current_minute > closing_minute):
                return ["Station closed!"]

        # Special case: Airport route (Lines 3 & 5) from 4:00 AM to 6:00 AM
        if line in ["Line 3", "Line 5"] and station_id in ["H3TS", "H5SG"] and 4 <= current_hour < 6:
            return timetable_data.get("early_morning", [])

        # Special case: Weekend nightlife on Line 2 (Ben Thanh ↔ Thu Thiem)
        if line == "Line 2" and station_id in ["H1BT", "H2TT"] and (day_of_week == 4 or day_of_week == 5) and (current_hour >= 23 or current_hour < 2):
            return timetable_data.get("weekend_night", timetable_data["late"])

        # Express service on Line 1 during peak hours
        if line == "Line 1" and station_id in ["H1BT", "H1BS", "H1TD", "H1ST", "H1TDU"] and ((6 <= current_hour < 9) or (16 <= current_hour < 19)):
            return timetable_data.get("express", timetable_data["peak"])

        # Regular timetable selection
        if (6 <= current_hour < 9) or (16 <= current_hour < 19):
            return timetable_data["peak"]
        elif (9 <= current_hour < 16) or (19 <= current_hour < 23):
            return timetable_data["off_peak"]
        elif 23 <= current_hour or current_hour < 2:
            return timetable_data.get("late", [])
        else:
            return []