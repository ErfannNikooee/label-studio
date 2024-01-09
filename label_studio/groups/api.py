import logging

from core.feature_flags import flag_set
from core.mixins import GetParentObjectMixin
from core.utils.common import load_func
from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from groups.models import Group, GroupMember
from groups.serializers import (
    GroupIdSerializer,
    GroupMemberUserSerializer,
    GroupSerializer,
    GroupsParamsSerializer,
)
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from label_studio.core.permissions import ViewClassPermission, all_permissions
from label_studio.core.utils.params import bool_from_request

class GroupListAPI(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.groups_view,
        PUT=all_permissions.groups_change,
        POST=all_permissions.groups_create,
        PATCH=all_permissions.groups_change,
        DELETE=all_permissions.groups_change,
    )
    serializer_class = GroupIdSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(
            groupmember__in=self.request.user.om_through.filter(deleted_at__isnull=True)
        ).distinct()

    def get(self, request, *args, **kwargs):
        return super(GroupListAPI, self).get(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        return super(GroupListAPI, self).post(request, *args, **kwargs)

class GroupMemberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        # emulate "unlimited" page_size
        if (
            self.page_size_query_param in request.query_params
            and request.query_params[self.page_size_query_param] == '-1'
        ):
            return 1000000
        return super().get_page_size(request)
    
@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Groups'],
        operation_summary='Get group members list',
        operation_description='Retrieve a list of the group members and their IDs.',
        manual_parameters=[
            openapi.Parameter(
                name='id',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this group.',
            ),
        ],
    ),
)
class GroupMemberListAPI(generics.ListAPIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.groups_view,
        PUT=all_permissions.groups_change,
        PATCH=all_permissions.groups_change,
        DELETE=all_permissions.groups_change,
    )
    serializer_class = GroupMemberUserSerializer
    pagination_class = GroupMemberPagination

    def get_serializer_context(self):
        return {
            'contributed_to_projects': bool_from_request(self.request.GET, 'contributed_to_projects', False),
            'request': self.request,
        }

    def get_queryset(self):
        org = generics.get_object_or_404(self.request.user.organizations, pk=self.kwargs[self.lookup_field])
        if flag_set('fix_backend_dev_3134_exclude_deactivated_users', self.request.user):
            serializer = GroupsParamsSerializer(data=self.request.GET)
            serializer.is_valid(raise_exception=True)
            active = serializer.validated_data.get('active')

            # return only active users (exclude DISABLED and NOT_ACTIVATED)
            if active:
                return org.active_members.order_by('user__username')

            # organization page to show all members
            return org.members.order_by('user__username')
        else:
            return org.members.order_by('user__username')

