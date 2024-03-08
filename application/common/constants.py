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


# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v2.html
CONTAINER_CREDENTIALS_API_IP = "169.254.170.2"

AGENT_SMITH_DEFAULT_PORT = 3000

# Pagination Defaults
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10
DEFAULT_PER_PAGE_MAX = 100000

DEFAULT_SESSION_HOURS = 1
DEFAULT_EMAIL_DELAY_SECONDS = 10

_DeployTypes = DeployTypes
