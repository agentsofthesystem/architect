from application.config.config import DefaultConfig
from application.factory import create_app, create_worker

config = DefaultConfig("kubernetes")
config.obtain_environment_variables()

APP = create_app(config=config, init_db=True)

WORKER = create_worker(APP)
