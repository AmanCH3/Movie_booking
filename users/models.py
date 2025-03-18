from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fullname = models.CharField(max_length=100 , blank=False , null=False)
    email = models.EmailField(unique=True , blank=False , null=False) 
    balance = models.IntegerField(default=1500)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
    
    
