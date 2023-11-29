import boto3

from botocore.config import Config
from botocore.exceptions import ClientError
from flask import current_app

from application.extensions import CELERY
from application.common import logger
from application.common.aws import get_role
from application.common.tools import _get_setting
from application.models.setting import SettingsSql


@CELERY.task(bind=True)
def emailer(self, sender: str, subject: str, recipient: str, html: str = "", text: str = ""):
    aws_region = None
    aws_key_id = None
    aws_key_secret = None
    aws_task_role = None
    aws_task_role_name = None

    try:
        setting_objs = SettingsSql.query.filter_by(category="aws").all()

        if setting_objs is None:
            logger.critical("emailer: Not Settings Objects for AWS category.")
            self.update_state(state="FAILURE")
            return

        # Region is stored as database item.
        aws_region = _get_setting("AWS_REGION", setting_objs)

        if "AWS_TASK_ROLE_NAME" in current_app.config:
            aws_task_role_name = current_app.config["AWS_TASK_ROLE_NAME"]
        else:
            logger.debug("emailer: Missing AWS Task Role Name, but that's okay...")

        # Got a task role name. That means we don't really care if we get that access key or
        # secret, but if we get the name, we must be able to retrieve the role itself.
        if aws_task_role_name:
            aws_task_role = get_role(aws_task_role_name)

        # AWS Key/Secret stored as environment variable / app config object.
        if "AWS_ACCESS_KEY_ID" in current_app.config:
            aws_key_id = current_app.config["AWS_ACCESS_KEY_ID"]
        else:
            logger.debug("emailer: Missing AWS Access Key ID. Returning...")
            if aws_task_role is None:
                logger.critical(
                    "emailer: No Role Provided and missing AWS Access Key ID. Returning.."
                )
                self.update_state(state="FAILURE")
                return

        if "AWS_SECRET_ACCESS_KEY" in current_app.config:
            aws_key_secret = current_app.config["AWS_SECRET_ACCESS_KEY"]
        else:
            logger.debug("emailer: Missing AWS Secret Key.")
            if aws_task_role is None:
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

        if aws_task_role:
            print("BOO")

            logger.debug("emailer: Using SES with Assumed Execution Role...")

            sts_client = boto3.client("sts", config=my_config)

            assumed_role_object = sts_client.assume_role(
                RoleArn=aws_task_role.arn, RoleSessionName="AssumeRoleSession"
            )

            credentials = assumed_role_object["Credentials"]

            ses = boto3.client(
                "ses",
                config=my_config,
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
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
