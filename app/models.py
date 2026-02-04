from django.db import models
from django.contrib.auth.models import AbstractUser


class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class User(AbstractUser):
    permissions = models.JSONField(default=dict, blank=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name='users',
        null=True,
        blank=True
    )
    current_role = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class LevellingGuide(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        related_name='levelling_guides',
        null=True,
        blank=True
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_guides',
        null=True,
        blank=True
    )
    uploaded_file_raw = models.CharField(max_length=255, null=True, blank=True)
    guides_data = models.JSONField(default=dict, blank=True, null=True)
    guides_examples = models.JSONField(default=dict, blank=True, null=True)
    version = models.IntegerField(default=1)
    is_current_version = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        company_name = self.company.name if self.company else "No Company"
        return f"{company_name} - v{self.version}"


class LevellingGuideLog(models.Model):
    levelling_guide = models.ForeignKey(
        LevellingGuide,
        on_delete=models.SET_NULL,
        related_name='logs',
        null=True,
        blank=True
    )
    guide_examples = models.JSONField(default=dict, blank=True, null=True)
    rating = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='guide_logs',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Log for {self.levelling_guide} by {self.updated_by}"
