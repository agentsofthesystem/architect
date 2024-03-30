from datetime import datetime

from application.common import logger
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.message import Messages
from application.models.friend_request import FriendRequests  # noqa: F401
from application.models.default_property import DefaultProperty
from application.models.property import Property


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

    # Track friend requests.
    incoming_friend_requests = DATABASE.relationship(
        "FriendRequests",
        foreign_keys="FriendRequests.recipient_id",
        backref="incoming_friend_requests",
        lazy="dynamic",
    )

    outgoing_friend_requests = DATABASE.relationship(
        "FriendRequests",
        foreign_keys="FriendRequests.sender_id",
        backref="outgoing_friend_requests",
        lazy="dynamic",
    )

    # Tracking a users' friends
    initiated_friends = DATABASE.relationship(
        "Friends",
        foreign_keys="Friends.initiator_id",
        backref="initiated_friends",
        lazy="dynamic",
    )

    received_friends = DATABASE.relationship(
        "Friends",
        foreign_keys="Friends.receiver_id",
        backref="received_friends",
        lazy="dynamic",
    )

    groups = DATABASE.relationship(
        "Groups",
        foreign_keys="Groups.owner_id",
        backref="groups",
        lazy="dynamic",
    )

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

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "active": self.active,
            "authenticated": self.authenticated,
            "admin": self.admin,
            "subscribed": self.subscribed,
            "subscription_id": self.subscription_id,
            "customer_id": self.customer_id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "friend_code": self.friend_code,
        }

    @property
    def is_admin(self):
        return self.admin

    @property
    def properties(self):
        user_properties = (
            DATABASE.session.query(DefaultProperty, Property)
            .join(Property, DefaultProperty.default_property_id == Property.default_property_id)
            .filter_by(user_id=self.user_id)
            .all()
        )
        output_dict = {}
        for property in user_properties:
            if property[0].property_type == "bool":
                value = False if property[1].property_value.lower() == "false" else True
            elif property[0].property_type == "int":
                value = int(property[1].property_value)
            elif property[0].property_type == "str":
                value = str(property[1].property_value)
            elif property[0].property_type == "float":
                value = float(property[1].property_value)
            else:
                logger.warning(f"Unknown property type: {property[0].property_type}")
                value = property[1].property_value

            output_dict[property[0].property_name] = value

        return output_dict
