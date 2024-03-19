from rest_framework import serializers
from .models import File, FileAccess


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['user', 'file', 'uploaded_at']


class FileAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAccess
        fields = ['first_name', 'email', 'type']
