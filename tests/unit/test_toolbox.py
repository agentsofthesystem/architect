from application.common import toolbox


class TestToolbox:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_is_valid_email(self):
        email = "foo@bar.com"
        assert toolbox.is_valid_email(email) is True

        email = "foo@bar"
        assert toolbox.is_valid_email(email) is False

    def test_format_url_prefix(self):
        address = "example.com"
        assert toolbox.format_url_prefix(address) == "https://example.com"

        address = "http://example.com"
        assert toolbox.format_url_prefix(address) == "https://example.com"
