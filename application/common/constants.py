from enum import Enum


class DeployTypes(Enum):
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    PYTHON = "python"


_DeployTypes = DeployTypes
