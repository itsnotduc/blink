import unittest
from datetime import datetime, timedelta
from trip_manager import TripManager
from db import create_session

class TestTripManager(unittest.TestCase):

    def setUp(self):
        self.trip_manager = TripManager()
        self.session_token = create_session(role="user")
        print("Available stations:", self.trip_manager.station_map_inv.keys())

    def test_get_schedules_valid_line_and_station(self):
        """Test retrieving schedules for a valid line and station."""
        line_name = "Line 1"  # Replace with a valid line name
        station_name = "Ben Thanh"  # Replace with a valid station name

        print("Validating station exists:", station_name)  # DEBUG
        if station_name not in self.trip_manager.station_map_inv:  # Check key on station_map_inv
            print("Available stations:", self.trip_manager.station_map_inv.keys())  # Debug
            self.fail(f"ERROR: Station '{station_name}' not found in self.trip_manager.station_map_inv. Check your database data and TripManager initialization. Valid keys are listed above.")

        schedule = self.trip_manager.get_schedules(self.session_token, line_name, station_name)
        self.assertIsNotNone(schedule, "Schedule should not be None")
        self.assertIsInstance(schedule, dict, "Schedule should be a dictionary")
        if "schedules" in schedule:
            self.assertIsInstance(schedule["schedules"], list, "Schedules should be a list")
            self.assertTrue(len(schedule["schedules"]) > 0, "Schedules list should not be empty")

            # Print the schedule for inspection
            print(f"Schedule for {station_name} on {line_name}:")
            for item in schedule["schedules"]:
                print(item)
        else:
            self.fail("Should not reach here, if no schedules, an exception is expected")

    def test_get_schedules_invalid_line(self):
        """Test retrieving schedules for an invalid line."""
        line_name = "InvalidLine"
        station_name = "Ben Thanh"

        with self.assertRaises(Exception) as context:
            self.trip_manager.get_schedules(self.session_token, line_name, station_name)
        self.assertIn(f"Error retrieving schedules: ", str(context.exception))

    def test_get_schedules_invalid_station(self):
        """Test retrieving schedules for an invalid station."""
        line_name = "Line 1"
        station_name = "InvalidStation"

        with self.assertRaises(Exception) as context:
            self.trip_manager.get_schedules(self.session_token, line_name, station_name)
        self.assertIn(f"Error retrieving schedules: ", str(context.exception))

if __name__ == '__main__':
    unittest.main()
