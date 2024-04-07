from enum import Enum


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
    AUTOMATION = 2
    NOT_SET = 3


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
]

_DeployTypes = DeployTypes
