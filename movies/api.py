from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.utils import timezone
from datetime import timedelta
from .models import Movie, Language, Genre, Show, Screen, Seat
from .serializers import MovieSerializer, ShowSerializer, ScreenSerializer, AddShowSerializer , SeatSerializer
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.permissions import IsAuthenticated , IsAdminUser
import logging


"""
Difference Between Viewset and ModelViewSet Can vary by the usecase
the main difference is that ModelViewSet is used when you want to perform 
CRUD operations on a model(admin) and ViewSet(Customer) is used when you want to perform custom operations on a model.

"""
movie_logger = logging.getLogger('movie')

class MovieViewSet(viewsets.ViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @action(detail=False, methods=['get'])
    def list_movies(self, request):
        try:
            movies = Movie.objects.all()
            serializer = MovieSerializer(movies, many=True)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_movie_shows(self, request, imdb_id=None):
        try:
            movie = Movie.objects.get(imdb_id=imdb_id)
            shows = Show.objects.filter(movie=movie)
            serializer = ShowSerializer(shows, many=True)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def add_movie(self, request):
        permission_classes = [IsAdminUser]
        try:
            serializer = MovieSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'])
    def delete_movie(self, request, imdb_id=None):
        permission_classes = [IsAdminUser]
        try:
            movie = Movie.objects.filter(imdb_id=imdb_id)
            if movie.exists():
                movie.delete()
                return Response({"success": True, "message": "Movie deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShowViewSet(viewsets.ViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @action(detail=False, methods=['get'])
    def get_show_seats(self, request, show_id=None):
        try:
            show = Show.objects.get(id=show_id)
            seats = Seat.objects.filter(show=show)
            serializer = SeatSerializer(seats, many=True)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def add_show(self, request):
        permission_classes = [IsAdminUser]
        try:
            serializer = AddShowSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                movie = Movie.objects.get(imdb_id=data['imdb_id'])
                screen = Screen.objects.get(number=data['screen_number'])

                if data['date_time'] < timezone.now():
                    return Response({"success": False, "message": "Show time is in the past."}, status=status.HTTP_400_BAD_REQUEST)

                overlapping_shows = Show.objects.filter (
                    screen__number=data['screen_number'],
                    date_time__range=(data['date_time'] - timedelta(minutes=180), data['date_time'] + timedelta(minutes=180)))
                if overlapping_shows.exists():
                    return Response({"success": False, "message": "This show overlaps with another show."}, status=status.HTTP_400_BAD_REQUEST)

                show = Show.objects.create(
                    date_time=data['date_time'],
                    movie=movie,
                    screen=screen,
                    base_price=data['base_price']
                )
                return Response({"success": True, "message": ShowSerializer(show).data}, status=status.HTTP_201_CREATED)
            return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'])
    def delete_show(self, request, show_id=None):
        permission_classes = [IsAdminUser]
        try:
            show = Show.objects.get(id=show_id)
            show.delete()
            return Response({"success": True, "message": "Show deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)