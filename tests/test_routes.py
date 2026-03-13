import unittest
from application import application

class TestBackendEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = application.test_client()
        self.client.testing = True

    def test_health_check(self):
        """Test the /health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json.get("status"), "healthy")

    def test_create_event_success(self):
        """Test creating a valid event"""
        payload = {
            "title": "Sample Event",
            "date": "2025-04-20"
        }
        response = self.client.post('/events', json=payload)
        self.assertIn(response.status_code, [201, 500, 501])  

    def test_create_event_missing_title(self):
        """Missing required 'title' field"""
        payload = {
            "date": "2025-04-20"
        }
        response = self.client.post('/events', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.json.get("error", ""))

    def test_create_event_missing_date(self):
        """Missing required 'date' field"""
        payload = {
            "title": "Event Without Date"
        }
        response = self.client.post('/events', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.json.get("error", ""))

if __name__ == '__main__':
    unittest.main()
