from application.common import logger


def create_monitor(agent_id, monitor_type):
    logger.info(f"Creating monitor for agent {agent_id} with type {monitor_type}")
    return True


def disable_monitor(agent_id, monitor_type):
    logger.info(f"Disabling monitor for agent {agent_id} with type {monitor_type}")
    return True
