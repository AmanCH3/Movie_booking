from .serializers import BookingSerializer, draftBookingSerializer, allUserBookingSerializer
from .models import Booking, draftBooking, allUserBookings
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from django.core.mail import send_mail
from django.conf import settings
from movies.models import Show, Seat
from movies.serializers import ShowSerializer, SeatSerializer, AddShowSerializer, ScreenSerializer
from django.utils import timezone
from datetime import timedelta
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from bookings import utlis
from django.views.decorators.csrf import csrf_exempt
from movies.models import Movie


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Booking-related operations.
    Supports CRUD operations for Booking and custom actions for user bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access these endpoints

    @action(detail=False, methods=['get'])
    def get_user_bookings(self, request):
        """
        Custom action to retrieve all bookings for the authenticated user.
        """
        try:
            # Fetch all bookings for the current user
            allbookings = allUserBookings.objects.all()
            # Serialize the bookings
            serializer = allUserBookingSerializer(allbookings, many=True)
            return Response({"success": True, "message": "Booking Fetched Succesfully" ,"data" : serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any exceptions and return an error response
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_booking(self, request):
        """
        Custom action to create a draft booking for the authenticated user.
        """
        try:
            # Fetch the show and seats from the request data
            show = Show.objects.get(id=request.data.get('show_id'))
            seats = Seat.objects.filter(uuid__in=request.data.get('seat_uuids', []))
            # Validate if the show and seats exist
            if not show or not seats:
                return Response({"success": False, "message": "Couldn't find show or seats."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if all seats are available
            for seat in seats:
                if seat.state != 'available':
                    return Response({"success": False, "message": "Seat not available"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user already has a pending booking
            if draftBooking.objects.filter(user=request.user).exists():
                return Response({"success": False, "message": "You already have a Pending Booking"}, status=status.HTTP_400_BAD_REQUEST)

            # Create a draft booking
            draft_booking = draftBooking.objects.create(show=show, user=request.user)
            draft_booking.seats.set(seats)

            # Lock the seats
            for seat in seats:
                seat.state = 'locked'
                seat.locked_at = timezone.now()
                seat.save()

            # Serialize and return the draft booking
            serializer = draftBookingSerializer(draft_booking)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle any exceptions and return an error response
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def confirm_booking(self, request, pk=None):
        """
        Custom action to confirm a draft booking and create a final booking.
        """
        try:
            # Fetch the draft booking
            draft_booking = draftBooking.objects.get(id=pk)
            # Validate if the draft booking exists and belongs to the user
            if not draft_booking or draft_booking.user != request.user:
                return Response({"success": False, "message": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            # Fetch the show and seats from the draft booking
            show = draft_booking.show
            seats = draft_booking.seats.all()
            # Calculate the total price
            total_price = sum(seat.price for seat in seats) * show.base_price

            # Check if the user has sufficient balance
            if request.user.balance < total_price:
                return Response({"success": False, "message": "Insufficient Balance"}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct the total price from the user's balance
            request.user.balance -= total_price
            request.user.save()

            # Create the final booking
            booking = Booking.objects.create(show=show, user=request.user, total_amount=total_price)
            booking.seats.set(seats)

            # Mark the seats as booked
            for seat in seats:
                seat.state = 'booked'
                seat.locked_at = None
                seat.save()

            # Create a record in allUserBookings
            allUserBookings.objects.create(
                id=booking.id,
                movie_title=show.movie.title,
                show_date=show.date_time,
                user=request.user,
                total_amount=total_price,
                seats=" ".join(seat.id for seat in seats)
            )

            # Serialize and return the final booking
            serializer = BookingSerializer(booking)
            return Response({"success": True, "message": serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle any exceptions and return an error response
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'])
    def delete_draft_booking(self, request, pk=None):
        """
        Custom action to delete a draft booking and release the locked seats.
        """
        try:
            # Fetch the draft booking
            draft_booking = draftBooking.objects.get(id=pk)
            # Validate if the draft booking belongs to the user
            if draft_booking.user != request.user:
                return Response({"success": False, "message": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            # Release the locked seats
            seats = draft_booking.seats.all()
            for seat in seats:
                seat.state = 'available'
                seat.locked_at = None
                seat.save()

            # Delete the draft booking
            draft_booking.delete()
            return Response({"success": True, "message": "Successfully Deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any exceptions and return an error response
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cancel_booking(self, request, pk=None):
        """
        Custom action to cancel a confirmed booking and issue a partial refund.
        """
        try:
            # Fetch the booking
            booking = Booking.objects.get(id=pk)
            # Validate if the booking belongs to the user
            if booking.user != request.user:
                return Response({"success": False, "message": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            # Check if the booking can still be canceled
            if booking.show.date_time < timezone.now() + timedelta(minutes=20):
                return Response({"success": False, "message": "Too late to cancel"}, status=status.HTTP_400_BAD_REQUEST)

            # Release the booked seats
            seats = booking.seats.all()
            total_price = booking.total_amount
            for seat in seats:
                seat.state = 'available'
                seat.locked_at = None
                seat.save()

            # Delete the booking and its record in allUserBookings
            booking.delete()
            allUserBookings.objects.filter(id=pk).delete()

            # Issue a partial refund (80% of the total price)
            refund_amount = total_price * 0.8
            request.user.balance += refund_amount
            request.user.save()

            return Response({"success": True, "message": f"Refund: {refund_amount}"}, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any exceptions and return an error response
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @csrf_exempt  
    @action(detail=True, methods=['post'])
    def send_tickets(self, request, pk=None):
        try:
            booking = Booking.objects.get(id=pk, user=request.user)

            
            movie = Movie.objects.get(title=booking.show.movie.title, language=booking.show.movie.language)

            seat_ids = [seat.id for seat in booking.seats.all()]

            utlis.send_tickets(
                username=booking.user.username,
                email=booking.user.email,
                booking_id=booking.id,
                movie_title=booking.show.movie.title,
                movie_language=booking.show.movie.language,
                start_time=booking.show.date_time,
                total_price=booking.total_amount,
                seat_ids=seat_ids,
            )

            return Response({"success": True, "message": "Email sent."}, status=200)

        except Booking.DoesNotExist:
            return Response({"success": False, "message": "Booking not found."}, status=404)

        except Movie.DoesNotExist:
            return Response({"success": False, "message": "Movie not found."}, status=404)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)