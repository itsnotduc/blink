import unittest
from unittest.mock import patch
from datetime import datetime
from trip_manager import TripManager  # Assuming TripManager is defined in trip_manager.py

class TestTripManager(unittest.TestCase):
    def setUp(self):
        """Initialize a fresh TripManager instance before each test."""
        self.tm = TripManager()

    # Pathfinding Tests
    def test_find_shortest_path_direct(self):
        """Test shortest path between two stations on the same line."""
        path, time = self.tm.find_shortest_path("Ben Thanh", "Opera House")
        self.assertEqual(path, ["Ben Thanh", "Opera House"])
        self.assertEqual(time, 3)  # Assuming 3 minutes per segment

    def test_find_shortest_path_multi_transfer(self):
        """Test shortest path requiring multiple transfers."""
        path, time = self.tm.find_shortest_path("Tan Binh", "Van Thanh")
        expected_path = [
            "Tan Binh", "Pham Van Bach", "Ba Queo", "Nguyen Hong Dao", "Bay Hien",
            "Pham Van Hai", "Le Thi Rieng Park", "Hoa Hung", "Dan Chu", "Tao Dan",
            "Ben Thanh", "Ben Thanh", "Opera House", "Ba Son", "Van Thanh"
        ]
        self.assertEqual(path, expected_path)
        expected_time = 44  # 14 segments × 3 min + 1 transfer × 5 min
        self.assertEqual(time, expected_time)

    def test_find_fastest_path_off_peak(self):
        """Test fastest path during off-peak hours with longer frequency."""
        start_time = datetime(2023, 1, 1, 14, 1)  # Off-peak, just after 14:00
        path, time = self.tm.find_fastest_path("Ben Thanh", "Opera House", start_time)
        self.assertEqual(path, ["Ben Thanh", "Opera House"])
        self.assertEqual(time, 17)  # 14 (wait until 14:15) + 3 (travel)

    def test_find_fastest_path_closed(self):
        """Test fastest path when stations are closed."""
        start_time = datetime(2023, 1, 1, 1, 0)  # Before opening (e.g., 6 AM)
        path, time = self.tm.find_fastest_path("Ben Thanh", "Opera House", start_time)
        self.assertIsNone(path)
        self.assertEqual(time, 0)

    # Timetable Tests
    def test_get_timetable_peak_hours(self):
        """Test timetable generation during peak hours."""
        current_time = datetime(2023, 1, 1, 8, 0)  # Peak time
        timetable = self.tm.get_timetable("Line 1", "Ben Thanh", current_time)
        expected = ["08:00", "08:10", "08:20", "08:30", "08:40", "08:50"]  # 10-min frequency
        self.assertEqual(timetable[:6], expected)  # Check first 6 entries

    def test_get_timetable_off_peak(self):
        """Test timetable generation during off-peak hours."""
        current_time = datetime(2023, 1, 1, 13, 0)  # Off-peak time
        timetable = self.tm.get_timetable("Line 1", "Ben Thanh", current_time)
        expected = ["13:00", "13:15", "13:30", "13:45"]  # 15-min frequency
        self.assertEqual(timetable[:4], expected)  # Check first 4 entries

    def test_get_timetable_closed(self):
        """Test timetable when the station is closed."""
        current_time = datetime(2023, 1, 1, 2, 0)  # Closed time (e.g., after midnight)
        timetable = self.tm.get_timetable("Line 1", "Ben Thanh", current_time)
        self.assertEqual(timetable, ["Station closed!"])

    def test_get_next_departure_near_time(self):
        """Test next departure when current time is close to a scheduled departure."""
        current_time = datetime(2023, 1, 1, 8, 8)  # Peak time, before 8:10
        next_dep = self.tm.get_next_departure("Line 1", "Ben Thanh", current_time)
        self.assertEqual(next_dep, datetime(2023, 1, 1, 8, 10))

    def test_get_next_departure_post_time(self):
        """Test next departure after a scheduled departure has passed."""
        current_time = datetime(2023, 1, 1, 8, 12)  # Peak time, after 8:10
        next_dep = self.tm.get_next_departure("Line 1", "Ben Thanh", current_time)
        self.assertEqual(next_dep, datetime(2023, 1, 1, 8, 20))

    # Trip Management Tests
    @patch('trip_manager.get_db_connection')
    @patch('trip_manager.release_db_connection')
    def test_trip_management(self, mock_release, mock_get_conn):
        """Test adding a trip and retrieving it from the database."""
        mock_conn = mock_get_conn.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [("Trip to Opera",), ("Trip to Ben Thanh",)]
        
        self.tm.add_trip("Trip to Opera", "user123")
        trips = self.tm.get_trips("user123")
        self.assertIn("Trip to Opera", trips)

    # Edge Case Tests
    def test_find_shortest_path_invalid_input(self):
        """Test shortest path with an invalid station name."""
        path, time = self.tm.find_shortest_path("Nonexistent", "Ben Thanh")
        self.assertIsNone(path)
        self.assertEqual(time, 0)

    def test_find_shortest_path_disconnected(self):
        """Test shortest path between stations with no possible route."""
        # Assuming "District 9" and "Binh Chanh" have no connecting lines
        path, time = self.tm.find_shortest_path("District 9", "Binh Chanh")
        self.assertIsNone(path)  # No path exists
        self.assertEqual(time, 0)

if __name__ == '__main__':
    unittest.main()