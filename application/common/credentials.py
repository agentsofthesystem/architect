import os
import requests

from flask import current_app

from application.common import logger
from application.common.constants import CONTAINER_CREDENTIALS_API_IP

_LOCAL_DEBUG = False


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
        logger.warning("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI is Not Set")
    else:
        # Don't want to configure this via env. It's just for local testing.
        if _LOCAL_DEBUG:
            endpoint_url = "http://{}{}".format("localhost:8888", creds_uri)
        else:
            endpoint_url = "http://{}{}".format(CONTAINER_CREDENTIALS_API_IP, creds_uri)

        logger.info(f"AWS Relative Endpoint: {endpoint_url}")
        resp = requests.get(endpoint_url)
        if resp.status_code == 200:
            credentials = resp.json()
        else:
            logger.error(
                f"Unable to retrieve any information from API. Status Code: {resp.status_code}"
            )

    return credentials
