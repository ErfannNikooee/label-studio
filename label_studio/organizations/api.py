"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import logging

from core.feature_flags import flag_set
from core.mixins import GetParentObjectMixin
from core.utils.common import load_func
from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from organizations.models import Organization, OrganizationMember
from organizations.serializers import (
    OrganizationIdSerializer,
    OrganizationInviteSerializer,
    OrganizationMemberUserSerializer,
    OrganizationSerializer,
    OrganizationsParamsSerializer,
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
from django.http import JsonResponse

from label_studio.core.permissions import ViewClassPermission, all_permissions
from label_studio.core.utils.params import bool_from_request

logger = logging.getLogger(__name__)

HasObjectPermission = load_func(settings.MEMBER_PERM)


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='List your organizations',
        operation_description="""
        Return a list of the organizations you've created or that you have access to.
        """,
    ),
)
class OrganizationListAPI(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_view,
        PUT=all_permissions.organizations_change,
        POST=all_permissions.organizations_create,
        PATCH=all_permissions.organizations_change,
        DELETE=all_permissions.organizations_change,
    )
    serializer_class = OrganizationIdSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(
            organizationmember__in=self.request.user.om_through.filter(deleted_at__isnull=True)
        ).distinct()

    def get(self, request, *args, **kwargs):
        return super(OrganizationListAPI, self).get(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        return super(OrganizationListAPI, self).post(request, *args, **kwargs)


class OrganizationMemberPagination(PageNumberPagination):
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
        tags=['Organizations'],
        operation_summary='Get organization members list',
        operation_description='Retrieve a list of the organization members and their IDs.',
        manual_parameters=[
            openapi.Parameter(
                name='id',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this organization.',
            ),
        ],
    ),
)
class OrganizationMemberListAPI(generics.ListAPIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_view,
        PUT=all_permissions.organizations_change,
        PATCH=all_permissions.organizations_change,
        DELETE=all_permissions.organizations_change,
    )
    serializer_class = OrganizationMemberUserSerializer
    pagination_class = OrganizationMemberPagination

    def get_serializer_context(self):
        return {
            'contributed_to_projects': bool_from_request(self.request.GET, 'contributed_to_projects', False),
            'request': self.request,
        }

    def get_queryset(self):
        org = generics.get_object_or_404(Organization, pk=self.kwargs[self.lookup_field])
        if flag_set('fix_backend_dev_3134_exclude_deactivated_users', self.request.user):
            serializer = OrganizationsParamsSerializer(data=self.request.GET)
            serializer.is_valid(raise_exception=True)
            active = serializer.validated_data.get('active')

            # return only active users (exclude DISABLED and NOT_ACTIVATED)
            if active:
                return org.active_members.order_by('user__username')

            # organization page to show all members
            return org.members.order_by('user__username')
        else:
            return org.members.order_by('user__username')


