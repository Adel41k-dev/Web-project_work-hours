from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    is_employee = models.BooleanField(default=True)

    # 💰 зарплата в час
    hourly_rate = models.FloatField(default=100)


class WorkDay(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def get_hours(self):
        if self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0

    def get_earnings(self):
        return round(self.get_hours() * self.user.hourly_rate, 2)