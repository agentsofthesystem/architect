import boto3

from botocore.config import Config
from botocore.exceptions import ClientError
from flask import current_app

from application.extensions import CELERY
from application.common import logger
from application.common.credentials import get_credentials
from application.common.toolbox import _get_setting
from application.models.default_property import DefaultProperty
from application.models.property import Property
from application.models.setting import SettingsSql
from application.models.user import UserSql

# Docs -
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses/client/send_email.html


def _send_email(
    sender: str,
    subject: str,
    recipients: list,
    html: str = "",
    text: str = "",
    address_mode="ToAddresses",
) -> bool:
    aws_region = None
    setting_objs = None

    try:
        setting_objs = SettingsSql.query.filter_by(category="aws").all()
    except Exception as error:
        logger.critical("Unable to read database settings table.")
        logger.critical(error)
        return False

    if setting_objs is None:
        logger.critical("emailer: Not Settings Objects for AWS category.")
        return False

    try:

        # Region is stored as database item.
        aws_region = _get_setting("AWS_REGION", setting_objs)

        # Get credentials, whether that be Role or User based..
        credentials = get_credentials()

        aws_access_key = credentials["AccessKeyId"]
        aws_secret_key = credentials["SecretAccessKey"]
        aws_session_token = None

        if "Token" in credentials:
            aws_session_token = credentials["Token"]

        my_config = Config(
            signature_version="v4",
            region_name=aws_region,
        )

        ses = boto3.client(
            "ses",
            config=my_config,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            aws_session_token=aws_session_token,
        )

        try:
            ses.send_email(
                Source=sender,
                Destination={address_mode: recipients},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": text}, "Html": {"Data": html}},
                },
            )
        except ClientError as error:
            logger.error(
                f"Couldn't send email. Here's why: " f"{error.response['Error']['Message']}"
            )
            return False

    except Exception as error:
        logger.critical("There was an error")
        logger.critical(error)
        return False

    return True


@CELERY.task(bind=True)
def send_global_email(self, subject: str, html: str):
    # Get sender
    sender = current_app.config["DEFAULT_ADMIN_EMAIL"]

    # Get a list of all user ids that have the NOTIFICATION_EMAIL_GLOBAL_ENABLED property in the
    # Properties table set to False.
    property_id = (
        DefaultProperty.query.filter_by(property_name="NOTIFICATION_EMAIL_GLOBAL_ENABLED")
        .first()
        .default_property_id
    )
    user_ids_opted_out = Property.query.filter_by(
        default_property_id=property_id, property_value="False"
    ).all()
    user_id_list = [user.user_id for user in user_ids_opted_out]

    # Get a list of all user emails that have not turned off global emails.
    users = (
        UserSql.query.filter(UserSql.user_id.notin_(user_id_list))
        .filter(UserSql.email.notin_([sender]))
        .all()
    )
    recipients = [user.email for user in users]

    # Edge case where there is only one user and they have opted out of global emails.
    if len(recipients) == 0:
        logger.info("No users have opted out of global emails.")
        return {"status": "Task Completed!"}

    if _send_email(sender, subject, recipients, html=html, address_mode="BccAddresses"):
        self.update_state(state="SUCCESS")
    else:
        self.update_state(state="FAILURE")

    return {"status": "Task Completed!"}


@CELERY.task(bind=True)
def send_email(self, sender: str, subject: str, recipients: list, html: str = "", text: str = ""):
    if _send_email(sender, subject, recipients, html, text):
        self.update_state(state="SUCCESS")
    else:
        self.update_state(state="FAILURE")

    return {"status": "Task Completed!"}
