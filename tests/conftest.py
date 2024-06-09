# -*- coding: utf-8 -*-
import os

from pytest import fixture
from selenium import webdriver

from application.config.config import DefaultConfig
from application.extensions import DATABASE as _db
from application.factory import create_app
from application.common.seed_data import _handle_default_records

# @fixture(scope="module")
# def client():
#     config = DefaultConfig(deploy_type="python")

#     config.DEBUG = False
#     config.ENV = "production"
#     config.WTF_CSRF_ENABLED = False
#     setattr(config, "TESTING", True)

#     app = create_app(config=config, init_db=False)

#     with app.test_client() as client:
#         ctx = app.app_context()
#         ctx.push()

#         yield client

#         ctx.pop()


# Used in functional database tests.
@fixture(scope="session")
def app(request):
    """Test session-wide test `Flask` application."""

    test_config = DefaultConfig(deploy_type="python")

    test_config.DEBUG = False
    test_config.ENV = "production"
    test_config.WTF_CSRF_ENABLED = False
    test_config.TESTING = True
    test_config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    app = create_app(test_config)
    return app


# @fixture()
# def client(app):
#     with app.test_client() as client:
#         ctx = app.app_context()
#         ctx.push()
#         yield client
#         ctx.pop()


@fixture(autouse=True)
def _setup_app_context_for_test(request, app):
    """
    Given app is session-wide, sets up a app context per test to ensure that
    app and request stack is not shared between tests.
    """
    ctx = app.app_context()
    ctx.push()
    yield  # tests will run here
    ctx.pop()


@fixture(scope="session")
def db(app, request):
    """Returns session-wide initialized database"""
    with app.app_context():
        _db.create_all()
        # Run this here in test mode.
        _handle_default_records(app)
        yield _db
        _db.drop_all()


@fixture(scope="function")
def session(app, db, request):
    """Creates a new database session for each test, rolling back changes afterwards"""
    connection = _db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = _db._make_scoped_session(options=options)

    _db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


# Used in system tests
@fixture(params=["firefox"], scope="class")
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
