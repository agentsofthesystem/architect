from application.config.config import DefaultConfig
from application.factory import create_app


def main(config_type):
    config = DefaultConfig(config_type)
    config.obtain_environment_variables()

    APP = create_app(config=config)

    return APP


def start_app(*args, **kwargs):
    deploy_config = "docker_compose"
    if "deploy_as" in kwargs:
        deploy_config = kwargs["deploy_as"]

    return main(deploy_config)
