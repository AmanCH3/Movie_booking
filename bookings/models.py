from django.db import models
import uuid
import string
import secrets
from movies.models import Show , Seat
from users.models import User

# Create your models here.
def generate_id(length = 16):
    character = string.ascii_letters + string.digits
    return ''.join(secrets.choice(character) for _ in range(length))


class Booking(models.Model):
    id  = models.CharField(max_length=16 , primary_key=True ,unique=True , editable=False,  default=generate_id)
    show = models.ForeignKey(Show , on_delete=models.CASCADE)
    user  = models.ForeignKey(User , on_delete=models.CASCADE)
    seats =  models.ManyToManyField(Seat)
    total_amount = models.FloatField()

    def __str__(self):
        return f"{self.id} - {self.show} - {self.user}"

class draftBooking(models.Model):
    id = models.CharField(max_length=16 , primary_key=True ,unique=True , editable=False,  default=generate_id)
    created_at = models.DateTimeField(auto_now_add=True)
    show  = models.ForeignKey(Show , on_delete=models.CASCADE)
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat , on_delete=models.CASCADE)

    def __str__(self):
        return  f"{self.id} - {self.show} - {self.user}"


class allUserBookings(models.Model):
    id = models.CharField(max_length=16 , primary_key=True ,unique=True , editable=False,  default=generate_id)
    movie_title = models.CharField(max_length=100)
    show_date = models.DateTimeField()
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat , on_delete=models.CASCADE)
    total_amount = models.FloatField()  

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.movie_title}"
    

