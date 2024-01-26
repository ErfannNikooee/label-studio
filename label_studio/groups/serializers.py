from collections import OrderedDict

import ujson as json
from drf_dynamic_fields import DynamicFieldsMixin
from groups.models import Group, GroupMember
from rest_framework import serializers
from users.serializers import UserSerializer
from organizations.serializers import UserSerializerWithProjects
class GroupIdSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'contact_info']

class GroupSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class GroupMemberSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user']
class GroupMemberUserSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Adds all user properties"""

    user = UserSerializerWithProjects()
    group = GroupSerializer()
    class Meta:
        model = GroupMember
        fields = "__all__"
class GroupsParamsSerializer(serializers.Serializer):
    active = serializers.BooleanField(required=False, default=False)
    contributed_to_projects = serializers.BooleanField(required=False, default=False)