from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.username
