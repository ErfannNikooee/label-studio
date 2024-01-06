class GroupMixin:
    @property
    def active_members(self):
        return self.members


class GroupMemberMixin:
    def has_permission(self, user):
        # if user.active_group_id == self.group_id:
        #     return True
        if self.group_id in user.active_group_id:
            return True
        return False
