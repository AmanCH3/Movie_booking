from rest_framework import serializers
from .models import Booking , draftBooking , allUserBookings



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'


class draftBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = draftBooking
        fields = '__all__'

class allUserBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = allUserBookings
        fields = '__all__'

