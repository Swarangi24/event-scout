import unittest
from app import app  # Adjust the import based on your app structure

class TestBrowseModule(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_fetch_events_empty_event_name(self):
        response = self.app.get('/browse.html?event=')  # Check for empty event name
        self.assertEqual(response.status_code, 200)

    def test_fetch_events_with_numbers(self):
        response = self.app.get('/browse.html?event=12345')  # Check for numeric event name
        self.assertEqual(response.status_code, 200)

    def test_fetch_events_with_special_characters(self):
        response = self.app.get('/browse.html?event=!@#$%^&*()')  # Check for special characters
        self.assertEqual(response.status_code, 200)

    def test_fetch_events_with_valid_name(self):
        response = self.app.get('/browse.html?event=concert')  # Check for a valid event name
        self.assertEqual(response.status_code, 200)

    def test_fetch_events_with_long_name(self):
        long_event_name = 'a' * 100  # Very long event name
        response = self.app.get(f'/browse.html?event={long_event_name}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No events found', response.data)  # Assuming no event matches this

    def test_fetch_events_with_whitespace(self):
        response = self.app.get('/browse.html?event=   ')  # Check for whitespace
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No events found', response.data)  # Assuming you handle whitespace


if __name__ == '__main__':
    unittest.main()
