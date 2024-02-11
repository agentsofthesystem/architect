# -*- coding: utf-8 -*-
import os
import pytest

from selenium import webdriver

from application.config.config import DefaultConfig
from application.factory import create_app


@pytest.fixture(scope="module")
def client():
    os.environ["ENV"] = "TEST"

    config = DefaultConfig(deploy_type="python")

    config.DEBUG = False
    config.ENV = "production"

    config.WTF_CSRF_ENABLED = False

    setattr(config, "TESTING", True)

    app = create_app(config=config)

    with app.test_client() as client:
        ctx = app.app_context()
        ctx.push()

        yield client

        ctx.pop()


@pytest.fixture(params=["firefox"], scope="class")
def selenium_local_driver(request):
    resources = os.path.join(os.path.dirname(__file__), "resources")

    env_path = os.environ["PATH"]
    os.environ["PATH"] = f"{resources}:{env_path}"
    print(os.environ["PATH"])

    if request.param == "chrome":
        web_driver = webdriver.Chrome()
    elif request.param == "firefox":
        web_driver = webdriver.Firefox()

    web_driver.delete_all_cookies()

    request.cls.driver = web_driver

    yield

    web_driver.close()
