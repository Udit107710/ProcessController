import uuid
from django.db import models
from django.contrib.auth.models import User


class Process(models.Model):
    STATUS_CHOICES = (
        ('queue', 'In queue'),
        ('processing', 'In progress'),
        ('completed', 'Finished'),
    )

    TRANSFER_TYPE_CHOICES = (
        ('system', 'System'),
        ('url', 'URL')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    completed_at = models.TimeField(null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='queue', null=False)
    address_from = models.SlugField(null=False)
    address_to = models.SlugField(null=False)
    tranfer_type = models.CharField(max_length=100, choices=TRANSFER_TYPE_CHOICES, default='system', null=False)
    other_info = models.JSONField(null=True)
