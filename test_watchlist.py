import unittest

from watchlist import app, db
from watchlist.modules import User, Movie
from watchlist.commands import forge, initdb


class WatchlistTestCase(unittest.TestCase):

    def setUp(self):
        # Update configurations
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        # Create database table
        db.create_all()
        # Create test data
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie', year='2023')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()  # Create test client
        self.runner = app.test_cli_runner()  # Create test command runner

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_app_exist(self):
        """
        Test whether the app exists.
        """
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        """
        Test whether the app is in testing mode.
        """
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        """
        Test the 404 not found page of app.
        """
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        """
        Test the main page (index page) of app.
        """
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie', data)
        self.assertEqual(response.status_code, 200)

    def login(self):
        """
        Helping method, used to let client login.
        """
        self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)

    def test_create_item(self):
        """
        Test the creation of new item in index page.
        """
        self.login()

        # Create new item
        response = self.client.post('/', data=dict(
            title='New Movie',
            year='2023'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)

        # Try to create invalid item, with empty title
        response = self.client.post('/', data=dict(
            title='',
            year='2023'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid input.', data)
        self.assertNotIn('Item created.', data)

        # Try to create invalid item, with empty year
        response = self.client.post('/', data=dict(
            title='New Movie',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid input.', data)
        self.assertNotIn('Item created.', data)

    def test_edit_item(self):
        """
        Test the edition of existed item.
        """
        self.login()

        # Test the edit page
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('Test Movie', data)
        self.assertIn('2023', data)

        # Test the edit operation
        response = self.client.post('/movie/edit/1', data=dict(
            title='Edited Movie',
            year='2023'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated', data)
        self.assertIn('Edited Movie', data)

        # Test update with empty title
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2023'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated', data)
        self.assertIn('Invalid input.', data)

        # Test update with empty year
        response = self.client.post('/movie/edit/1', data=dict(
            title='Edited Again Movie',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated', data)
        self.assertNotIn('Edited Again Movie', data)
        self.assertIn('Invalid input.', data)

    def test_delete_item(self):
        """
        Test the deletion of item.
        """
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie', data)

    def test_login_protection(self):
        """
        Test whether login_required works properly.
        """
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)

    def test_login(self):
        """
        Test login.
        """
        # Login with right username-password pair.
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        # Login with wrong password.
        response = self.client.post('/login', data=dict(
            username='test',
            password='456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # Login with wrong username.
        response = self.client.post('/login', data=dict(
            username='wrong',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # Login with empty password.
        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # Login with empty username.
        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

    def test_logout(self):
        """
        Test logout works properly.
        """
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)

    def test_settings(self):
        """
        Test settings work properly (change user's name).
        """
        self.login()

        # Test setting page.
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        # Test updating user's name.
        response = self.client.post('/settings', data=dict(
            name='Parzivaal',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Parzivaal', data)

        # Test updating with empty word.
        response = self.client.post('/settings', data=dict(
            name='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)

    def test_forge_command(self):
        """
        Test command 'forge' works properly.
        """
        result = self.runner.invoke(forge)
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)
        self.assertNotEqual(Movie.query.count(), 1)

    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'max', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'max')
        self.assertTrue(User.query.first().validate_password('123'))

    def test_admin_command_update(self):
        result = self.runner.invoke(args=['admin', '--username', 'parzivaal', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'parzivaal')
        self.assertTrue(User.query.first().validate_password('456'))

if __name__ == '__main__':
    unittest.main()
