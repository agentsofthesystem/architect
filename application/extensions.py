from celery import Celery
from flask_admin import Admin
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

task_modules = [
    "application.workers.monitor_agent",
    "application.workers.monitor_dedicated_server",
    "application.workers.monitor_dedicated_server_updates",
    "application.workers.monitor_test_task",
    "application.workers.email",
    "application.workers.game_server_control",
]

ADMIN = Admin(template_mode="bootstrap3")

CELERY = Celery("celery_worker", include=task_modules)

CSRF = CSRFProtect()

DATABASE = SQLAlchemy()

LOGIN_MANAGER = LoginManager()

SOCKETIO = SocketIO()
