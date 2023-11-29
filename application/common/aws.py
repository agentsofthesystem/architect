import boto3

from botocore.exceptions import ClientError

from application.common import logger


def get_role(role_name):
    """
    Gets a role by name.

    :param role_name: The name of the role to retrieve.
    :return: The specified role.
    """
    role = None
    iam = boto3.resource("iam")

    try:
        role = iam.Role(role_name)
        role.load()  # calls GetRole to load attributes
        logger.info("Got role with arn %s.", role.arn)
    except ClientError:
        logger.exception("Couldn't get role named %s.", role_name)
    else:
        return role


def get_sts_credentials(role):
    """
    Generate a set of temporary credentials.

    :param role: AWS Role Object
    :return: Dictionary of temp creds.
    """
    sts_client = boto3.client("sts")
    credentials = None

    try:
        assumed_role_object = sts_client.assume_role(
            RoleArn=role.arn, RoleSessionName="AssumeRoleSession"
        )
        credentials = assumed_role_object["Credentials"]
    except ClientError:
        logger.exception("Couldn't get credentials with role arn: %s.", role.arn)
    else:
        return credentials
