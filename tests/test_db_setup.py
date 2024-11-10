# tests/test_db_setup.py
from pymongo import MongoClient

def setup_test_db():
    # Connect to the main database
    client = MongoClient('mongodb://localhost:27017/')
    event_db = client['eventdb']  # Main database
    test_db = client['testdb']     # Test database

    # Drop test database if it already exists
    client.drop_database('testdb')  # Correctly drop the test database using the client

    # Copy collections from eventdb to testdb
    for collection_name in event_db.list_collection_names():
        event_collection = event_db[collection_name]
        documents = list(event_collection.find({}))
        if documents:  # Only insert if there are documents to insert
            test_collection = test_db[collection_name]
            test_collection.insert_many(documents)

    print("Test database setup complete.")
