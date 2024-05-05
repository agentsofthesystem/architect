from enum import Enum
from application.common.timezones import get_time_zone_dict, get_hours_list


class DeployTypes(Enum):
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    PYTHON = "python"


class FriendRequestStates(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2
    CANCELED = 3


class GroupInviteStates(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2


class MessageCategories(Enum):
    ADMIN = 0
    SOCIAL = 1
    MONITOR = 2
    NOT_SET = 3


class MonitorTypes(Enum):
    AGENT = 0
    DEDICATED_SERVER = 1
    UPDATES = 2
    NOT_SET = 3


# Conversion functions between strings and Enums can go in this file.


# A function that takes a string and returns the corresponding Enum value for MonitorTypes
def monitor_type_from_string(monitor_type: str) -> MonitorTypes:
    monitor_type = monitor_type.upper()
    if monitor_type == "AGENT":
        return MonitorTypes.AGENT
    elif monitor_type == "DEDICATED_SERVER":
        return MonitorTypes.DEDICATED_SERVER
    elif monitor_type == "UPDATES":
        return MonitorTypes.UPDATES
    else:
        return MonitorTypes.NOT_SET


# A function that takes a MonitorTypes Enum value and returns the corresponding string
def monitor_type_to_string(monitor_type: MonitorTypes) -> str:
    if monitor_type == MonitorTypes.AGENT:
        return "AGENT"
    elif monitor_type == MonitorTypes.DEDICATED_SERVER:
        return "DEDICATED_SERVER"
    elif monitor_type == MonitorTypes.UPDATES:
        return "UPDATES"
    else:
        return "NOT_SET"


# Pagination Defaults
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10
DEFAULT_PER_PAGE_MAX = 100000

# Misc Application Constants
DEFAULT_SESSION_HOURS = 1
DEFAULT_EMAIL_DELAY_SECONDS = 10
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v2.html
CONTAINER_CREDENTIALS_API_IP = "169.254.170.2"
AGENT_SMITH_DEFAULT_PORT = 3000

# Time-related Constants
TIME_ZONE_DICT = get_time_zone_dict()
HOURS_LIST = get_hours_list()
TIMESTAMP_FORMAT_24_HR = "%Y-%m-%d %H:%M"  # 24 hour format
TIMESTAMP_FORMAT_12_HR = "%Y-%m-%d %I:%M %p"  # 12 hour format
DEFAULT_TIME_FORMAT_STR = TIMESTAMP_FORMAT_12_HR
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 60
HOURS_PER_DAY = 24
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24

# Defaults & Constants for Monitors
AGENT_SMITH_TIMEOUT = 10  # seconds
# These are the invalid statuses that can be returned from the agent. If Agent Smith ever
# alters what these status are, then this will become broken.
AGENT_SMITH_INVALID_HEALTH = ["InvalidAccessToken", "SSLError", "SSLCertMissing", None]
DEFAULT_MONITOR_TESTING_INTERVAL = 60  # seconds
DEFAULT_MONITOR_INTERVAL = 60 * SECONDS_PER_MINUTE  # 1 Hours

# Default System Settings
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
    # Monitors
    "MONITOR_TEST_MODE": {
        "pretty": "Test Mode for Monitors",
        "description": "Allows short intervals for testing monitors.",
        "category": "monitor",
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

# Define the default properties for the system users.
SYSTEM_DEFAULT_PROPERTIES = [
    {
        "property_name": "NOTIFICATION_DM_SOCIAL_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive direct message "
        "notifications for social interactions.",
    },
    {
        "property_name": "NOTIFICATION_EMAIL_SOCIAL_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive email notifications for "
        "social interactions.",
    },
    {
        "property_name": "NOTIFICATION_DM_GLOBAL_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive direct message for "
        "global notifications.",
    },
    {
        "property_name": "NOTIFICATION_EMAIL_GLOBAL_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive email notifications for "
        "global notifications.",
    },
    {
        "property_name": "NOTIFICATION_DM_MONITOR_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive direct message for "
        "agent monitor automation alerts.",
    },
    {
        "property_name": "NOTIFICATION_EMAIL_MONITOR_ENABLED",
        "property_type": "bool",
        "property_default_value": "True",
        "property_description": "Determines if the user will receive email notifications for "
        "agent monitor automation alerts.",
    },
    {
        "property_name": "USER_TIMEZONE",
        "property_type": "str",
        "property_default_value": "(UTC+0h) UTC",
        "property_description": "This is the default timezone for the user.",
    },
    {
        "property_name": "USER_HOUR_FORMAT",
        "property_type": "str",
        "property_default_value": "12",
        "property_description": "This is the default hour format for the user.",
    },
]

_DeployTypes = DeployTypes
