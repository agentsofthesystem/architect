import boto3

from botocore.config import Config

from application.extensions import CELERY
from application.common import logger
from application.common.tools import _get_setting
from application.models.setting import SettingsSql


@CELERY.task(bind=True)
def emailer(self, sender, subject, recipient, html="", text=""):
    try:
        setting_objs = SettingsSql.query.filter_by(category="email").all()

        if setting_objs is None:
            logger.critical("emailer: Not Settings Objects for email category.")
            self.update_state(state="FAILURE")
            return

        aws_region = _get_setting("AWS_REGION", setting_objs)
        aws_key_id = _get_setting("AWS_ACCESS_KEY_ID", setting_objs)
        aws_key_secret = _get_setting("AWS_SECRET_ACCESS_KEY", setting_objs)

        if aws_region is None or aws_key_id is None or aws_key_secret is None:
            logger.critical("emailer: One of the required settings was not found.")
            self.update_state(state="FAILURE")
            return

        recipients = [recipient]

        my_config = Config(
            signature_version="v4",
            region_name=aws_region,
        )

        ses = boto3.client(
            "ses",
            config=my_config,
            aws_access_key_id=aws_key_id,
            aws_secret_access_key=aws_key_secret,
        )

        ses.send_email(
            Source=sender,
            Destination={"ToAddresses": recipients},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": text}, "Html": {"Data": html}},
            },
        )

        self.update_state(state="PROGRESS")

    except Exception as error:
        logger.critical(error)
        self.update_state(state="FAILURE")
        return

    self.update_state(state="SUCCESS")
    return {"current": 100, "status": "Task Completed!"}
