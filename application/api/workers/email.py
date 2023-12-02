import boto3

from botocore.config import Config
from botocore.exceptions import ClientError

from application.extensions import CELERY
from application.common import logger
from application.common.credentials import get_credentials
from application.common.tools import _get_setting
from application.models.setting import SettingsSql


@CELERY.task(bind=True)
def emailer(self, sender: str, subject: str, recipient: str, html: str = "", text: str = ""):
    aws_region = None

    try:
        setting_objs = SettingsSql.query.filter_by(category="aws").all()

        if setting_objs is None:
            logger.critical("emailer: Not Settings Objects for AWS category.")
            self.update_state(state="FAILURE")
            return

        # Region is stored as database item.
        aws_region = _get_setting("AWS_REGION", setting_objs)

        # Get credentials, whether that be Role or User based..
        credentials = get_credentials()

        aws_access_key = credentials["AccessKeyId"]
        aws_secret_key = credentials["SecretAccessKey"]

        # TODO - Go back and make the argument a list and update callers.
        recipients = [recipient]

        my_config = Config(
            signature_version="v4",
            region_name=aws_region,
        )

        ses = boto3.client(
            "ses",
            config=my_config,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
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
    return {"status": "Task Completed!"}
