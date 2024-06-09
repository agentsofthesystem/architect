from werkzeug.security import generate_password_hash
from application.models.user import UserSql


def _create_data(session) -> None:
    test_item = UserSql()
    test_item.username = "test"
    test_item.email = "test@test.com"
    test_item.password = generate_password_hash("password")

    session.add(test_item)
    session.commit()


def _destroy_data(session) -> None:
    test_item = UserSql.query.filter_by(email="test@test.com").first()
    session.delete(test_item)
    session.commit()


class TestSignin:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_good_signin(self, app, session):

        _create_data(session)

        payload = {"email": "test@test.com", "password": "password", "remember": True}
        header = {"Content-Disposition": "form-data"}

        with app.test_client() as client:
            resp = client.post("/signin", data=payload, headers=header)

        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "/app/dashboard"

        _destroy_data(session)

    def test_bad_signin(self, app, session):
        # Test user
        _create_data(session)

        payload = {"email": "test@test.com", "password": "bad"}
        header = {"Content-Disposition": "form-data"}

        with app.test_client() as client:
            resp = client.post("/signin", data=payload, headers=header)

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200

        _destroy_data(session)

    def test_missing_form_data(self, app):

        with app.test_client() as client:
            resp = client.post("/signin")

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200

    def test_invalid_user(self, app, session):

        _create_data(session)

        payload = {"email": "anothertest-user@test.com", "password": "password"}
        header = {"Content-Disposition": "form-data"}

        with app.test_client() as client:
            resp = client.post("/signin", data=payload, headers=header)

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200

        _destroy_data(session)
