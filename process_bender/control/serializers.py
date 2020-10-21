from rest_framework import serializers
from control.models import Process

class ProcessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Process
        exclude = []
