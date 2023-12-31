from application.common.constants import GroupInviteStates
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class GroupInvites(PaginatedApi, DATABASE.Model):
    __tablename__ = "group_invites"

    group_invite_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    state = DATABASE.Column(
        DATABASE.Integer, nullable=False, default=GroupInviteStates.PENDING.value
    )

    # ID Of group user is inviting user to.
    group_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("groups.group_id"), nullable=False
    )

    # User ID of user being invited
    invite_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    # User ID of user doing the inviting action...
    requestor_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    def to_dict(self):
        return {
            "group_member_id": self.group_invite_id,
            "state": self.state,
            "group_id": self.group_id,
            "invite_id": self.invite_id,
            "requestor_id": self.requestor_id,
        }
