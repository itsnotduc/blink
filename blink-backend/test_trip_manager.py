import unittest
from datetime import datetime
from trip_manager import TripManager
from db import create_session
import psycopg2

class TestTripManager(unittest.TestCase):

    def setUp(self):
        self.trip_manager = TripManager()
        self.session_token = create_session(role="user")
        # Mock database connection for testing (replace with actual test DB setup)
        self.conn = psycopg2.connect(dbname="blink", user="postgres", password="minhduc456", host="localhost")
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.cursor.close()
        self.conn.close()

    # Test Case 1: Finding a Path
    def test_find_shortest_path(self):
        start_station = "Mien Dong"
        end_station = "Ben Thanh"
        path, distance = self.trip_manager.find_shortest_path(start_station, end_station)
        self.assertIsNotNone(path, "Path should exist between Mien Dong and Ben Thanh")
        self.assertTrue(len(path) > 0, "Path should contain at least one station")
        self.assertIn("Ben Thanh", path, "End station should be in path")
        self.assertIn("Mien Dong", path, "Start station should be in path")
        print(f"Shortest path: {path}, Distance: {distance} minutes")

    def test_find_shortest_path_invalid_stations(self):
        path, distance = self.trip_manager.find_shortest_path("InvalidStart", "InvalidEnd")
        self.assertIsNone(path, "Path should be None for invalid stations")
        self.assertEqual(distance, 0, "Distance should be 0 for invalid path")

    # Test Case 2: Adding Trips
    # In test_trip_manager.py
    def test_add_trip(self):
        trip_desc = ["Test trip from Mien Dong to Ben Thanh"]  # Wrap in a list to match TEXT[] type
        user_id = 1  # Assume a test user exists
        start_station = "Mien Dong"
        end_station = "Ben Thanh"
        start_time = datetime.now()
        response = self.trip_manager.add_trip(trip_desc, self.session_token, user_id, start_station, end_station, start_time)
        self.assertEqual(response["message"], f"Trip {response['trip_id']} added successfully")
        self.cursor.execute("SELECT description FROM trips WHERE trip_id = %s", (response["trip_id"],))
        result = self.cursor.fetchone()
        self.assertEqual(result[0][0], trip_desc[0], "Trip description should match")  # Access first element of array
    def test_add_trip_invalid_session(self):
        invalid_token = "invalid_token"
        with self.assertRaises(Exception) as context:
            self.trip_manager.add_trip("Invalid trip", invalid_token)
        self.assertTrue("Invalid or expired session token" in str(context.exception))

    # Test Case 3: Adding a New User
    def test_add_new_user(self):
        # Assume a function to add a user (not in TripManager, so we'll mock DB interaction)
        username = "testuser"
        email = "testuser@example.com"
        password_hash = "$2b$12$test_hash"  # Mocked hash for testing
        self.cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s) RETURNING user_id
        """, (username, email, password_hash, "user"))
        user_id = self.cursor.fetchone()[0]
        self.conn.commit()
        self.assertIsNotNone(user_id, "User should be added successfully")
        self.cursor.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
        result = self.cursor.fetchone()
        self.assertEqual(result[0], username, "Username should match")

    def test_add_existing_user(self):
        username = "admin"
        email = "admin@example.com"
        password_hash = "$2b$12$test_hash"
        with self.assertRaises(psycopg2.IntegrityError):
            self.cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, (username, email, password_hash, "user"))
            self.conn.commit()



    def test_get_schedules_invalid_line(self):
        with self.assertRaises(Exception) as context:
            self.trip_manager.get_schedules(self.session_token, "InvalidLine", "Mien Dong")
        self.assertTrue("Station Mien Dong not found" in str(context.exception))

if __name__ == '__main__':
    unittest.main()