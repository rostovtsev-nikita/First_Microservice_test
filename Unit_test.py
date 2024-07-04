import unittest
import json
from app import app

class AnalyzeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_analyze(self):
        response = self.app.post('/analyze',
                                 data=json.dumps({'url': 'http://example.com', 'phrase': 'example'}),
                                 content_type='application/json',
                                 headers={'Authorization': 'valid_token'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data())
        self.assertIn('found', data)
        self.assertIn('levenshtein_distance', data)

if __name__ == '__main__':
    unittest.main()
