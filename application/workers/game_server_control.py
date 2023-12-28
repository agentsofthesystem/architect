import time

from application.extensions import CELERY
from application.common import logger

from operator_client import Operator


@CELERY.task(bind=True)
def startup_game_server(self, hostname: str, port: str, verbose: bool, token: str, game_name: str):
    logger.info(f"Staring up game: {game_name}")

    try:
        client = Operator(hostname, port, verbose, token=token)

        args_list = client.game.get_argument_by_game_name(game_name)
        arg_dict = {}

        for arg in args_list:
            arg_dict[arg["game_arg"]] = arg["game_arg_value"]

        client.game.game_startup(game_name, input_args=arg_dict)
    except Exception as error:
        logger.critical(error)
        self.update_state(state="FAILURE")
        return

    self.update_state(state="SUCCESS")
    return {"status": "Task Completed!"}


@CELERY.task(bind=True)
def shutdown_game_server(self, hostname: str, port: str, verbose: bool, token: str, game_name: str):
    logger.info(f"Shutting down game: {game_name}")

    try:
        client = Operator(hostname, port, verbose, token=token)
        client.game.game_shutdown(game_name)

    except Exception as error:
        logger.critical(error)
        self.update_state(state="FAILURE")
        return

    self.update_state(state="SUCCESS")
    return {"status": "Task Completed!"}


@CELERY.task(bind=True)
def restart_game_server(self, hostname: str, port: str, verbose: bool, token: str, game_name: str):
    logger.info(f"Restarting game: {game_name}")

    try:
        client = Operator(hostname, port, verbose, token=token)

        client.game.game_shutdown(game_name)

        time.sleep(10)  # TODO - Make this a constant

        args_list = client.game.get_argument_by_game_name(game_name)
        arg_dict = {}

        for arg in args_list:
            arg_dict[arg["game_arg"]] = arg["game_arg_value"]

        client.game.game_startup(game_name, input_args=arg_dict)

    except Exception as error:
        logger.critical(error)
        self.update_state(state="FAILURE")
        return

    self.update_state(state="SUCCESS")
    return {"status": "Task Completed!"}
