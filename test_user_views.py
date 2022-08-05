from app import app, CURR_USER_KEY
import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):

    def setUp(self):

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 123
        self.testuser.id = self.testuser_id

        self.user1 = User.signup(
            "testuser1", "test1@test.com", "password", None)
        self.user1_id = 456
        self.user1.id = self.user1_id
        self.user2 = User.signup(
            "testuser2", "test2@test.com", "password", None)
        self.user2_id = 789
        self.user2.id = self.user2_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_list(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=testuser1")

            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@testuser", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))

    def test_user_details(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))

    def set_follows(self):
        follow1 = Follows(user_being_followed_id=self.user1_id,
                          user_following_id=self.testuser_id)
        follow2 = Follows(user_being_followed_id=self.user2_id,
                          user_following_id=self.testuser_id)
        follow3 = Follows(user_being_followed_id=self.testuser_id,
                          user_following_id=self.user1_id)

        db.session.add_all([follow1, follow2, follow3])
        db.session.commit()

    def test_show_follows(self):
        self.set_follows()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 3)
            self.assertIn("0", found[0].text)
            self.assertIn("2", found[1].text)
            self.assertIn("1", found[2].text)

    def test_show_following(self):
        self.set_follows()
        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))

    def test_invalid_following(self):
        self.set_follows()
        with self.client as c:
            resp = c.get(
                f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_show_followers(self):
        self.set_follows()
        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))

    def test_invalid_followers(self):
        self.set_follows()
        with self.client as c:
            resp = c.get(
                f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
