from django.urls import include, path
from groups import  api, views

app_name = 'groups'

_urlpatterns = [
    path('',views.group_list, name='group-index')
]

_api_urlpattens = [
    path('', api.GroupListAPI.as_view(), name='group-list'),
    path('<int:pk>', api.GroupAPI.as_view(), name='group-detail'),
    path('<int:pk>/memberships', api.GroupMemberListAPI.as_view(), name='group-memberships-list'),
    path(
        '<int:pk>/memberships/<int:user_pk>/',
        api.GroupMemberDetailAPI.as_view(),
        name='group-membership-detail',
    ),
]

urlpatterns = [
    path('group/', views.simple_view, name='group-simple'),
    path('group/webhooks', views.simple_view, name='group-simple-webhooks'),
    path('members/', include(_urlpatterns)),
    path('api/group/', include((_api_urlpattens, app_name), namespace='api')),
    path('api/newgroup/',api.GroupAPI,name='creategroup' )
    # # invite
    # path('api/invite', api.OrganizationInviteAPI.as_view(), name='organization-invite'),
    # path('api/invite/reset-token', api.OrganizationResetTokenAPI.as_view(), name='organization-reset-token'),
]