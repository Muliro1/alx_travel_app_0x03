from rest_framework import serializers
from .models import Listing, Booking
from django.contrib.auth.models import User


class ListingSerializer(serializers.ModelSerializer):
    #host = UserSerializer(read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'address', 'city', 'state',
            'zipcode', 'price_per_night', 'bedrooms', 'bathrooms',
            'max_guests', 'property_type', 'host', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['host', 'created_at', 'updated_at']

class BookingSerializer(serializers.ModelSerializer):
    #guest = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        write_only=True,
        source='listing'
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'guest', 'check_in',
            'check_out', 'total_price', 'status', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['guest', 'total_price', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError("Check-out date must be after check-in date")
        return data
