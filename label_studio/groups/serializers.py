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

class GroupSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class GroupMemberSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ['id', 'organization', 'user']

class UserSerializerWithProjects(UserSerializer):
    created_projects = serializers.SerializerMethodField(read_only=True)
    contributed_to_projects = serializers.SerializerMethodField(read_only=True)

    # def get_created_projects(self, user):
    #     if not self.context.get('contributed_to_projects', False):
    #         return None

    #     current_user = self.context['request'].user
    #     user_group = current_user.objects.get(self.context['request'].group_id)


    #     return user.created_projects.filter(group=user_group).values('id', 'title')

    # def get_contributed_to_projects(self, user):
    #     if not self.context.get('contributed_to_projects', False):
    #         return None

    #     current_user = self.context['request'].user
    #     projects = user.annotations.filter(project__organization=current_user.active_organization).values(
    #         'project__id', 'project__title'
    #     )
    #     contributed_to = [(json.dumps({'id': p['project__id'], 'title': p['project__title']}), 0) for p in projects]
    #     contributed_to = OrderedDict(contributed_to)  # remove duplicates without ordering losing
    #     return [json.loads(key) for key in contributed_to]

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('created_projects', 'contributed_to_projects')

class GroupMemberUserSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Adds all user properties"""

    user = UserSerializerWithProjects()
    group = GroupSerializer()
    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'group']
class GroupsParamsSerializer(serializers.Serializer):
    active = serializers.BooleanField(required=False, default=False)
    contributed_to_projects = serializers.BooleanField(required=False, default=False)