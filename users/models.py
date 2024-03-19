import hashlib
import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=130)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


def get_file_upload_path(instance, filename):
    return os.path.join('uploads', str(instance.user.id), filename)


def generate_file_id(filename):
    return hashlib.md5(filename.encode()).hexdigest()[:10]


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_upload_path)
    file_id = models.CharField(max_length=10, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.file_id = generate_file_id(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file.name


class FileAccess(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, default='co-author')

    def __str__(self):
        return f"{self.user.first_name} - {self.type}"
