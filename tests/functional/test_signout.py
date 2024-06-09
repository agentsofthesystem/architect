class TestSignout:

    def test_good_signout(self, app):

        with app.test_client() as client:
            resp = client.get("/signout")

        assert resp.status_code == 302

        location = resp.headers["location"]

        assert location == "/"
