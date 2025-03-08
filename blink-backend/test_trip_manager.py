import unittest
from datetime import datetime
from db import create_session, get_db_connection, release_db_connection
from trip_manager import TripManager

class TestTripManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trip_manager = TripManager()
        cls.admin_session = create_session(role="admin")
        cls.user_session = create_session(role="user")

    def setUp(self):
        conn = get_db_connection(self.admin_session)
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE trips RESTART IDENTITY")
        conn.commit()
        cursor.close()
        release_db_connection(conn)
        self.trip_manager.route_tree = None

    def test_add_trip_success(self):
        trip = "Mien Dong to Saigon Hi-tech Park"
        self.trip_manager.add_trip(trip, self.admin_session)
        trips = self.trip_manager.get_trips(self.admin_session)
        self.assertIn(trip, trips)

    def test_add_trip_invalid_station(self):
        trip = "Ben Thanh to District 9"
        self.trip_manager.add_trip(trip, self.admin_session)
        trips = self.trip_manager.get_trips(self.admin_session)
        self.assertIn(trip, trips)

    def test_get_trips_multiple(self):
        trips_to_add = ["Cu Chi to An Suong", "Tan Kien to Phu Lam", "Thanh Xuan to Go Vap"]
        for trip in trips_to_add:
            self.trip_manager.add_trip(trip, self.admin_session)
        retrieved_trips = self.trip_manager.get_trips(self.admin_session)
        self.assertEqual(len(retrieved_trips), 3)
        for trip in trips_to_add:
            self.assertIn(trip, retrieved_trips)

    def test_get_trips_empty(self):
        trips = self.trip_manager.get_trips(self.admin_session)
        self.assertEqual(len(trips), 0)

    def test_get_station_id_known(self):
        station_id = self.trip_manager.get_station_id("Ben Thanh")
        self.assertEqual(station_id, "S114BT")

    def test_get_station_id_unknown(self):
        station_id = self.trip_manager.get_station_id("District 9")
        self.assertEqual(station_id, "Unknown")

    def test_find_path_direct(self):
        start = "S101MD"  # Mien Dong
        end = "S104TD"    # Thu Duc
        path = self.trip_manager.find_path(start, end)
        self.assertIsInstance(path, list)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], end)
        self.assertEqual(len(path), 4)  # Mien Dong -> Suoi Tien -> Saigon Hi-tech -> Thu Duc

    def test_find_path_with_transfer(self):
        start = "S114BT"  # Ben Thanh
        end = "S219TT"    # Thu Thiem
        path = self.trip_manager.find_path(start, end)
        print(f"Path from S114BT to S219TT: {path}")  # Debug print
        self.assertIsInstance(path, list)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], end)
        self.assertIn("S214HN", path)  # Should go via Ham Nghi on Line 2

    def test_find_path_no_path(self):
        start = "S101MD"  # Mien Dong
        end = "S999XX"    # Non-existent station
        path = self.trip_manager.find_path(start, end)
        self.assertIsNone(path)

    def test_longest_route_no_repeats(self):
        longest_route = self.trip_manager.longest_route_no_repeats()
        self.assertIsInstance(longest_route, list)
        self.assertGreater(len(longest_route), 10)
        self.assertEqual(len(longest_route), len(set(longest_route)))

    def test_get_timetable_peak(self):
        current_time = datetime.strptime("2023-10-10 08:00:00", "%Y-%m-%d %H:%M:%S")
        timetable = self.trip_manager.get_timetable("Line 1", "Thu Duc", current_time)
        self.assertIsInstance(timetable, list)
        self.assertGreater(len(timetable), 0)
        self.assertNotEqual(timetable, ["Station closed!"])
        self.assertEqual(timetable[1], "08:10")

    def test_get_timetable_off_peak(self):
        current_time = datetime.strptime("2023-10-10 10:00:00", "%Y-%m-%d %H:%M:%S")
        timetable = self.trip_manager.get_timetable("Line 2", "Bay Hien", current_time)
        self.assertIsInstance(timetable, list)
        self.assertGreater(len(timetable), 0)
        self.assertNotEqual(timetable, ["Station closed!"])
        self.assertEqual(timetable[1], "10:15")

    def test_get_timetable_closed(self):
        current_time = datetime.strptime("2023-10-10 03:00:00", "%Y-%m-%d %H:%M:%S")
        timetable = self.trip_manager.get_timetable("Line 3A", "Phu Lam", current_time)
        self.assertEqual(timetable, ["Station closed!"])

    def test_get_timetable_invalid_line(self):
        current_time = datetime.strptime("2023-10-10 08:00:00", "%Y-%m-%d %H:%M:%S")
        timetable = self.trip_manager.get_timetable("Line X", "Ben Thanh", current_time)
        self.assertEqual(timetable, [])

    def test_find_fastest_path(self):
        start_time = datetime.strptime("2023-10-10 08:00:00", "%Y-%m-%d %H:%M:%S")
        result = self.trip_manager.find_fastest_path("Ben Thanh", "Ham Nghi", start_time)
        print(f"Fastest path result: {result}")
        self.assertIsNotNone(result)
        path, total_time = result
        self.assertIsInstance(path, list)
        self.assertEqual(path[0], "Ben Thanh")
        self.assertEqual(path[-1], "Ham Nghi")
        self.assertGreater(total_time, 0)

    def test_find_fastest_path_no_path(self):
        start_time = datetime.strptime("2023-10-10 08:00:00", "%Y-%m-%d %H:%M:%S")
        result = self.trip_manager.find_fastest_path("Ben Thanh", "District 9", start_time)
        self.assertIsNone(result)

    def test_find_fastest_path_closed(self):
        start_time = datetime.strptime("2023-10-10 03:00:00", "%Y-%m-%d %H:%M:%S")
        result = self.trip_manager.find_fastest_path("Tan Kien", "Cho Lon", start_time)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()