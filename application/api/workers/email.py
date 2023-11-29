import boto3

from botocore.config import Config
from botocore.exceptions import ClientError
from flask import current_app

from application.extensions import CELERY
from application.common import logger
from application.common.aws import get_task_credentials
from application.common.tools import _get_setting
from application.models.setting import SettingsSql


@CELERY.task(bind=True)
def emailer(self, sender: str, subject: str, recipient: str, html: str = "", text: str = ""):
    aws_region = None
    aws_key_id = None
    aws_key_secret = None
    task_credentials = None

    try:
        setting_objs = SettingsSql.query.filter_by(category="aws").all()

        if setting_objs is None:
            logger.critical("emailer: Not Settings Objects for AWS category.")
            self.update_state(state="FAILURE")
            return

        # Region is stored as database item.
        aws_region = _get_setting("AWS_REGION", setting_objs)

        # If running inside of an ECS container, then task credentials are supplied via FARGATE API.
        task_credentials = get_task_credentials()

        # AWS Key/Secret stored as environment variable / app config object.
        if "AWS_ACCESS_KEY_ID" in current_app.config:
            aws_key_id = current_app.config["AWS_ACCESS_KEY_ID"]
        else:
            logger.debug("emailer: Missing AWS Access Key ID. Returning...")
            if task_credentials is None:
                logger.critical(
                    "emailer: No Role Provided and missing AWS Access Key ID. Returning.."
                )
                self.update_state(state="FAILURE")
                return

        if "AWS_SECRET_ACCESS_KEY" in current_app.config:
            aws_key_secret = current_app.config["AWS_SECRET_ACCESS_KEY"]
        else:
            logger.debug("emailer: Missing AWS Secret Key.")
            if task_credentials is None:
                logger.critical(
                    "emailer: No Role Provided and missing AWS Secret Key.. Returning.."
                )
                self.update_state(state="FAILURE")
                return

        if aws_region is None:
            logger.critical("emailer: Missing AWS Region. Returning...")
            self.update_state(state="FAILURE")
            return

        # TODO - Go back and make the argument a list and update callers.
        recipients = [recipient]

        my_config = Config(
            signature_version="v4",
            region_name=aws_region,
        )

        if task_credentials:
            logger.debug("emailer: Using SES with Assumed Execution Role...")

            ses = boto3.client(
                "ses",
                config=my_config,
                aws_access_key_id=task_credentials["AccessKeyId"],
                aws_secret_access_key=task_credentials["SecretAccessKey"],
            )

        else:
            logger.debug("emailer: Directly using supplied AWS Key ID / Secret...")
            logger.debug("         This should only ever be done in development.")

            ses = boto3.client(
                "ses",
                config=my_config,
                aws_access_key_id=aws_key_id,
                aws_secret_access_key=aws_key_secret,
            )

        try:
            ses.send_email(
                Source=sender,
                Destination={"ToAddresses": recipients},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": text}, "Html": {"Data": html}},
                },
            )
        except ClientError as error:
            logger.error(
                f"Couldn't send email. Here's why: " f"{error.response['Error']['Message']}"
            )
        self.update_state(state="PROGRESS")

    except Exception as error:
        logger.critical(error)
        self.update_state(state="FAILURE")
        return

    self.update_state(state="SUCCESS")
    return {"current": 100, "status": "Task Completed!"}
