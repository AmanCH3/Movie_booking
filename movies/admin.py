from django.contrib import admin
from .models import Movie , Language , Genre , Show , Screen , Seat

# Register your models here.
admin.site.register(Movie)
admin.site.register(Language)
admin.site.register(Genre)
admin.site.register(Show)
admin.site.register(Screen)
admin.site.register(Seat)

list_display = ['title' , 'release_datetime' , 'language' , 'duration']
list_filter = ['language' , 'genre']
search_fields = ['title' , 'description']

