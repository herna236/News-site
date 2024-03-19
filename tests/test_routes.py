import unittest
from app import app, db

class TestApp(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        
        # Creating application context
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_homepage(self):
        """Test homepage route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        

    def test_signup_page(self):
        """Test signup page route."""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        

    def test_login_page(self):
        """Test login page route."""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
       

    def test_user_favorites_page(self):
        """Test user favorites page route."""
        response = self.app.get('/user/1/favorites')
        self.assertEqual(response.status_code, 200)
        

if __name__ == '__main__':
    unittest.main()

