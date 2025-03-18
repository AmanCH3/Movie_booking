from django.contrib import admin
from .models import Booking , draftBooking , allUserBookings
# Register your models here.
admin.site.register(Booking)
admin.site.register(draftBooking)
admin.site.register(allUserBookings)