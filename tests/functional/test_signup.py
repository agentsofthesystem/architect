from application.workers.email import emailer
from application.models.user import UserSql
from kombu.exceptions import OperationalError


class TestSignup:
    def test_good_signup(self, client, mocker):
        mocker.patch.object(emailer, "apply_async", return_value=None)

        payload = {
            "username": "TEST",
            "password": "TEST12345",
            "email": "test@test.com",
            "first": "TEST",
            "last": "TEST",
        }

        header = {"Content-Disposition": "form-data"}
        resp = client.post("/signup", data=payload, headers=header)

        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "http://localhost/app/main"

        obj = UserSql.objects(email="test@test.com")
        obj[0].delete()

    def test_good_signup_with_email_error(self, client, mocker):
        mocker.patch.object(emailer, "apply_async", return_value=None, side_effect=OperationalError)

        payload = {
            "username": "TEST",
            "password": "TEST12345",
            "email": "test@test.com",
            "first": "TEST",
            "last": "TEST",
        }

        header = {"Content-Disposition": "form-data"}
        resp = client.post("/signup", data=payload, headers=header)

        # Software will just keep chugging along. Same response as a good sign up.
        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "http://localhost/app/main"

        obj = UserSql.objects(email="test@test.com")
        obj[0].delete()
