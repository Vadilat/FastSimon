import unittest
from main import app  # Import your Flask app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Setup a test client before each test
        self.client = app.test_client()

    def test_set_and_get(self):
        # Test setting and getting a variable
        response = self.client.get('/set?name=testvar&value=42')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testvar = 42', response.data)

        response = self.client.get('/get?name=testvar')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'42')

    def test_unset(self):
        # Test unsetting a variable and then retrieving it
        self.client.get('/set?name=toDelete&value=deleteMe')
        response = self.client.get('/unset?name=toDelete')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'toDelete = None', response.data)

        response = self.client.get('/get?name=toDelete')
        self.assertEqual(response.data, b'None')

    def test_numequalto(self):
        # Test numequalto counting values
        self.client.get('/set?name=a&value=10')
        self.client.get('/set?name=b&value=10')
        response = self.client.get('/numequalto?value=10')
        self.assertEqual(response.data, b'2')

    def test_undo_redo(self):
        # Test undo/redo functionality for SET and UNSET
        self.client.get('/set?name=x&value=100')
        self.client.get('/unset?name=x')

        undo_resp = self.client.get('/undo')
        self.assertIn(b'x = 100', undo_resp.data)

        redo_resp = self.client.get('/redo')
        self.assertIn(b'x = None', redo_resp.data)

    def test_undo_when_empty(self):
        # Test undo when nothing to undo
        self.client.get('/end')
        response = self.client.get('/undo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'NO COMMANDS')

    def test_redo_after_new_set(self):
        # Test that redo is blocked after new SET command
        self.client.get('/set?name=z&value=1')
        self.client.get('/undo')
        self.client.get('/set?name=z&value=999')  # This should clear the redo stack
        response = self.client.get('/redo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'NO COMMANDS')

    def tearDown(self):
        # Clean up the datastore after each test
        self.client.get('/end')

if __name__ == '__main__':
    unittest.main()
