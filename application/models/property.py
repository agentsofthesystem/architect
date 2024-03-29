from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Property(PaginatedApi, DATABASE.Model):
    __tablename__ = "properties"

    property_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    property_value = DATABASE.Column(DATABASE.String(256), nullable=False)

    user_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    default_property_id = DATABASE.Column(
        DATABASE.Integer,
        DATABASE.ForeignKey("default_properties.default_property_id"),
        nullable=False,
    )
