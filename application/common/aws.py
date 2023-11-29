import os
import boto3
import requests

from botocore.exceptions import ClientError

from application.common import logger
from application.common.constants import FARGATE_CONTAINER_API_IP


def get_task_credentials():
    creds_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "")
    credentials = None

    if creds_uri == "":
        logger.error("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI is Not Set")
    else:
        resp = requests.get("http://{}{}".format(FARGATE_CONTAINER_API_IP, creds_uri))
        if resp.status_code == 200:
            credentials = resp.json()
        else:
            logger.error(
                f"Unable to retrieve any information from API. Status Code: {resp.status_code}"
            )

    return credentials
