from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import MovieViewSet, ShowViewSet

router = DefaultRouter()
router.register(r'movie', MovieViewSet, basename="movie")
router.register(r'show', ShowViewSet, basename="show")

urlpatterns = [
    path("", include(router.urls)),
    
    # Custom action for getting shows of a movie
    path('movie/<str:imdb_id>/shows/', MovieViewSet.as_view({'get': 'get_movie_shows'}), name='get-movie-shows'),
    
    # Custom action for getting seats of a show
    path('show/<int:show_id>/seats/', ShowViewSet.as_view({'get': 'get_show_seats'}), name='get-show-seats'),
]