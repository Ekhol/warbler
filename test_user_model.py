"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup("TestMcTester", "test@test.com", "password", None)
        user_id1 = 1
        user1.id = user_id1

        user2 = User.signup("TestMcTesterSon",
                            "test2@test.com", "password", None)
        user_id2 = 2
        user2.id = user_id2

        db.session.commit()

        user1 = User.query.get(user_id1)
        user2 = User.query.get(user_id2)

        self.user1 = user1
        self.user2 = user2

        self.user_id1 = user_id1
        self.user_id2 = user_id2

        self.client = app.test_client()

    def tearDown(self):
        result = super().tearDown()
        db.session.rollback()
        return result

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_signup(self):
        user = User.signup("TestMcTester2", "test3@test.com", "password", None)
        user_id = 30
        user.id = user_id
        db.session.commit()

        user = User.query.get(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "TestMcTester2")
        self.assertEqual(user.email, "test3@test.com")
        self.assertNotEqual(user.password, "password")

    def test_authenticate(self):
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_id1)

    def test_bad_username(self):
        self.assertFalse(User.authenticate("blahblah", "password"))

    def test_bad_password(self):
        self.assertFalse(User.authenticate(self.user_1.username, "incorrect"))
