import json

from application.common import logger
from application.extensions import DATABASE
from application.models.default_property import DefaultProperty
from application.models.property import Property


def get_default_property(property_name):
    return DefaultProperty.query.filter_by(property_name=property_name).first()


def create_property(user_id, property_name, payload):
    logger.info("Creating property...")

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


def delete_property(user_id, property_name):
    logger.info("Deleting property...")

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
