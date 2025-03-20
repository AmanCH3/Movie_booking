from rest_framework import serializers
from .models import User

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username' , 'email' , 'fullname' , 'balance' , 'is_superuser']


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=True)


class RegisterSerializer(serializers.Serializer):
    fullname = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

class CSRFTokenSerializer(serializers.Serializer):
    csrf_token = serializers.CharField(read_only=True)

class UsernameCheckSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)  
