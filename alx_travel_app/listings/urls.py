from django.urls import path, include
from rest_framework import routers
from .views import ListingViewSet, BookingViewSet, PaymentInitiateView, PaymentVerifyView

# Create a router and register our viewsets with it
router = routers.DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('payment/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payment/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('', include(router.urls)),
] 