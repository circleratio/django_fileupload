from django.db import models
from django.utils import timezone

class Workflow(models.Model):
    owner = models.CharField(max_length=200)

    files = models.CharField(max_length=1000)

