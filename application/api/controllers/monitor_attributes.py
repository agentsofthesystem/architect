import json

from application.common import logger
from application.extensions import DATABASE
from application.models.monitor import Monitor
from application.models.monitor_attribute import MonitorAttribute


def _get_monitor_id(agent_id, monitor_type):
    logger.debug(f"Getting monitor id for agent {agent_id} with type {monitor_type}")
    # Retrieve the monitor id for the agent and monitor type
    monitor_obj = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type).first()
    return monitor_obj.monitor_id


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

    try:
        monitor_id = _get_monitor_id(agent_id, monitor_type)
    except Exception:
        logger.error(f"Failed to get monitor id for agent {agent_id} with type {monitor_type}")
        return False

    # Create a new MonitorAttribute record
    new_monitor_attribute = MonitorAttribute(
        monitor_id=monitor_id, attribute_name=attribute_name, attribute_value=attribute_value
    )

    try:
        DATABASE.session.add(new_monitor_attribute)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to attach attribute to monitor {monitor_id}")
        logger.error(e)
        return False

    logger.info(
        f"Attached attribute {attribute_name} to monitor {monitor_id} with value {attribute_value}"
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

    try:
        monitor_id = _get_monitor_id(agent_id, monitor_type)
    except Exception:
        logger.error(f"Failed to get monitor id for agent {agent_id} with type {monitor_type}")
        return False

    # Check and see if the attribute already exists
    monitor_attribute_qry = MonitorAttribute.query.filter_by(
        monitor_id=monitor_id, attribute_name=attribute_name
    )

    if monitor_attribute_qry.first() is None:
        logger.debug(f"Attribute {attribute_name} does not exist for monitor {monitor_id}")
        # Create a new MonitorAttribute record
        if not attach_attribute_to_monitor(agent_id, monitor_type, payload):
            logger.error(f"Failed to attach attribute {attribute_name} to monitor {monitor_id}")
            return False
    else:
        # Update the attribute value & name
        update_dict = {"attribute_name": attribute_name, "attribute_value": attribute_value}
        try:
            monitor_attribute_qry.update(update_dict)
            DATABASE.session.commit()
        except Exception as e:
            logger.error(f"Failed to update attribute {attribute_name} for monitor {monitor_id}")
            logger.error(e)
            return False

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

    try:
        monitor_id = _get_monitor_id(agent_id, monitor_type)
    except Exception:
        logger.error(f"Failed to get monitor id for agent {agent_id} with type {monitor_type}")
        return False

    # Retrieve the monitor attribute record
    monitor_attribute_obj = MonitorAttribute.query.filter_by(
        monitor_id=monitor_id, attribute_name=attribute_name
    ).first()

    if monitor_attribute_obj is None:
        logger.debug(f"Attribute {attribute_name} does not exist for monitor {monitor_id}")
        return False

    try:
        DATABASE.session.delete(monitor_attribute_obj)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to remove attribute {attribute_name} from monitor {monitor_id}")
        logger.error(e)
        return False

    logger.info(f"Removing attribute {attribute_name} from monitor {monitor_id}")
    return True
