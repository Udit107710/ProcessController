from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
# Create your views here.
## View to create a process
## Check status
## Start/Pause/Stop a process
## RollBack the db

class ProcessCreateView(APIView, LoginRequiredMixin):
    pass