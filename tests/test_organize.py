import unittest
from pymongo import MongoClient
from flask import json
from app import app, events_collection  # Adjust the import based on your app structure
from bson import ObjectId  # Import ObjectId for MongoDB ID handling


def setup_test_db():
    # Connect to the main database
    client = MongoClient('mongodb://localhost:27017/')
    event_db = client['eventdb']  # Main database
    test_db = client['testdb']  # Test database

    # Drop test database if it already exists
    client.drop_database('testdb')  # Correctly drop the test database

    # Copy collections from eventdb to testdb
    for collection_name in event_db.list_collection_names():
        event_collection = event_db[collection_name]
        documents = list(event_collection.find({}))
        if documents:  # Only insert if there are documents to insert
            test_collection = test_db[collection_name]
            test_collection.insert_many(documents)

    print("Test database setup complete.")


class EventOrganizerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Configure the test database and set up the Flask test client
        setup_test_db()  # Ensure the test database is set up
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def setUp(self):
        # Clear the test database before each test
        events_collection.delete_many({})

    def tearDown(self):
        # Clear the test database after each test
        events_collection.delete_many({})

    @classmethod
    def tearDownClass(cls):
        # Drop the test database after all tests have completed
        client = MongoClient('mongodb://localhost:27017/')
        client.drop_database('testdb')  # Make sure to drop the correct test database

    def test_create_event_with_field_check(self):
        # Define test data
        test_data = {
            "name": "Ras Graba",
            "description": "Dandiya",
            "eventLocation": "BKC",
            "dateFrom": "2024-11-05",
            "dateTo": "2024-11-09", #if missed then test cass fail
            "price": '', #if data not enter
            "category": "Dance",
            "created_by": "ok@example.com"
        }

        # Check if all required fields are present
        required_fields = ["name", "description", "eventLocation", "dateFrom", "dateTo", "price", "category",
                           "created_by"]

        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in test_data or not test_data[field]]

        if missing_fields:
            self.fail(f"Missing fields: {', '.join(missing_fields)}")  # Fail the test if any fields are missing
        else:
            print("All fields present. Proceeding to submit event data.")

            # Make a POST request to create an event
            response = self.client.post('/event', data=json.dumps(test_data), content_type='application/json')

            # Check the response
            print(response.data)  # Print response data for debugging
            self.assertEqual(response.status_code, 201)

            response_data = json.loads(response.data)
            self.assertIn("message", response_data)
            self.assertEqual(response_data["message"], "Event created")
            self.assertIn("id", response_data)

            # Verify that the event was added to the database
            event_in_db = events_collection.find_one({"_id": ObjectId(response_data["id"])})  # Convert ID to ObjectId
            self.assertIsNotNone(event_in_db)


if __name__ == '__main__':
    unittest.main()
