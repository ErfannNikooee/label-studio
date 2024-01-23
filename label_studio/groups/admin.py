# from django.contrib import admin
from django.contrib import admin

# Register your models here.
from groups.models import GroupMember, Group
admin.site.register(Group)
admin.site.register(GroupMember)