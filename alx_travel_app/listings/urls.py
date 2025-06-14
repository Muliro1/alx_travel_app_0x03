from django.urls import path, include
from rest_framework import routers
from .views import ListingViewSet, BookingViewSet

# Create a router and register our viewsets with it
router = routers.DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
] 