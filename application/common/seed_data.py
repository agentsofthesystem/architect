from flask import current_app, Flask
from werkzeug.security import generate_password_hash

from application.extensions import DATABASE
from application.common import logger
from application.common.constants import SYSTEM_SETTINGS, SYSTEM_DEFAULT_PROPERTIES
from application.common.toolbox import _get_setting
from application.models.default_property import DefaultProperty
from application.models.setting import SettingsSql
from application.models.user import UserSql


def _handle_default_records(flask_app: Flask) -> None:
    """Add initial admin user & settings."""

    # Setup an admin user & Seed system settings & default properties.
    with flask_app.app_context():
        # Add an admin user to the DATABASE
        user_obj = UserSql.query.filter_by(username=flask_app.config["ADMIN_USER"]).first()

        if user_obj is None:
            new_admin_user = UserSql()
            new_admin_user.admin = True
            new_admin_user.verified = True
            new_admin_user.first_name = "admin"
            new_admin_user.last_name = "admin"
            new_admin_user.subscribed = True
            new_admin_user.username = flask_app.config["ADMIN_USER"]
            new_admin_user.email = flask_app.config["DEFAULT_ADMIN_EMAIL"]
            new_admin_user.password = generate_password_hash(flask_app.config["ADMIN_PASSWORD"])
            try:
                DATABASE.session.add(new_admin_user)
                DATABASE.session.commit()
            except Exception as error:
                logger.error(error)

        # Add configurable settings to the DATABASE
        seeded_settings_obj = SettingsSql.query.filter_by(name="IS_SEEDED").first()

        if seeded_settings_obj is None:
            # System settings mirror config.py items.
            seed_system_settings(flask_app.config)

        # Override the app name from the settings database.
        app_name = SettingsSql.query.filter_by(name="APP_NAME").first()
        flask_app.name = app_name.value

        # Seed the default properties
        seed_system_default_properties()


def seed_system_settings(configuration):
    system_settings = SYSTEM_SETTINGS.keys()

    for setting in system_settings:
        new_setting = SettingsSql()

        if setting in configuration.keys():
            value = str(configuration[setting])
        else:
            value = ""

        new_setting.name = setting
        new_setting.pretty_name = SYSTEM_SETTINGS[setting]["pretty"]
        new_setting.description = SYSTEM_SETTINGS[setting]["description"]
        new_setting.category = SYSTEM_SETTINGS[setting]["category"]
        new_setting.data_type = SYSTEM_SETTINGS[setting]["type"]
        new_setting.value = value

        setting_qry = SettingsSql.query.filter_by(name=setting)

        if setting_qry.first() is None:
            DATABASE.session.add(new_setting)

    DATABASE.session.commit()

    configuration["IS_SEEDED"] = True


def seed_system_default_properties():
    for default_property in SYSTEM_DEFAULT_PROPERTIES:
        query = DefaultProperty.query.filter_by(property_name=default_property["property_name"])

        if query.first() is None:
            new_default_property = DefaultProperty(
                property_name=default_property["property_name"],
                property_type=default_property["property_type"],
                property_default_value=default_property["property_default_value"],
                property_description=default_property["property_description"],
            )

            DATABASE.session.add(new_default_property)
        else:
            logger.info(
                f"Default Property {default_property['property_name']} already exists so updating"
            )
            update_property_dict = {
                "property_type": default_property["property_type"],
                "property_default_value": default_property["property_default_value"],
                "property_description": default_property["property_description"],
            }
            query.update(update_property_dict)

    try:
        DATABASE.session.commit()
    except Exception as error:
        logger.error(error)


def update_system_settings():
    system_settings = SYSTEM_SETTINGS.keys()

    # One DB Access per request minimizes number of accesses.
    setting_objs = SettingsSql.query.all()

    for setting in system_settings:
        dtype = SYSTEM_SETTINGS[setting]["type"]

        # TODO - Nested for loop.  Would be better to have O(n) instead we have O(n^2)
        value = _get_setting(setting, setting_objs)

        output = ""
        if dtype == "str":
            output = str(value)
        elif dtype == "int":
            output = int(value)
        elif dtype == "float":
            output = float(value)
        elif dtype == "bool":
            output = True if value.lower() == "true" else False
        else:
            raise TypeError

        current_app.config[setting] = output
