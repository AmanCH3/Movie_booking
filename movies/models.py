from django.db import models
import uuid

# Create your models here.
class Movie(models.Model):
    imdb_id = models.CharField(max_length=20, unique=True , default=None)
    title = models.CharField(max_length=100 , blank=False , null=False)
    description = models.TextField(blank=False , null=False)
    duration = models.IntegerField(blank=False , null=False)
    poster = models.URLField(max_length=100)
    backdrop = models.URLField(max_length=100)
    release_datetime = models.CharField(max_length=100)
    language = models.ForeignKey('Language', on_delete=models.CASCADE)
    genre = models.ManyToManyField('Genre')
    imdb_page  = models.URLField(max_length=200)


    def __str__(self):
        return self.title

class Language(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name  = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Show(models.Model):
    date_time = models.DateTimeField()
    movie = models.ForeignKey('Movie' , on_delete=models.CASCADE)
    language = models.ForeignKey('Language' , on_delete=models.CASCADE)
    base_price = models.FloatField()

    def __str__(self):
        return str(self.date_time)


class Screen(models.Model):
    number = models.IntegerField(primary_key=True)
    layout = models.JSONField()

    def __str__(self):
        return str(self.number)



class Seat(models.Model):
    STATE_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('locked', 'Locked'),
    ]
    SEAT_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('premium', 'Premium'),
        ('disabled', 'Disabled'),
    ]
    uuid = models.CharField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.CharField(max_length=5)
    type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES, default='standard')
    row = models.CharField(max_length=1)
    col = models.IntegerField()
    show = models.ForeignKey("Show", on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='available')
    price = models.FloatField(default=1)
    #It is business rule in the movie hall that if a seat is disabled, it is booked by default.
    def save(self, *args, **kwargs):
        if self.type == 'disabled':
            self.state = 'booked'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.state}"

