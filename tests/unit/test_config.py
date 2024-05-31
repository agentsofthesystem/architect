from application.config.config import DefaultConfig


class TestConfigObject:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def test_config(self):
        config = DefaultConfig("python")
        assert config.STRIPE_PUBLISHABLE_KEY == "pk_test1"

    def test_get(self):
        config = DefaultConfig("python")
        assert config.get("STRIPE_PUBLISHABLE_KEY") == "pk_test1"

    def test_obtain_environment_variables(self):
        config = DefaultConfig("python")
        config.obtain_environment_variables()
        config.update_derived_variables()
        assert config.STRIPE_PUBLISHABLE_KEY == "pk_test1"
