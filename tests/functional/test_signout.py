import pytest


class TestSignout:
    @pytest.mark.skip(reason="TODO: Fix this test")
    def test_good_signout(self, client):
        resp = client.get("/signout")

        assert resp.status_code == 302
        location = resp.headers["location"]
        assert location == "http://localhost/"
