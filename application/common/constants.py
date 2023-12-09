from enum import Enum


class DeployTypes(Enum):
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    PYTHON = "python"


# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v2.html
CONTAINER_CREDENTIALS_API_IP = "169.254.170.2"

AGENT_SMITH_DEFAULT_PORT = 3000

_DeployTypes = DeployTypes
