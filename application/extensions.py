from celery import Celery
from flask_admin import Admin
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from zerorpc import Server as ZeroRpcServer

task_modules = ["application.workers.email", "application.workers.game_server_control"]

ADMIN = Admin(template_mode="bootstrap3")

CELERY = Celery("celery_worker", include=task_modules)

CSRF = CSRFProtect()

DATABASE = SQLAlchemy()

LOGIN_MANAGER = LoginManager()

SOCKETIO = SocketIO()

ZRPC = ZeroRpcServer()
