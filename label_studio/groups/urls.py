from django.urls import include, path
from groups import  views

app_name = 'groups'

urlpatterns = [
    path('group/',views.index, name='group-view')
]
