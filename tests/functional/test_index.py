class TestIndex:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_index(self, app):

        with app.test_client() as client:
            response = client.get("/")

        assert response.status_code == 200
