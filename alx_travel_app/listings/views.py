from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer

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
