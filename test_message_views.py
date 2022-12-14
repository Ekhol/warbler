"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 123
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_not_session(self):
        with self.client as c:
            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_view(self):
        message = Message(id=123, text="testing", user_id=self.testuser_id)

        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.testuser.id

            mess = Message.query.get(123)

            resp = c.get(f'/messages/{mess.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(mess.text, str(resp.data))

    def test_message_invalid_view(self):
        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/122345')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        message = Message(id=123, text="testing", user_id=self.testuser_id)

        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/123/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            mess = Message.query.get(123)
            self.assertIsNone(mess)

    def test_invalid_delete(self):
        invalidUser = User.signup(
            username="invalid", email="testing@test.com", password="password", image_url=None)
        invalidUser.id = 420

        message = Message(id=123, text="testing", user_id=self.testuser_id)

        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = 420

            resp = c.post("/messages/123/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            mess = Message.query.get(123)
            self.assertIsNotNone(mess)
