# -*- coding: utf-8 -*-
import json
import os

from datetime import timedelta

from application.common import logger, constants


class DefaultConfig:
    ######################################################################
    # Configurable Settings
    # These must still be present here but user may change later
    ######################################################################

    # App name and secret
    APP_DOMAIN = "agentsofthesystem.com"
    APP_NAME = "TheArchitect"
    APP_WEBSITE = f"www.{APP_DOMAIN}"
    APP_PRETTY_NAME = "The Architect"
    SECRET_KEY = "super-secret-key-be-sure-to-change-me"
    DEPLOYMENT_TYPE = "docker_compose"  # also supports kubernetes

    # Top-level App Controls
    APP_ENABLE_PAYMENTS = False
    APP_ENABLE_EMAIL = False
    APP_ENABLE_BETA = False

    # AWS Settings
    AWS_REGION = "us-east-1"
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None

    # Email Settings
    DEFAULT_MAIL_SENDER = f"architect@{APP_DOMAIN}"

    # Celery Settings
    CELERY_BROKER = "redis://redis-service:6379"
    CELERY_BACKEND = "redis://redis-service:6379"
    CELERY_BACKED_BY = "REDIS"
    CELERY_SQS_PREDEFINED_QUEUE = None

    # Log/Verbosity Settings
    OPERATOR_CLIENT_VERBOSE = False

    ######################################################################
    # Non - Re-Configurable Settings
    ######################################################################

    # Flask specific configs
    DEBUG = False
    ENV = "production"
    FLASK_RUN_HOST = "0.0.0.0"
    FLASK_RUN_PORT = "3000"
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=constants.DEFAULT_SESSION_HOURS)
    IS_SEEDED = True

    # SQL Database Settings
    SQL_DATABASE_USER = "admin"
    SQL_DATABASE_PASS = "REPLACEME"
    # SQL_DATABASE_SERVER = "mariadb-service"
    SQL_DATABASE_SERVER = "localhost"
    SQL_DATABASE_PORT = "3306"
    SQL_DATABASE_NAME = "app"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{SQL_DATABASE_USER}:{SQL_DATABASE_PASS}@{SQL_DATABASE_SERVER}:{SQL_DATABASE_PORT}/{SQL_DATABASE_NAME}"  # noqa: E501
    SQL_DEPLOY_SECRET = None

    # Stripe Payment configs
    # This is a test key. Okay to expose.
    STRIPE_PUBLISHABLE_KEY = "pk_test1"
    STRIPE_SECRET_KEY = "pk_test2"
    STRIPE_MONTHLY_PRICE_ID = "price_id1"
    STRIPE_ANNUAL_PRICE_ID = "price_id2"
    STRIPE_WEBHOOK_SECRET = "whsec_abc123"

    # Admin Stuff
    ADMIN_USER = "Global Admin"
    ADMIN_PASSWORD = "password"  # Default password
    DEFAULT_ADMIN_EMAIL = f"admin@{APP_DOMAIN}"
    FLASK_ADMIN_SWATCH = "cosmo"  # See https://bootswatch.com/3/ for swatches

    def __init__(self, deploy_type):
        configuration_options = [el.value for el in constants._DeployTypes]

        if deploy_type not in configuration_options:
            logger.info(
                f"Configuration: {deploy_type} is not a valid configuration type, "
                f"which are: {configuration_options}"
            )
            raise RuntimeError

        self.DEPLOYMENT_TYPE = deploy_type

    @classmethod
    def get(cls, attribute, default_value=None):
        if hasattr(cls, attribute):
            return getattr(cls, attribute)
        else:
            return default_value

    @classmethod
    def obtain_environment_variables(cls):
        for var in cls.__dict__.keys():
            if var[:1] != "_" and var != "obtain_environment_variables":
                if var in os.environ:
                    value = os.environ[var].lower()
                    if value == "true" or value == "True" or value == "TRUE":
                        setattr(cls, var, True)
                    elif value == "false" or value == "False" or value == "FALSE":
                        setattr(cls, var, False)
                    else:
                        setattr(cls, var, os.environ[var])

        cls.update_derived_variables()

    @classmethod
    def __str__(cls):
        print_str = ""
        for var in cls.__dict__.keys():
            if var[:1] != "_" and var != "obtain_environment_variables":
                print_str += f"VAR: {var} set to: {getattr(cls,var)}\n"
        return print_str

    @classmethod
    def update_derived_variables(cls):
        """Update Computed Configuration Variables."""

        if cls.SQL_DEPLOY_SECRET:
            logger.info("Configuration Alert!: Overriding DB URI with deploy secret!")
            unpack_string = json.loads(cls.SQL_DEPLOY_SECRET)
            cls.SQL_DATABASE_USER = unpack_string["username"]
            cls.SQL_DATABASE_PASS = unpack_string["password"]

        cls.SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{cls.SQL_DATABASE_USER}:{cls.SQL_DATABASE_PASS}@{cls.SQL_DATABASE_SERVER}:{cls.SQL_DATABASE_PORT}/{cls.SQL_DATABASE_NAME}"  # noqa: E501

        cls.DEFAULT_MAIL_SENDER = f"architect@{cls.APP_DOMAIN}"
