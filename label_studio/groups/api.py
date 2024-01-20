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
from rest_framework import generics, status,viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from users.models import User

from label_studio.core.permissions import ViewClassPermission, all_permissions
from label_studio.core.utils.params import bool_from_request

logger = logging.getLogger(__name__)

HasObjectPermission = load_func(settings.MEMBER_PERM)

@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Groups'],
        operation_summary='List your groups',
        operation_description="""
        Return a list of the groups you've created or that you have access to.
        """,
    ),
)
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
            groupmember__in=self.request.user.gm_through.filter(deleted_at__isnull=True)
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
        group = generics.get_object_or_404(self.request.user.groups, pk=self.kwargs[self.lookup_field])
        if flag_set('fix_backend_dev_3134_exclude_deactivated_users', self.request.user):
            serializer = GroupsParamsSerializer(data=self.request.GET)
            serializer.is_valid(raise_exception=True)
            active = serializer.validated_data.get('active')

            # return only active users (exclude DISABLED and NOT_ACTIVATED)
            if active:
                return group.active_members.order_by('user__username')

            # group page to show all members
            return group.members.order_by('user__username')
        else:
            return group.members.order_by('user__username')

@method_decorator(
    name='delete',
    decorator=swagger_auto_schema(
        tags=['Groups'],
        operation_summary='Soft delete an group member',
        operation_description='Soft delete a member from the group.',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this group.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be deleted from the group.',
            ),
        ],
        responses={
            204: 'Member deleted successfully.',
            405: 'User cannot soft delete self.',
            404: 'Member not found',
        },
    ),
)
class GroupMemberDetailAPI(GetParentObjectMixin, generics.RetrieveDestroyAPIView):
    permission_required = ViewClassPermission(
        DELETE=all_permissions.groups_change,
    )
    parent_queryset = Group.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_classes = (IsAuthenticated, HasObjectPermission)
    serializer_class = GroupMemberUserSerializer  # Assuming this is the right serializer
    http_method_names = ['delete']

    def delete(self, request, pk=None, user_pk=None):
        group = self.get_parent_object()
        if group != request.user.active_organization:
            raise PermissionDenied('You can delete members only for your current active organization')

        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(GroupMember, user=user, group=group)
        if member.deleted_at is not None:
            raise NotFound('Member not found')

        if member.user_id == request.user.id:
            return Response({'detail': 'User cannot soft delete self'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        member.soft_delete()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Groups'],
        operation_summary=' Get group settings',
        operation_description='Retrieve the settings for a specific group by ID.',
    ),
)
@method_decorator(
    name='patch',
    decorator=swagger_auto_schema(
        tags=['Groups'],
        operation_summary='Update group settings',
        operation_description='Update the settings for a specific group by ID.',
    ),
)
class GroupAPI(generics.RetrieveUpdateAPIView, generics.CreateAPIView):

    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = Group.objects.all()
    permission_required = all_permissions.groups_change
    serializer_class = GroupSerializer

    redirect_route = 'groups-dashboard'
    redirect_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        return super(GroupAPI, self).get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super(GroupAPI, self).patch(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        return super(GroupAPI, self).create(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def put(self, request, *args, **kwargs):
        return super(GroupAPI, self).put(request, *args, **kwargs)

