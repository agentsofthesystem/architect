from enum import Enum


class DeployTypes(Enum):
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    PYTHON = "python"


# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v2.html
FARGATE_CONTAINER_API_IP = "169.254.170.2"

_DeployTypes = DeployTypes
