from datetime import datetime

from application.common import logger
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.message import Messages


class UserSql(PaginatedApi, DATABASE.Model):
    __tablename__ = "users"

    user_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # User Login Stuff
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)
    authenticated = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)

    # Special Stuff
    admin = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)
    verified = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)

    # Payments
    subscribed = DATABASE.Column(
        DATABASE.Boolean, nullable=False, default=False
    )  # For paying users.
    subscription_id = DATABASE.Column(DATABASE.String(256), nullable=True)
    customer_id = DATABASE.Column(DATABASE.String(256), nullable=True)

    # Identifying features
    username = DATABASE.Column(DATABASE.String(256), nullable=True)
    email = DATABASE.Column(DATABASE.String(256), unique=True, nullable=False)
    password = DATABASE.Column(DATABASE.String(256), nullable=False)
    first_name = DATABASE.Column(DATABASE.String(256), nullable=True)
    last_name = DATABASE.Column(DATABASE.String(256), nullable=True)

    # Friends
    friend_code = DATABASE.Column(DATABASE.String(256), nullable=True)

    # Designate User Relationship Back-refs
    messages_sent = DATABASE.relationship(
        "Messages", foreign_keys="Messages.sender_id", backref="author", lazy="dynamic"
    )
    messages_received = DATABASE.relationship(
        "Messages",
        foreign_keys="Messages.recipient_id",
        backref="recipient",
        lazy="dynamic",
    )

    agents = DATABASE.relationship(
        "Agents",
        foreign_keys="Agents.owner_id",
        backref="agents",
        lazy="dynamic",
    )

    # To track sharing - TODO - Will need an intermediate table for each.
    # Friend to Agent (Direct)
    # Group to Agent

    # friends = DATABASE.relationship(
    #     "Friends",
    #     foreign_keys="Friends.friend_id",
    #     backref="friends",
    #     lazy="dynamic",
    # )

    # groups = DATABASE.relationship(
    #     "Groups",
    #     foreign_keys="Groups.group_id",
    #     backref="groups",
    #     lazy="dynamic",
    # )

    last_message_read_time = DATABASE.Column(DATABASE.DateTime, nullable=True)

    def __str__(self):
        user_str = f"\n************************ User: {self.user_id} ************************ \n"
        user_str += f" Admin: {self.admin}, Verified: {self.verified}, subscribed: {self.subscribed} \n"  # noqa: E501
        user_str += f" First: {self.first_name}, Last: {self.last_name} \n"
        user_str += f" Username: {self.username}, email: {self.email} \n"
        user_str += "******************************************************************************** \n"  # noqa: E501

        return user_str

    def __unicode__(self):
        return self.username

    def get_id(self):
        logger.debug(f"Called get_id: ID IS: {self.user_id}")
        return str(self.user_id)

    def is_active(self):
        return self.active

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def new_direct_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Messages.query.filter_by(recipient=self)
            .filter(Messages.timestamp > last_read_time)
            .count()
        )

    def new_global_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Messages.query.filter_by(is_global=True)
            .filter(Messages.timestamp > last_read_time)
            .count()
        )

    @property
    def is_admin(self):
        return self.admin
