import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from donations.models import Donation, DonationStatus, Request, QualityFeedback
from accounts.models import UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with test data for FoodConnect development'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        
        # Order matters due to ForeignKey dependencies
        QualityFeedback.objects.all().delete()
        Donation.objects.all().delete()
        Request.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write('Seeding users...')
        
        # 1. Admin
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@foodconnect.org',
            password='password',
            role=UserRole.ADMIN
        )
        self.stdout.write('- Admin user: admin / password')

        # 2. Donors
        donor1 = User.objects.create_user(
            username='donor1',
            email='donor1@gourmet.com',
            password='password',
            role=UserRole.DONOR,
            contact_info='+1 555-0101',
            address='123 Main Street, Downtown',
            impact_score=150
        )
        
        donor2 = User.objects.create_user(
            username='donor2',
            email='donor2@cafecentral.com',
            password='password',
            role=UserRole.DONOR,
            contact_info='+1 555-0102',
            address='456 Elm Street, Midtown',
            impact_score=80
        )
        self.stdout.write('- Donors: donor1 (150 pts), donor2 (80 pts) / password')

        # 3. NGOs
        ngo1 = User.objects.create_user(
            username='ngo1',
            email='ngo1@sheltercare.org',
            password='password',
            role=UserRole.NGO,
            contact_info='+1 555-0201',
            address='789 Oak Street, North End',
            is_verified=True
        )

        ngo2 = User.objects.create_user(
            username='ngo2',
            email='ngo2@hopemission.org',
            password='password',
            role=UserRole.NGO,
            contact_info='+1 555-0202',
            address='321 Pine Street, South End',
            is_verified=False
        )
        self.stdout.write('- NGOs: ngo1 (Verified), ngo2 (Unverified) / password')

        self.stdout.write('Seeding donations...')
        now = timezone.now()

        # Donation 1: Available (Fresh)
        Donation.objects.create(
            donor=donor1,
            food_item='30 Servings of Fried Rice',
            quantity='30 servings',
            expiry_time=now + datetime.timedelta(hours=3),
            status=DonationStatus.AVAILABLE,
            latitude=12.9716,
            longitude=77.5946,
            address='123 Main Street, Downtown'
        )

        # Donation 2: Available (Fresh)
        Donation.objects.create(
            donor=donor2,
            food_item='15 Veg Sandwiches',
            quantity='15 packets',
            expiry_time=now + datetime.timedelta(hours=1),
            status=DonationStatus.AVAILABLE,
            latitude=12.9816,
            longitude=77.6046,
            address='456 Elm Street, Midtown'
        )

        # Donation 3: Available (Expired)
        Donation.objects.create(
            donor=donor1,
            food_item='40 Servings of Chicken Curry (Expired)',
            quantity='40 servings',
            expiry_time=now - datetime.timedelta(hours=2),
            status=DonationStatus.AVAILABLE,
            latitude=12.9716,
            longitude=77.5946,
            address='123 Main Street, Downtown'
        )

        # Donation 4: Claimed
        Donation.objects.create(
            donor=donor1,
            food_item='20 Packs of Pasta',
            quantity='20 servings',
            expiry_time=now + datetime.timedelta(hours=4),
            status=DonationStatus.CLAIMED,
            claimed_by=ngo1,
            latitude=12.9716,
            longitude=77.5946,
            address='123 Main Street, Downtown'
        )

        # Donation 5: Collected
        d5 = Donation.objects.create(
            donor=donor2,
            food_item='50 Loaves of Fresh Bread',
            quantity='50 loaves',
            expiry_time=now + datetime.timedelta(hours=6),
            status=DonationStatus.COLLECTED,
            claimed_by=ngo1,
            latitude=12.9816,
            longitude=77.6046,
            address='456 Elm Street, Midtown',
            collected_at=now - datetime.timedelta(minutes=30)
        )
        
        # Add feedback for collected item
        QualityFeedback.objects.create(
            donation=d5,
            ngo=ngo1,
            acceptable=True
        )

        # NGO Request stub
        Request.objects.create(
            ngo=ngo1,
            description="Need 50 packets of food for Sunday evening shelter run"
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
