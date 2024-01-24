class GroupMixin:
    @property
    def active_members(self):
        return self.members
        # return self.users


class GroupMemberMixin:
    def has_permission(self, user):
        if user is self.user:
            return True
        # if self.group.id == group.id and self.user.id == user.id:
        #     return True
        return False

