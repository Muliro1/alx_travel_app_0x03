from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import os

# Create your views here.

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'city', 'state', 'is_available']
    search_fields = ['title', 'description', 'address', 'city', 'state']
    ordering_fields = ['price_per_night', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('host'):
            queryset = queryset.filter(host=self.request.user)
        return queryset

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'listing']
    ordering_fields = ['check_in', 'check_out', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(guest=user)

    def perform_create(self, serializer):
        booking = serializer.save(guest=self.request.user)
        # Initiate payment with Chapa
        tx_ref = f"booking-{booking.id}-{booking.guest.id}"
        chapa_url = settings.CHAPA_API_URL
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "amount": str(booking.total_price),
            "currency": "ETB",
            "email": booking.guest.email,
            "first_name": booking.guest.first_name or booking.guest.username,
            "last_name": booking.guest.last_name or '',
            "tx_ref": tx_ref,
            "callback_url": self.request.build_absolute_uri('/api/payment/callback/'),
            "return_url": self.request.build_absolute_uri('/payment/thankyou/'),
            "customization[title]": "Booking Payment",
            "customization[description]": f"Payment for booking {booking.id}"
        }
        chapa_response = requests.post(chapa_url, json=data, headers=headers)
        if chapa_response.status_code == 200:
            chapa_data = chapa_response.json()
            transaction_id = chapa_data['data']['tx_ref']
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                status='pending',
                transaction_id=transaction_id
            )
            # Attach payment and checkout_url to booking for response
            booking._payment_checkout_url = chapa_data['data']['checkout_url']
        else:
            # Handle payment initiation failure gracefully
            booking._payment_checkout_url = None

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Attach payment link if available
        if hasattr(self, 'object') and hasattr(self.object, '_payment_checkout_url'):
            response.data['payment_checkout_url'] = self.object._payment_checkout_url
        elif hasattr(self, 'object'):
            response.data['payment_checkout_url'] = None
        return response

class PaymentInitiateView(APIView):
    def post(self, request):
        booking_id = request.data.get('booking_id')
        amount = request.data.get('amount')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        if not all([booking_id, amount, email, first_name, last_name]):
            return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        tx_ref = f"booking-{booking_id}-{booking.guest.id}"
        chapa_url = settings.CHAPA_API_URL
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "amount": str(amount),
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": request.build_absolute_uri('/api/payment/callback/'),
            "return_url": request.build_absolute_uri('/payment/thankyou/'),
            "customization[title]": "Booking Payment",
            "customization[description]": f"Payment for booking {booking_id}"
        }
        chapa_response = requests.post(chapa_url, json=data, headers=headers)
        if chapa_response.status_code == 200:
            chapa_data = chapa_response.json()
            transaction_id = chapa_data['data']['tx_ref']
            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                status='pending',
                transaction_id=transaction_id
            )
            serializer = PaymentSerializer(payment)
            return Response({
                'payment': serializer.data,
                'checkout_url': chapa_data['data']['checkout_url']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Failed to initiate payment with Chapa.'}, status=status.HTTP_502_BAD_GATEWAY)

class PaymentVerifyView(APIView):
    def post(self, request):
        tx_ref = request.data.get('tx_ref')
        if not tx_ref:
            return Response({'error': 'Transaction reference (tx_ref) is required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Find the payment by transaction_id
        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        verify_url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
        }
        chapa_response = requests.get(verify_url, headers=headers)
        if chapa_response.status_code == 200:
            chapa_data = chapa_response.json()
            status_from_chapa = chapa_data.get('data', {}).get('status')
            if status_from_chapa == 'success':
                payment.status = 'completed'
            else:
                payment.status = 'failed'
            payment.save()
            serializer = PaymentSerializer(payment)
            return Response({'payment': serializer.data, 'chapa_response': chapa_data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to verify payment with Chapa.'}, status=status.HTTP_502_BAD_GATEWAY)
