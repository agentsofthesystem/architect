from application.workers.email import send_email
from application.models.user import UserSql
from kombu.exceptions import OperationalError


def _eliminate_data(session) -> None:
    test_item = UserSql.query.filter_by(email="test@test.com").first()
    session.delete(test_item)
    session.commit()


class TestSignup:

    def test_good_signup(self, app, mocker, session):

        mocker.patch("application.api.controllers.users._get_session_id", return_value="TEST")
        mocker.patch.object(send_email, "apply_async", return_value=None)

        payload = {
            "username": "TEST",
            "password": "TEST12345",
            "email": "test@test.com",
        }

        header = {"Content-Disposition": "form-data"}

        with app.test_client() as client:
            resp = client.post("/signup", data=payload, headers=header)

        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "/app/dashboard"

        _eliminate_data(session)

    def test_good_signup_with_email_error(self, app, mocker, session):

        mocker.patch("application.api.controllers.users._get_session_id", return_value="TEST")
        mocker.patch.object(
            send_email, "apply_async", return_value=None, side_effect=OperationalError
        )

        payload = {
            "username": "TEST",
            "password": "TEST12345",
            "email": "test@test.com",
        }

        header = {"Content-Disposition": "form-data"}

        with app.test_client() as client:
            resp = client.post("/signup", data=payload, headers=header)

        # Software will just keep chugging along. Same response as a good sign up.
        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "/app/dashboard"

        _eliminate_data(session)
