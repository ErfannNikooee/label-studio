import logging

from core.utils.common import create_hash, load_func
from django.conf import settings
from django.db import models, transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

GroupMemberMixin = load_func(settings.GROUP_MEMBER_MIXIN)

class GroupMember(GroupMemberMixin, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete = models.CASCADE, related_name='gm_user', help_text='User ID'
        )
    
    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, help_text='Group ID'
    )

    owner = models.BooleanField(default=False, editable=False)
    admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    deleted_at = models.DateTimeField(
        _('deleted at'),
        default=None,
        null=True,
        blank=True,
        db_index=True,
        help_text='Timestamp indicating when the group member was marked as deleted.  '
        'If NULL, the member is not considered deleted.',
    )

    @property
    def is_owner(self):
        return self.is_owner or (self.user.id == self.group.created_by.id)
    @property
    def is_admin(self):
        return self.is_owner or self.admin

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"user {self.user.email} group {self.group.name}"

    class Meta:
        ordering = ['pk']

GroupMixin = load_func(settings.GROUP_MIXIN)
class Group(GroupMixin, models.Model):
    name = models.CharField(_('group name'),max_length=500, null=False)

    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members', through=GroupMember)

    description = models.TextField(
        _('description'), blank=True, null=True, default='', help_text='Project description'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        verbose_name=_('created_by'),)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    contact_info = models.EmailField(_('contact info'), blank=True, null=True)

    class Meta:
        ordering = ['pk']

    @classmethod
    def create_group(cls, name,created_by):
        _create_group = load_func(settings.CREATE_GROUP)
        return _create_group(name=name, created_by=created_by)
    
    def has_user(self, user):
        return self.users.filter(pk=user.pk).exists()

    def has_deleted(self, user):
        return GroupMember.objects.filter(user=user, group=self, deleted_at__isnull=False).exists()
    
    def has_permission(self, user):
        return GroupMember.objects.filter(user=user, group=self, deleted_at__isnull=True).exists()

    def add_user(self, user):
        if self.users.filter(pk=user.pk).exists():
            logger.debug('User already exists in group.')
            return

        with transaction.atomic():
            gm = GroupMember(user=user, group=self)
            gm.save()

            return gm

    def remove_user(self, user):
        GroupMember.objects.filter(user=user, group=self).delete()

    def __str__(self):
        return f"Group {self.id} | {self.name}"