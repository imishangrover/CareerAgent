from django.db import models
from django.conf import settings  # use this instead of auth.User

class CareerRoadmap(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # FIXED
    career_name = models.CharField(max_length=100)
    roadmap = models.JSONField()
    preferences = models.JSONField(default=dict)
    reference = models.ForeignKey(
        'RoadmapReference', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RoadmapReference(models.Model):
    name = models.CharField(max_length=100, unique=True)
    content = models.JSONField()
    source_url = models.URLField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
