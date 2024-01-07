class GroupMixin:
    @property
    def active_members(self):
        return self.members


class GroupMemberMixin:
    def has_permission(self, user, group):
        # if user.active_group_id == self.group_id:
        #     return True
        # if self.group_id in user.active_group_id:
        #     return True
        if self.group.id == group.id and self.user.id == user.id:
            return True
        return False
