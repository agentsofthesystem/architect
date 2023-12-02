import os
import requests

from flask import current_app

from application.common import logger
from application.common.constants import FARGATE_CONTAINER_API_IP


def get_credentials():
    task_credentials = get_task_credentials()

    if task_credentials is None:
        logger.warning("Unable to access Task IAM Role Credentials via API.")
    else:
        logger.debug("Using Task IAM Role Credentials")
        return task_credentials

    user_credentials = get_user_provided_credentials()

    if user_credentials is None:
        logger.error("Unable to obtain either TASK IAM Role or User Provided credentials...")
    else:
        logger.debug("Using credentials directly supplied by user. DEVELOPMENT ONLY!")
        return user_credentials


def get_user_provided_credentials():
    credentials = {}

    if "AWS_ACCESS_KEY_ID" in current_app.config:
        if current_app.config["AWS_ACCESS_KEY_ID"]:  # Prevent None from populating.
            credentials["AccessKeyId"] = current_app.config["AWS_ACCESS_KEY_ID"]

    if "AWS_SECRET_ACCESS_KEY" in current_app.config:
        if current_app.config["AWS_SECRET_ACCESS_KEY"]:
            credentials["SecretAccessKey"] = current_app.config["AWS_SECRET_ACCESS_KEY"]

    if list(credentials.keys()) != ["AccessKeyId", "SecretAccessKey"]:
        logger.error("Missing User Provided Access Key or Secret")
        return None

    return credentials


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