@method_decorator(
    name='delete',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='Soft delete an organization member',
        operation_description='Soft delete a member from the organization.',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this organization.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be deleted from the organization.',
            ),
        ],
        responses={
            204: 'Member deleted successfully.',
            405: 'User cannot soft delete self.',
            404: 'Member not found',
        },
    ),
)
class OrganizationMemberDetailAPI(GetParentObjectMixin, generics.RetrieveDestroyAPIView):
    permission_required = ViewClassPermission(
        DELETE=all_permissions.organizations_change,
    )
    parent_queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_classes = (IsAuthenticated, HasObjectPermission)
    serializer_class = OrganizationMemberUserSerializer  # Assuming this is the right serializer
    http_method_names = ['delete']

    def delete(self, request, pk=None, user_pk=None):
        org = self.get_parent_object()
        if not org:
            raise NotFound("organization not found")
        # if org != request.user.active_organization:
        #     raise PermissionDenied('You can delete members only for your current active organization')

        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(OrganizationMember, user=user, organization=org)
        om_self = get_object_or_404(OrganizationMember, user=request.user, organization=org)
        if member.deleted_at is not None:
            raise NotFound('Member not found')

        if (not om_self or not om_self.is_admin ) and not user.is_superuser:
            raise PermissionDenied('You can remove members from the organization that you are admin/owner in.')

        if member.user_id == request.user.id:
            return Response({'detail': 'User cannot soft delete self'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        member.soft_delete()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary=' Get organization settings',
        operation_description='Retrieve the settings for a specific organization by ID.',
    ),
)
@method_decorator(
    name='patch',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='Update organization settings',
        operation_description='Update the settings for a specific organization by ID.',
    ),
)
class OrganizationAPI(generics.RetrieveUpdateAPIView):

    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = Organization.objects.all()
    permission_required = all_permissions.organizations_change
    serializer_class = OrganizationSerializer

    redirect_route = 'organizations-dashboard'
    redirect_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).patch(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def put(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).put(request, *args, **kwargs)


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Invites'],
        operation_summary='Get organization invite link',
        operation_description='Get a link to use to invite a new member to an organization in Label Studio Enterprise.',
        responses={200: OrganizationInviteSerializer()},
    ),
)
class OrganizationInviteAPI(generics.RetrieveAPIView):
    parser_classes = (JSONParser,)
    queryset = Organization.objects.all()
    permission_required = all_permissions.organizations_change

    def get(self, request, *args, **kwargs):
        org = request.user.active_organization
        invite_url = '{}?token={}'.format(reverse('user-signup'), org.token)
        if hasattr(settings, 'FORCE_SCRIPT_NAME') and settings.FORCE_SCRIPT_NAME:
            invite_url = invite_url.replace(settings.FORCE_SCRIPT_NAME, '', 1)
        serializer = OrganizationInviteSerializer(data={'invite_url': invite_url, 'token': org.token})
        serializer.is_valid()
        return Response(serializer.data, status=200)


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Invites'],
        operation_summary='Reset organization token',
        operation_description='Reset the token used in the invitation link to invite someone to an organization.',
        responses={200: OrganizationInviteSerializer()},
    ),
)
class OrganizationResetTokenAPI(APIView):
    permission_required = all_permissions.organizations_invite
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        org = request.user.active_organization
        org.reset_token()
        logger.debug(f'New token for organization {org.pk} is {org.token}')
        invite_url = '{}?token={}'.format(reverse('user-signup'), org.token)
        serializer = OrganizationInviteSerializer(data={'invite_url': invite_url, 'token': org.token})
        serializer.is_valid()
        return Response(serializer.data, status=201)


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='Create new organization',
    ),
)
class OrganizationCreateAPI(generics.ListCreateAPIView):

    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = Organization.objects.all()
    permission_required = all_permissions.groups_change
    serializer_class = OrganizationSerializer
    http_method_names = ['post']
    redirect_route = 'organization-list'
    redirect_kwarg = 'pk'

    def create(self, request, *args, **kwargs):
        response = super(OrganizationCreateAPI, self).create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            # Access the created object from the response data
            body = request.data
            created_object = response.data

            om = get_object_or_404(OrganizationMember, user__id=self.request.user.id, organization__id=1)
            om.organization = Organization.objects.get(id=created_object['id'])
            om.admin = True
            om.save()
        return response

