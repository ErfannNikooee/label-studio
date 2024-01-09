from collections import OrderedDict

import ujson as json
from drf_dynamic_fields import DynamicFieldsMixin
from groups.models import Group, GroupMember
from rest_framework import serializers
from users.serializers import UserSerializer

class GroupIdSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'contact_info']