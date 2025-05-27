from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seeds the database with sample listings data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        # Create sample users if they don't exist
        users = []
        for i in range(1, 4):
            username = f'host{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123',
                    first_name=f'Host{i}',
                    last_name='User'
                )
                users.append(user)
            else:
                users.append(User.objects.get(username=username))

        # Sample data for listings
        listings_data = [
            {
                'title': 'Cozy Mountain Cabin',
                'description': 'Beautiful cabin with mountain views and modern amenities.',
                'address': '123 Mountain Road',
                'city': 'Denver',
                'state': 'CO',
                'zipcode': '80201',
                'price_per_night': Decimal('199.99'),
                'bedrooms': 2,
                'bathrooms': Decimal('1.5'),
                'max_guests': 4,
                'property_type': 'cabin',
            },
            {
                'title': 'Luxury Beach Villa',
                'description': 'Stunning beachfront villa with private pool and ocean views.',
                'address': '456 Ocean Drive',
                'city': 'Miami',
                'state': 'FL',
                'zipcode': '33101',
                'price_per_night': Decimal('499.99'),
                'bedrooms': 4,
                'bathrooms': Decimal('3.5'),
                'max_guests': 8,
                'property_type': 'villa',
            },
            {
                'title': 'Downtown Apartment',
                'description': 'Modern apartment in the heart of the city.',
                'address': '789 Main Street',
                'city': 'New York',
                'state': 'NY',
                'zipcode': '10001',
                'price_per_night': Decimal('299.99'),
                'bedrooms': 1,
                'bathrooms': Decimal('1.0'),
                'max_guests': 2,
                'property_type': 'apartment',
            },
            {
                'title': 'Family House',
                'description': 'Spacious family home with large backyard.',
                'address': '321 Oak Avenue',
                'city': 'Chicago',
                'state': 'IL',
                'zipcode': '60601',
                'price_per_night': Decimal('349.99'),
                'bedrooms': 3,
                'bathrooms': Decimal('2.0'),
                'max_guests': 6,
                'property_type': 'house',
            },
        ]

        # Create listings
        for listing_data in listings_data:
            # Randomly assign a host
            host = random.choice(users)
            
            # Check if listing already exists
            if not Listing.objects.filter(title=listing_data['title']).exists():
                Listing.objects.create(
                    host=host,
                    **listing_data
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created listing: {listing_data["title"]}')
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
