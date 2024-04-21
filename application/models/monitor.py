from application.common import constants
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Monitor(PaginatedApi, DATABASE.Model):
    __tablename__ = "monitors"

    monitor_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    agent_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("agents.agent_id"), nullable=False
    )

    monitor_type = DATABASE.Column(
        DATABASE.String(256),
        nullable=False,
        default=constants.monitor_type_to_string(constants.MonitorTypes.NOT_SET),
    )

    last_check = DATABASE.Column(DATABASE.DateTime, nullable=False)
    next_check = DATABASE.Column(DATABASE.DateTime, nullable=False)

    interval = DATABASE.Column(
        DATABASE.Integer, nullable=False, default=constants.DEFAULT_EMAIL_DELAY_SECONDS
    )  # Seconds

    has_fault = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)
