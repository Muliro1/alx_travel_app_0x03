from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

def build_booking_email(booking):
    subject = f"Booking Confirmation for {booking.listing.title}"
    message = (
        f"Dear {booking.guest.first_name or booking.guest.username},\n\n"
        f"Your booking at {booking.listing.title} from {booking.check_in} to {booking.check_out} has been confirmed.\n"
        f"Total price: {booking.total_price} ETB.\n\nThank you for booking with us!"
    )
    recipient_list = [booking.guest.email]
    return subject, message, recipient_list

@shared_task
def send_booking_confirmation_email(booking_id):
    from .models import Booking  # Import here to avoid circular import
    try:
        booking = Booking.objects.select_related('guest', 'listing').get(id=booking_id)
        subject, message, recipient_list = build_booking_email(booking)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
    except Booking.DoesNotExist:
        pass 
