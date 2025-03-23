from django.urls import path , include
from rest_framework.routers import DefaultRouter
from .api import MovieViewSet , ShowViewSet

router = DefaultRouter()
router.register(r'movie' , MovieViewSet , basename="movie")
router.register(r'show' , ShowViewSet , basename="show")

urlpatterns = [
    path("" , include(router.urls)) ,
]