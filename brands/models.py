from django.db import models
from django.contrib.auth.models import User


class Brand(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="brands",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, default="Cosmetics")
    description = models.TextField(blank=True)
    interview_data = models.JSONField(default=list, blank=True)
    strategy_report = models.TextField(blank=True, default="")
    strategy_data = models.JSONField(default=dict, blank=True)
    report_mode = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
# Create your models here.
