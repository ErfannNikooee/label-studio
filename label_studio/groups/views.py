from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def group_list(request):
    return render(request, 'groups/people_list.html')


@login_required
def simple_view(request):
    return render(request, 'groups/people_list.html')

