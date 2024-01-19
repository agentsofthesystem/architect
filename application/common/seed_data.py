from flask import current_app

from application.extensions import DATABASE
from application.common.toolbox import _get_setting
from application.models.setting import SettingsSql

SYSTEM_SETTINGS = {
    # General Settings
    "APP_NAME": {
        "pretty": "Application Name",
        "description": "System Application Name",
        "category": "name",
        "type": "str",
    },
    "APP_WEBSITE": {
        "pretty": "Application Domain Name",
        "description": "System Application Domain Name",
        "category": "name",
        "type": "str",
    },
    "APP_PRETTY_NAME": {
        "pretty": "Application Display Name",
        "description": "System Application Display Name",
        "category": "name",
        "type": "str",
    },
    # AWS
    "AWS_REGION": {
        "pretty": "Aws Region",
        "description": "Region to use for AWS.",
        "category": "aws",
        "type": "str",
    },
    # Email
    "DEFAULT_MAIL_SENDER": {
        "pretty": "Email Default Sender",
        "description": "From email for all emails sent",
        "category": "email",
        "type": "str",
    },
    # Payments
    "STRIPE_PUBLISHABLE_KEY": {
        "pretty": "Stripe Publish Key",
        "description": "",
        "category": "payments",
        "type": "str",
    },
    "STRIPE_SECRET_KEY": {
        "pretty": "Stripe Secret Key",
        "description": "",
        "category": "payments",
        "type": "str",
    },
    "STRIPE_MONTHLY_PRICE_ID": {
        "pretty": "Price ID For Monthly Price Option",
        "description": "",
        "category": "payments",
        "type": "str",
    },
    "STRIPE_ANNUAL_PRICE_ID": {
        "pretty": "Price ID For Annual Price Option",
        "description": "",
        "category": "payments",
        "type": "str",
    },
    "STRIPE_WEBHOOK_SECRET": {
        "pretty": "Webhook secret for stripe",
        "description": "",
        "category": "payments",
        "type": "str",
    },
    # Top Level Settings
    "APP_ENABLE_PAYMENTS": {
        "pretty": "Application Payments Enable",
        "description": "Turn Payments feature on or off",
        "category": "system",
        "type": "bool",
    },
    "APP_ENABLE_EMAIL": {
        "pretty": "Application Enable Email",
        "description": "Turn system wide emails on or off",
        "category": "system",
        "type": "bool",
    },
    "APP_ENABLE_BETA": {
        "pretty": "Application Enable Beta Mode",
        "description": "Only allow users in beta table to signup.",
        "category": "system",
        "type": "bool",
    },
    # This one is special so the factory.py only runs the init code once.
    "IS_SEEDED": {
        "pretty": "System Settings are Seeded.",
        "description": "Stores whether the system has already been seeded once or not.",
        "category": "system",
        "type": "bool",
    },
}


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
