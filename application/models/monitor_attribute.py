from flask_admin.contrib.sqla import ModelView

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

    def to_dict(self):
        return {
            "monitor_attribute_id": self.monitor_attribute_id,
            "monitor_id": self.monitor_id,
            "attribute_name": self.attribute_name,
            "attribute_value": self.attribute_value,
        }


class MonitorAttrView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = MonitorAttribute.__table__.columns.keys()
