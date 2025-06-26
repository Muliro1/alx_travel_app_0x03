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
        serializer.save(guest=self.request.user)

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
