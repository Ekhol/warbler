from cgitb import text
from app import app
import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
#
#
db.create_all()


class UserModelTestCase(TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.user_id = 1
        user = User.signup("TestMcTester", "test@test.com", "password", None)
        user.id = self.user_id
        db.session.commit()

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        result = super().tearDown()
        db.session.rollback()
        return result

    def test_message_model(self):

        message = Message(text="testing", user_id=self.user_id)

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "testing")

    def test_message_likes(self):

        message1 = Message(text="testing", user_id=self.user_id)

        message2 = Message(text="testing", user_id=self.user_id)

        user = User.signup("SecondTester", "test2@test.com", "password", None)
        user_id = 2
        user.id = user_id
        db.session.add_all([message1, message2, user])
        db.session.commit()

        user.likes.append(message1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == user_id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, message1.id)
