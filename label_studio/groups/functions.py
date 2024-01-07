from core.utils.common import temporary_disconnect_all_signals
from django.db import transaction
from groups.models import Group, GroupMember
from projects.models import Project


def create_group(name, created_by):
    with transaction.atomic():
        group = Group.objects.create(name=name, created_by=created_by)
        GroupMember.objects.create(user=created_by, group=group)
        return group


def destroy_group(group):
    with temporary_disconnect_all_signals():
        Project.objects.filter(group=group).delete()
        if hasattr(group, 'saml'):
            group.saml.delete()
        group.delete()
