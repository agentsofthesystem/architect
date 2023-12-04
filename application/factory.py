import os
import sqlalchemy
import sys
import traceback

from flask import (
    Flask,
    send_from_directory,
    render_template,
    request,
)

from alembic import command
from alembic.config import Config
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from kombu.utils.url import safequote
from werkzeug.security import generate_password_hash

from application.common import logger
from application.common.credentials import get_credentials
from application.common.user_loader import load_user  # noqa: F401
from application.common.tools import MyAdminIndexView, _get_application_path
from application.common.seed_data import seed_system_settings, update_system_settings
from application.config.config import DefaultConfig
from application.debugger import init_debugger
from application.extensions import (
    ADMIN,
    CELERY,
    CSRF,
    DATABASE,
    LOGIN_MANAGER,
)
from application.models.user import UserSql
from application.models.setting import SettingsSql
from application.uix.public.views import public
from application.uix.protected.views import protected

CURRENT_FOLDER = _get_application_path()
STATIC_FOLDER = os.path.join(CURRENT_FOLDER, "static")
TEMPLATE_FOLDER = os.path.join(CURRENT_FOLDER, "templates")
ALEMBIC_FOLDER = os.path.join(CURRENT_FOLDER, "alembic")


def _configure_celery(config: dict) -> None:
    celery_backed_by = config["CELERY_BACKED_BY"]
    broker_url = config["CELERY_BROKER"]
    aws_region = config["AWS_REGION"]
    aws_access_key = config["AWS_ACCESS_KEY_ID"]
    aws_secret_key = config["AWS_SECRET_ACCESS_KEY"]

    if celery_backed_by.lower() == "redis":
        logger.debug("CONFIG CELERY: Using Redis")

        CELERY.conf.update(
            broker_url=broker_url,
            result_backend=config["CELERY_BACKEND"],
        )

    elif celery_backed_by.lower() == "sqs":
        logger.debug("CONFIG CELERY: Using SQS")

        task_credentials = get_credentials()

        aws_access_key = task_credentials["AccessKeyId"]
        aws_secret_key = task_credentials["SecretAccessKey"]

        final_broker_url = f"sqs://{safequote(aws_access_key)}:{safequote(aws_secret_key)}@"

        final_transport_options = {"region": aws_region}

        if "RoleArn" in task_credentials:
            final_transport_options.update({"sts_role_arn": task_credentials["RoleArn"]})

        CELERY.conf.update(
            broker_url=final_broker_url, broker_transport_options=final_transport_options
        )

    else:
        logger.critical(f"Error: Unsupported Celery Backed Type: {celery_backed_by}")
        sys.exit(1)

    CELERY.conf.update(config)


def _handle_migrations(flask_app: Flask) -> None:
    alembic_init = os.path.join(ALEMBIC_FOLDER, "alembic.ini")

    alembic_cfg = Config(alembic_init)

    alembic_cfg.set_section_option(
        alembic_cfg.config_ini_section,
        "sqlalchemy.url",
        flask_app.config["SQLALCHEMY_DATABASE_URI"],
    )

    alembic_cfg.set_section_option(
        alembic_cfg.config_ini_section, "script_location", ALEMBIC_FOLDER
    )
    with flask_app.app_context():
        with DATABASE.engine.begin() as connection:
            alembic_cfg.attributes["connection"] = connection

            command.upgrade(alembic_cfg, "head")


def _handle_default_records(flask_app: Flask) -> None:
    """Add initial admin user & settings."""

    # Setup an admin user.
    with flask_app.app_context():
        user_obj = UserSql.query.filter_by(username=flask_app.config["ADMIN_USER"]).first()

        if user_obj is None:
            new_admin_user = UserSql()
            new_admin_user.admin = True
            new_admin_user.verified = True
            new_admin_user.first_name = "admin"
            new_admin_user.last_name = "admin"
            new_admin_user.subscribed = True
            new_admin_user.username = flask_app.config["ADMIN_USER"]
            new_admin_user.email = flask_app.config["DEFAULT_ADMIN_EMAIL"]
            new_admin_user.password = generate_password_hash(flask_app.config["ADMIN_PASSWORD"])
            try:
                DATABASE.session.add(new_admin_user)
                DATABASE.session.commit()
            except Exception as error:
                logger.error(error)

        # Add configurable settings to the DATABASE
        seeded_settings_obj = SettingsSql.query.filter_by(name="IS_SEEDED").first()

        if seeded_settings_obj is None:
            # System settings mirror config.py items.
            seed_system_settings(flask_app.config)

        # Override the app name from the settings database.
        app_name = SettingsSql.query.filter_by(name="APP_NAME").first()
        flask_app.name = app_name.value


def create_app(config=None, init_db=True):
    logger.info("Begin initialization.")

    if config is None:
        config = DefaultConfig("python")
        logger.critical("WARNING. Missing Configuration. Initializing with default...")

    flask_app = Flask(
        "NOT_SET",
        instance_relative_config=True,
        static_folder=STATIC_FOLDER,
        static_url_path="/static",
        template_folder=TEMPLATE_FOLDER,
    )

    # Changing instance path to directory above.
    instance_path = os.path.dirname(flask_app.instance_path)
    flask_app.instance_path = instance_path

    flask_app.config.from_object(config)

    # Set up debugging if the user asked for it.
    init_debugger(flask_app)

    # Configure Celery Settings
    with flask_app.app_context():
        _configure_celery(flask_app.config)

    # All the extension initializations go here
    LOGIN_MANAGER.login_view = "public.signin"
    LOGIN_MANAGER.init_app(flask_app)
    CSRF.init_app(flask_app)

    # Initialize Flask Admin Panel
    ADMIN.add_view(ModelView(UserSql, DATABASE.session, "Users"))
    ADMIN.add_view(ModelView(SettingsSql, DATABASE.session, "Settings"))
    ADMIN.init_app(flask_app, index_view=MyAdminIndexView(url="/app/flask_admin"))
    ADMIN.add_link(MenuLink(name="Return", url="/app/admin", category="Links"))
    ADMIN.add_link(MenuLink(name="Signout", url="/signout", category="Links"))

    # Register all blueprints
    flask_app.register_blueprint(public)
    flask_app.register_blueprint(protected)

    if init_db is False:
        return flask_app

    try:
        DATABASE.init_app(flask_app)
        _handle_migrations(flask_app)
    except sqlalchemy.exc.OperationalError:
        logger.critical("Error: Database string invalid or DB service not reachable.")
        traceback.print_exc()
        return None

    @flask_app.route("/favicon.ico")
    def favicon():
        favicon_path = os.path.join(STATIC_FOLDER, "images")
        return send_from_directory(favicon_path, "favicon.ico", mimetype="image/vnd.microsoft.icon")

    # Error Routes
    @flask_app.errorhandler(404)
    def not_found(e):
        return render_template("uix/404.html")

    @flask_app.errorhandler(500)
    def server_error(e):
        return render_template("uix/500.html")

    @flask_app.before_request
    def before_request_func():
        if request.endpoint is None:
            test_str = ""
        else:
            test_str = request.endpoint

        if "favicon" not in test_str and "static" != test_str:
            logger.debug(f"*** Updating System Settings for -> {test_str}")
            update_system_settings()

    _handle_default_records(flask_app)

    logger.info(f"{flask_app.name} has successfully initialized.")

    return flask_app


def create_worker(flask_app: Flask):
    # Configure Celery Settings
    with flask_app.app_context():
        _configure_celery(flask_app.config)

    class ContextTask(CELERY.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    CELERY.Task = ContextTask

    return CELERY
