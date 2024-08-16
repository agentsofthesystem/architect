import logging
import os
import sqlalchemy
import sys
import traceback

from alembic import command
from alembic.config import Config
from flask import Flask, send_from_directory, render_template, request, redirect, flash, url_for
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_wtf.csrf import CSRFError
from kombu.utils.url import safequote

from application.common import logger, constants
from application.common.credentials import get_credentials
from application.common.user_loader import load_user  # noqa: F401
from application.common.toolbox import MyAdminIndexView, _get_application_path
from application.common.seed_data import update_system_settings, _handle_default_records
from application.config.config import DefaultConfig
from application.debugger import init_debugger
from application.extensions import (
    ADMIN,
    CELERY,
    CSRF,
    DATABASE,
    LOGIN_MANAGER,
    SOCKETIO,
    OAUTH_CLIENT,
)

from application import models as orm
from application.api.backend.views import backend
from application.api.public.views import public
from application.api.protected.views import protected

CURRENT_FOLDER = _get_application_path()
STATIC_FOLDER = os.path.join(CURRENT_FOLDER, "static")
TEMPLATE_FOLDER = os.path.join(CURRENT_FOLDER, "templates")
ALEMBIC_FOLDER = os.path.join(CURRENT_FOLDER, "alembic")


def _configure_celery(config: dict) -> None:
    celery_backed_by = config["CELERY_BACKED_BY"]
    broker_url = config["CELERY_BROKER"]
    predefined_queue = config["CELERY_SQS_PREDEFINED_QUEUE"]
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

        # Also - AWS Variables not set in environment, so SDK won't pick it up.
        if task_credentials is None:
            logger.critical("CONFIG CELERY: No Credentials Available... Exiting...")
            sys.exit(1)

        aws_access_key = task_credentials["AccessKeyId"]
        aws_secret_key = task_credentials["SecretAccessKey"]

        final_broker_url = f"sqs://{safequote(aws_access_key)}:{safequote(aws_secret_key)}@"

        if predefined_queue is None:
            final_transport_options = {"region": aws_region}
        else:
            final_transport_options = {
                "region": aws_region,
                "predefined_queues": {
                    "celery": {
                        "url": predefined_queue,
                        "access_key_id": aws_access_key,
                        "secret_access_key": aws_secret_key,
                    }
                },
            }

        if "RoleArn" in task_credentials:
            if task_credentials["RoleArn"] == "":
                logger.debug("CONFIG CELERY: RoleArn is Empty string. Skipping..")
            else:
                logger.debug("CONFIG CELERY: RoleArn Present, updating transport options.")
                final_transport_options.update({"sts_role_arn": task_credentials["RoleArn"]})

        else:
            logger.debug(
                "CONFIG CELERY: RoleArn is Missing Entirely. Must be using direct user credentials."
            )

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

    # Alembic safe URI does a replace ON TOP OF the quote_plus fix already done in the config.py
    # This is because Alembic does not like the % character in the URI.
    alembic_safe_uri = flask_app.config["SQLALCHEMY_DATABASE_URI"].replace("%", "%%")
    alembic_cfg.set_section_option(
        alembic_cfg.config_ini_section,
        "sqlalchemy.url",
        alembic_safe_uri,
    )

    alembic_cfg.set_section_option(
        alembic_cfg.config_ini_section, "script_location", ALEMBIC_FOLDER
    )
    with flask_app.app_context():
        with DATABASE.engine.begin() as connection:
            alembic_cfg.attributes["connection"] = connection

            command.upgrade(alembic_cfg, "head")


def _handle_logging(logger_level=constants.DEFAULT_LOG_LEVEL):
    """Update log configuration."""
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if type(logger_level) is str:
        logger_level = logger_level.upper()
        level = logging.getLevelName(logger_level)
    else:
        level = logger_level

    # Reconfigure logging again, this time with a file in addition to stdout.
    formatter = logging.Formatter(constants.DEFAULT_LOG_FORMAT)

    # Also route to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)


def create_app(config=None, init_db=True, init_celery=True):
    logger.debug("Begin initialization.")

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
    if init_celery:
        logger.debug("Initializing Celery")
        with flask_app.app_context():
            _configure_celery(flask_app.config)
    else:
        logger.debug("SKIP: Initializing Celery")

    # All the extension initializations go here
    LOGIN_MANAGER.login_view = "public.signin"
    LOGIN_MANAGER.init_app(flask_app)
    CSRF.init_app(flask_app)

    # Initialize Flask Admin Panel
    ADMIN.add_view(orm.user.UserView(orm.user.UserSql, DATABASE.session, "Users"))
    ADMIN.add_view(ModelView(orm.beta_user.BetaUser, DATABASE.session, "Beta Users"))
    ADMIN.add_view(ModelView(orm.setting.SettingsSql, DATABASE.session, "Settings"))
    ADMIN.add_view(orm.agent.AgentView(orm.agent.Agents, DATABASE.session, "Agents"))
    ADMIN.add_view(orm.monitor.MonitorView(orm.monitor.Monitor, DATABASE.session, "Monitors"))
    ADMIN.add_view(
        orm.monitor_attribute.MonitorAttrView(
            orm.monitor_attribute.MonitorAttribute, DATABASE.session, "Monitor Settings"
        )
    )
    ADMIN.add_view(
        orm.monitor_fault.MonitorFaultView(
            orm.monitor_fault.MonitorFault, DATABASE.session, "Faults"
        )
    )
    ADMIN.init_app(flask_app, index_view=MyAdminIndexView(url="/app/flask_admin"))
    ADMIN.add_link(MenuLink(name="Return", url="/app/admin", category="Links"))
    ADMIN.add_link(MenuLink(name="Signout", url="/signout", category="Links"))

    # Register all blueprints
    flask_app.register_blueprint(backend)
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
        return render_template("public/404.html"), 404

    @flask_app.errorhandler(500)
    def server_error(e):
        return render_template("public/500.html"), 500

    @flask_app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("For your protection, Please resubmit the form.", "warning")
        return redirect(url_for(request.endpoint))

    @flask_app.before_request
    def before_request_func():
        if request.endpoint is None:
            test_str = ""
        else:
            test_str = request.endpoint

        # Ignore updating settings for static back endpoints, public pages, and the favicon.
        if test_str == "static" or test_str == "favicon":
            return
        elif "public." in test_str:
            if test_str == "public.signin" or test_str == "public.signup":
                logger.debug(f"*** Updating System Settings for -> {test_str}")
                update_system_settings()
            return
        else:
            logger.debug(f"*** Updating System Settings for -> {test_str}")
            update_system_settings()

    # If not in test mode, run this.
    if not flask_app.config["TESTING"]:
        _handle_default_records(flask_app)

    # Initialize SocketIO
    SOCKETIO.init_app(flask_app)

    # Initialize OAuth Client
    OAUTH_CLIENT.client_id = flask_app.config["GOOGLE_CLIENT_ID"]

    # Import socket endpoints
    # Intentionally imported here after socketio initializes.
    from application.api.websocket import agents  # noqa: F401
    from application.api.websocket import monitors  # noqa: F401

    # Configure Logging
    _handle_logging(logger_level=config.LOG_LEVEL)

    logger.debug(f"{flask_app.name} has successfully initialized.")

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
