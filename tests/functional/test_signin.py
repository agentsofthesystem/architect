from application.models.user import UserSql
from werkzeug.security import generate_password_hash


class TestSignin:
    @classmethod
    def setup_class(cls):
        test_item = UserSql()
        test_item.username = "test"
        test_item.email = "test@test.com"
        test_item.password = generate_password_hash("password")
        test_item.save()

    @classmethod
    def teardown_class(cls):
        users = UserSql.objects(email="test@test.com")
        for user in users:
            user.delete()

    def test_good_signin(self, client):
        payload = {"email": "test@test.com", "password": "password", "remember": True}
        header = {"Content-Disposition": "form-data"}
        resp = client.post("/signin", data=payload, headers=header)

        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "http://localhost/app/main"

    def test_bad_signin(self, client):
        # Test user

        payload = {"email": "test@test.com", "password": "bad"}
        header = {"Content-Disposition": "form-data"}
        resp = client.post("/signin", data=payload, headers=header)

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200

    def test_missing_form_data(self, client):
        resp = client.post("/signin")

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200

    def test_invalid_user(self, client):
        payload = {"email": "anothertest-user@test.com", "password": "password"}
        header = {"Content-Disposition": "form-data"}
        resp = client.post("/signin", data=payload, headers=header)

        # Expect a 200 because app re-renders same page in this case.
        assert resp.status_code == 200
