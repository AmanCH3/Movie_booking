from rest_framework import serializers
from .models import Movie, Language, Genre, Show, Screen, Seat


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name']

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['name']

class MovieSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()
    genre = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = ['imdb_id', 'title', 'description', 'duration', 'poster', 'backdrop', 'release_datetime', 'imdb_page', 'language', 'genre']

class ScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screen
        fields = ['number', 'layout']

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'type', 'row', 'col', 'state', 'price']

class ShowSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    screen = ScreenSerializer()
    seats = SeatSerializer(many=True)

    class Meta:
        model = Show
        fields = ['id','date_time', 'movie', 'screen', 'base_price', 'seats']

class AddShowSerializer(serializers.Serializer):
    imdb_id = serializers.CharField()
    screen_number = serializers.IntegerField()
    date_time = serializers.DateTimeField()
    base_price = serializers.FloatField()