@method_decorator(
    name='delete',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='remove user as an admin from the Organization',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this Organization.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be removed as admin.',
            ),
        ],
        responses={
            204: 'admin removed successfully.',
            403: 'Organization not found/no permission',
            404: 'Member not found',
            405: 'User cannot remove self as admin if owner.',

        },
    ),
)
@method_decorator(
    name='put',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='set user as an admin to the Organization',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this Organization.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be set as admin.',
            ),
        ],
        responses={
            204: 'admin removed successfully.',
            403: 'Organization not found/no permission',
            404: 'Member not found',
            405: 'User already owner',

        },
    ),
)
class OrganizationAdminAPI(GetParentObjectMixin, generics.RetrieveDestroyAPIView):
    permission_required = ViewClassPermission(
        DELETE=all_permissions.groups_change,
    )
    parent_queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_classes = (IsAuthenticated, HasObjectPermission)
    serializer_class = OrganizationMemberUserSerializer  # Assuming this is the right serializer
    http_method_names = ['delete','put','get']

    def delete(self, request, pk=None, user_pk=None):
        om = get_object_or_404(OrganizationMember, user__id=user_pk, organization__id=pk)
        om_self = get_object_or_404(OrganizationMember, user__id=self.request.user.id, organization__id=pk)
        if not om:
            raise PermissionDenied("organization not found")
        if (not om_self or not om_self.is_admin) and not user.is_superuser:
            raise PermissionDenied('You can remove admins only in the organizations you are admin/owner in')

        if om.deleted_at is not None:
            raise NotFound('Member not found')

        if om.user.id == request.user.id and om.is_owner:
            return Response({'detail': 'cannot remove  self as admin'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        om.admin = False
        om.save()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests

    def put(self, request, pk=None, user_pk=None):
        om = get_object_or_404(OrganizationMember, user__id=user_pk, organization__id=pk)
        om_self = get_object_or_404(OrganizationMember, user__id=self.request.user.id, organization__id=pk)
        if not om:
            raise PermissionDenied("organization not found")
        if (not om_self or not om_self.is_admin) and not user.is_superuser:
            raise PermissionDenied('You can add admins only in the organizations you are admin/owner in')

        if om.deleted_at is not None:
            raise NotFound('Member not found')

        if om.user.id == request.user.id and om.is_owner:
            return Response({'detail': 'cannot set self as admin'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        om.admin = True
        om.save()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests

@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='add an organization member',
        operation_description='add member to an organization.',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this organization.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be added to the organization.',
            ),
        ],
        responses={
            204: 'Member added successfully.',
            404: 'Member not found'
        },
    ),
)
@method_decorator(
    name='put',
    decorator=swagger_auto_schema(
        tags=['Organizations'],
        operation_summary='change an organization member\'s organization',
        operation_description='change the organization member\'s organization.',
        manual_parameters=[
            openapi.Parameter(
                name='pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying this organization.',
            ),
            openapi.Parameter(
                name='user_pk',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_PATH,
                description='A unique integer value identifying the user to be added to the organization.',
            ),
        ],
        responses={
            204: 'Member added successfully.',
            404: 'Member not found'
        },
    ),
)
class OrganizationMemberAddAPI(GetParentObjectMixin, generics.ListCreateAPIView, generics.RetrieveUpdateAPIView):
    permission_required = ViewClassPermission(
        POST=all_permissions.organizations_create,
    )
    parent_queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_classes = (IsAuthenticated, HasObjectPermission)
    serializer_class = OrganizationMemberUserSerializer  # Assuming this is the right serializer
    http_method_names = ['post','put','get']

    def create(self, request, pk=None, user_pk=None):
        org = self.get_parent_object()
        if not org:
            raise NotFound("organization not found")
        # if org != request.user.active_organization:
        #     raise PermissionDenied('You can delete members only for your current active organization')

        user = get_object_or_404(User, pk=user_pk)
        om_self = get_object_or_404(OrganizationMember, user=request.user, organization=org)
        if user is None:
            raise NotFound('Member not found')
        if (not om_self or not om_self.is_admin) and not user.is_superuser:
            raise PermissionDenied('You can add members to the organization that you are admin/owner in.')
        new_om = OrganizationMember(user=user, organization=org)
        new_om.save()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests
    
    def put(self,request, pk=None, user_pk=None, *args, **kwargs):
        # response = super(OrganizationMemberAddAPI, self).put(request, *args, **kwargs)
        body = request.data

        om = get_object_or_404(OrganizationMember, user__id=user_pk, organization__id=pk)
        om_self = get_object_or_404(OrganizationMember, user__id=self.request.user.id, organization__id=body['id'])
        if not om:
            raise PermissionDenied("organization not found")
        if (not om_self or not om_self.is_admin) and not user.is_superuser:
            raise PermissionDenied('You can add admins only in the organizations you are admin/owner in')

        if om.deleted_at is not None:
            raise NotFound('Member not found')

        if om.user.id == request.user.id and om.is_owner:
            return Response({'detail': 'cannot set self as admin'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        

        org = get_object_or_404(Organization,id=body['id'])
        om.organization = org
        om.save()
        return Response(status=204)

