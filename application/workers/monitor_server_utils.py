"""This module is for utility functions for monitors interacting with dedicated servers."""
import time

from application.common import logger
from application.workers import monitor_constants

from operator_client import Operator


# A sub-routine to start the server.
def _start_server(client: Operator, server_name: str) -> bool:
    # Start the server. Issue the start command regardless.
    client.game.game_startup(server_name)

    # Check that the server actually is running.
    retry_count = 0
    server_status = client.game.get_game_status(server_name)
    is_running = server_status["is_running"]

    while not is_running and (retry_count < monitor_constants.MAX_COMMAND_RETRIES):
        logger.debug(
            f"Server {server_name} is not running. Retrying startup. Attempt: {retry_count}"
        )
        arg_dict = {}
        for arg in client.game.get_argument_by_game_name(server_name):
            arg_dict[arg["game_arg"]] = arg["game_arg_value"]
        client.game.game_startup(server_name, input_args=arg_dict)
        time.sleep(monitor_constants.COMMAND_WAIT_TIME)
        server_status = client.game.get_game_status(server_name)
        is_running = server_status["is_running"]
        retry_count += 1

    if not is_running:
        logger.error(f"Server {server_name} failed to start.")
        return False

    return True


# A sub-routine to stop the server.
def _stop_server(client: Operator, server_name: str) -> bool:
    # Stop the server. Issue the stop command regardless.
    client.game.game_shutdown(server_name)

    # Check that the server actually is shutdown.
    retry_count = 0
    server_status = client.game.get_game_status(server_name)
    is_running = server_status["is_running"]

    while is_running and (retry_count < monitor_constants.MAX_COMMAND_RETRIES):
        logger.debug(
            f"Server {server_name} is still running. Retrying shutdown. Attempt: {retry_count}"
        )
        client.game.game_shutdown(server_name)
        time.sleep(monitor_constants.COMMAND_WAIT_TIME)
        server_status = client.game.get_game_status(server_name)
        is_running = server_status["is_running"]
        retry_count += 1

    if not is_running:
        logger.error(f"Server {server_name} failed to start.")
        return False

    return True


# A sub-routine to update the server.
def _update_server(client: Operator, server_name: str):
    # Obtain some requisite information
    steam_install_dir = client.app.get_setting_by_name("steam_install_dir")
    game_info = client.game.get_game_by_name(server_name)

    game_id = game_info["items"][0]["game_id"]
    steam_id = game_info["items"][0]["game_steam_id"]
    install_path = game_info["items"][0]["game_install_dir"]

    thread_ident = client.steam.update_steam_app(steam_install_dir, steam_id, install_path)
    thread_alive = client.app.is_thread_alive(thread_ident)

    logger.debug(f"Update Thread Ident: {thread_ident}, Alive: {thread_alive}")

    while thread_alive:
        logger.debug("Waiting for update to finish....")
        thread_alive = client.app.is_thread_alive(thread_ident)
        time.sleep(1)

    steam_build_id = client.steam.get_steam_app_build_id(steam_install_dir, install_path, steam_id)

    if steam_build_id:
        client.game.update_game_data(game_id, game_steam_build_id=steam_build_id)
    else:
        logger.error(f"Failed to get Steam Build ID for {server_name}")
