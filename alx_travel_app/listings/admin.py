from django.contrib import admin
from .models import Listing, Booking, Review

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'city', 'price_per_night', 'property_type', 'is_available')
    list_filter = ('property_type', 'is_available', 'city')
    search_fields = ('title', 'description', 'address', 'city')
    list_editable = ('is_available',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('guest', 'listing', 'check_in', 'check_out', 'total_price', 'status')
    list_filter = ('status', 'check_in', 'check_out')
    search_fields = ('guest__username', 'listing__title')
    date_hierarchy = 'check_in'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'booking__listing__title', 'booking__guest__username')