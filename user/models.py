from django.db import models
from django.contrib.auth.models import User
from .constants import USER_TYPE


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    # image = models.ImageField(upload_to='user_images')
    # image_url = models.URLField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15)
    user_type = models.CharField(max_length=20, choices=USER_TYPE)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
