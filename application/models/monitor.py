from application.common import constants
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.monitor_attribute import MonitorAttribute
from application.models.monitor_fault import MonitorFault


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

    last_check = DATABASE.Column(DATABASE.DateTime, nullable=True)
    next_check = DATABASE.Column(DATABASE.DateTime, nullable=True)

    task_id = DATABASE.Column(DATABASE.String(256), nullable=True)
    has_fault = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)

    # Useful as a bacref... other property function is used to get all attributes as a dict.
    monitor_attributes = DATABASE.relationship(
        "MonitorAttribute",
        foreign_keys="MonitorAttribute.monitor_id",
        backref="monitor_attributes",
        lazy="dynamic",
    )

    # Useful as a backref... other property function is used to get all attributes as a dict.
    monitor_faults = DATABASE.relationship(
        "MonitorFault",
        foreign_keys="MonitorFault.monitor_id",
        backref="monitor_faults",
        lazy="dynamic",
    )

    @property
    def attributes(self):
        all_attrs = MonitorAttribute.query.filter_by(monitor_id=self.monitor_id).all()
        output_dict = {}
        for attr in all_attrs:
            output_dict[attr.attribute_name] = attr.attribute_value
        return output_dict

    def faults(self, time_format_str=constants.DEFAULT_TIME_FORMAT_STR):
        all_faults = MonitorFault.query.filter_by(monitor_id=self.monitor_id, active=True).all()
        fault_list = []
        count = 1
        for fault in all_faults:
            fault_dict = fault.to_dict()
            fault_time = fault_dict["fault_time"]
            if fault_time is not None:
                fault_dict["fault_time"] = fault_time.strftime(time_format_str)

            fault_dict["name"] = f"Fault #{count}"
            fault_list.append(fault_dict)
            count += 1
        return fault_list

    def to_dict(self):
        return {
            "monitor_id": self.monitor_id,
            "agent_id": self.agent_id,
            "monitor_type": self.monitor_type,
            "last_check": self.last_check,
            "next_check": self.next_check,
            "has_fault": self.has_fault,
            "active": self.active,
        }
