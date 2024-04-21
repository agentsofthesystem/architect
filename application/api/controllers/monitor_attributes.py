import json
from application.common import logger


def attach_attribute_to_monitor(agent_id, monitor_type, payload):
    logger.info(f"Attaching attribute to monitor {monitor_type} on agent {agent_id}")

    if type(payload) is str:
        payload = json.loads(payload)

    try:
        attribute_name = payload["attribute_name"]
        attribute_value = payload["attribute_value"]
    except KeyError:
        logger.error("Attribute name or value missing in payload")
        return False

    monitor_id = -1

    logger.info(
        f"Attaching attribute {attribute_name} to monitor {monitor_id} with value {attribute_value}"
    )
    return True


def update_monitor_attribute(agent_id, monitor_type, payload):
    logger.info(f"Updating attribute to monitor {monitor_type} on agent {agent_id}")

    if type(payload) is str:
        payload = json.loads(payload)

    try:
        attribute_name = payload["attribute_name"]
        attribute_value = payload["attribute_value"]
    except KeyError:
        logger.error("Attribute name or value missing in payload")
        return False

    monitor_id = -1

    logger.info(
        f"Updating attribute {attribute_name} to monitor {monitor_id} with value {attribute_value}"
    )
    return True


def remove_attribute_from_monitor(agent_id, monitor_type, payload):
    logger.info(f"Removing attribute from monitor {monitor_type} on agent {agent_id}")

    if type(payload) is str:
        payload = json.loads(payload)

    try:
        attribute_name = payload["attribute_name"]
    except KeyError:
        logger.error("Attribute name or value missing in payload")
        return False

    monitor_id = -1

    logger.info(f"Removing attribute {attribute_name} from monitor {monitor_id}")
    return True
