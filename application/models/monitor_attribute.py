from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class MonitorAttribute(PaginatedApi, DATABASE.Model):
    __tablename__ = "monitor_attributes"

    monitor_attribute_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    monitor_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("monitors.monitor_id"), nullable=False
    )

    attribute_name = DATABASE.Column(DATABASE.String(256), nullable=False)
    attribute_value = DATABASE.Column(DATABASE.String(256), nullable=False)
