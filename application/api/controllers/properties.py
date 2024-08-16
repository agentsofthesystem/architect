import json

from flask_login import current_user

from application.common import logger
from application.extensions import DATABASE
from application.models.default_property import DefaultProperty
from application.models.property import Property


def get_default_property(property_name):
    return DefaultProperty.query.filter_by(property_name=property_name).first()


def get_property(user_id, property_name):

    default_property = get_default_property(property_name)

    property_check = Property.query.filter_by(
        user_id=user_id, default_property_id=default_property.default_property_id
    ).first()

    return (
        property_check.property_value if property_check else default_property.property_default_value
    )


def create_property(user_id, property_name, payload):
    logger.info("Creating property...")

    if current_user.user_id != user_id:
        logger.info("User does not have permission to create property.")
        return False

    default_property = get_default_property(property_name)

    property_check = Property.query.filter_by(
        user_id=user_id, default_property_id=default_property.default_property_id
    ).first()

    if property_check:
        logger.info("Property already exists.")
        return False

    if type(payload) is str:
        payload = json.loads(payload)

    value = payload["value"]

    new_property = Property(
        user_id=user_id,
        default_property_id=default_property.default_property_id,
        property_value=str(value),
    )

    try:
        DATABASE.session.add(new_property)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        return False

    return True


def update_property(user_id, property_name, payload):
    logger.info("Updating property...")

    if current_user.user_id != user_id:
        logger.info("User does not have permission to create property.")
        return False

    default_property = get_default_property(property_name)

    property_check = Property.query.filter_by(
        user_id=user_id, default_property_id=default_property.default_property_id
    ).first()

    if property_check is None:
        logger.info("Property does not exist, then create it.")
        if not create_property(user_id, property_name, payload):
            logger.error("Error creating property.")
            return False

    # Use this query to update the property
    property_qry = Property.query.filter_by(
        user_id=user_id, default_property_id=default_property.default_property_id
    )

    # Otherwise, update the property.
    if type(payload) is str:
        payload = json.loads(payload)

    value = payload["value"]
    update_dict = {"property_value": str(value)}

    try:
        property_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error updating property: {e}")
        return False

    return True


def delete_property(user_id, property_name):
    logger.info("Deleting property...")

    if current_user.user_id != user_id:
        logger.info("User does not have permission to create property.")
        return False

    default_property = get_default_property(property_name)

    property_check = Property.query.filter_by(
        user_id=user_id, default_property_id=default_property.default_property_id
    ).first()

    if property_check is None:
        logger.info("Property does not exist.")
        return False

    try:
        DATABASE.session.delete(property_check)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error deleting property: {e}")
        return False

    return True
