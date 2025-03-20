from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from .models import User
from .serializers import (
    UserDetailSerializer,
    SignInSerializer,
    RegisterSerializer,
    CSRFTokenSerializer,
    UsernameCheckSerializer,
)
from .utils import generate_otp_secret, generate_otp, send_otp
import pyotp
import logging

core_logger = logging.getLogger('users')

# Throttling classes
class Anon5PerSecThrottle(AnonRateThrottle):
    rate = '5/second'

class User10PerSecThrottle(UserRateThrottle):
    rate = '10/second'

# User ViewSet
class UserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Allow any user to access these endpoints

    @action(detail=False, methods=['get'], throttle_classes=[Anon5PerSecThrottle])
    def add(self, request):
        a = int(request.query_params.get('a', 0))
        b = int(request.query_params.get('b', 0))
        return Response({"success": True, "message": a + b}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], throttle_classes=[User10PerSecThrottle])
    def user(self, request):
        try:
            serializer = UserDetailSerializer(request.user)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], throttle_classes=[Anon5PerSecThrottle])
    def get_csrf_token(self, request):
        try:
            serializer = CSRFTokenSerializer({'csrf_token': get_token(request)})
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[User10PerSecThrottle])
    def refill_balance(self, request):
        try:
            request.user.balance = 1500
            request.user.save()
            return Response({"success": True, "message": request.user.balance}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], throttle_classes=[Anon5PerSecThrottle])
    def login(self, request):
        try:
            serializer = SignInSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            user = authenticate(request, username=data.get('username'), email=data.get('email'), password=data.get('password'))
            if user:
                login(request, user , email=data.get('email'))
                return Response({"success": True, "message": "Logged in successfully"}, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[User10PerSecThrottle])
    def logout(self, request):
        try:
            logout(request)
            return Response({"success": True, "message": "Logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'])
    def request_otp(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({"success": False, "message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exists():
                return Response({"success": False, "message": "Email is already taken"}, status=status.HTTP_400_BAD_REQUEST)

            otp_secret = generate_otp_secret()
            otp = generate_otp(otp_secret)

            request.session['otp_secret'] = otp_secret
            request.session['otp_email'] = email

            send_otp(email, otp, request.META.get('REMOTE_ADDR'))
            return Response({"success": True, "message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # @action(detail=False, methods=['get'])
    # def check_username(self, request, user_name):
    #     try:
    #         if User.objects.filter(username=user_name).exists():
    #             return Response({"success": False, "message": "taken"}, status=status.HTTP_200_OK)
    #         return Response({"success": True, "message": "Username is available"}, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], throttle_classes=[Anon5PerSecThrottle])
    def register(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            otp_secret = request.session.get('otp_secret')
            otp_email = request.session.get('otp_email')

            if not otp_secret or otp_email != data.get('email'):
                return Response({"success": False, "message": "OTP verification failed"}, status=status.HTTP_400_BAD_REQUEST)

            totp = pyotp.TOTP(otp_secret, interval=300)
            if totp.verify(data.get('otp')):
                User.objects.create_user(
                    fullname=data.get('fullname'),
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password'),
                )
                del request.session['otp_secret']
                del request.session['otp_email']
                return Response({"success": True, "message": "User registered successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)