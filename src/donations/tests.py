import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from unittest.mock import Mock

from accounts.models import UserRole
from donations.models import Donation, DonationStatus
from donations.forms import DonationPostForm
from events.signals import donation_posted

User = get_user_model()

class DonationsWorkflowTests(TestCase):
    def setUp(self):
        # Setup signals spy
        self.posted_spy = Mock()
        donation_posted.connect(self.posted_spy)

        # Create test users
        self.donor = User.objects.create_user(
            username='donor1',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=50
        )
        
        self.ngo = User.objects.create_user(
            username='ngo1',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )

        self.form_data = {
            'food_item': 'Spaghetti Bolognese',
            'quantity': '20 servings',
            'expiry_time': timezone.now() + datetime.timedelta(hours=4),
            'address': '789 Pasta Road',
            'latitude': 40.7128,
            'longitude': -74.0060
        }

    def test_donation_post_form_valid(self):
        """
        Verify that correct donation values pass form validation.
        """
        form = DonationPostForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_donation_post_form_expired_fails(self):
        """
        Verify that an expiry time in the past fails form validation.
        """
        data = self.form_data.copy()
        data['expiry_time'] = timezone.now() - datetime.timedelta(hours=1)
        
        form = DonationPostForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('expiry_time', form.errors)

    def test_donation_post_form_missing_required_fields_fails(self):
        """
        Verify that missing food item, quantity, or address fails form validation.
        """
        required_fields = ['food_item', 'quantity', 'address']
        for field in required_fields:
            data = self.form_data.copy()
            del data[field]
            form = DonationPostForm(data=data)
            self.assertFalse(form.is_valid(), f"Form should be invalid when {field} is missing")

    def test_post_donation_view_saves_correctly_and_fires_signal(self):
        """
        Verify that a Donor posting a donation succeeds, saves record, and fires donation_posted signal.
        """
        self.client.login(username='donor1', password='d0n0r_P@ssw0rd_987')
        
        # Post request
        response = self.client.post(reverse('donations:post_donation'), data=self.form_data)
        self.assertEqual(response.status_code, 200) # Renders post_success.html
        self.assertTemplateUsed(response, 'donations/post_success.html')

        # Check DB
        donation = Donation.objects.get(food_item='Spaghetti Bolognese')
        self.assertEqual(donation.donor, self.donor)
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)
        self.assertEqual(donation.address, '789 Pasta Road')

        # Verify signal fired
        self.assertEqual(self.posted_spy.call_count, 1)
        self.assertEqual(self.posted_spy.call_args[1]['donation'], donation)

    def test_post_donation_by_non_donor_denied(self):
        """
        Verify that a non-donor (like an NGO) is blocked from posting donations.
        """
        self.client.login(username='ngo1', password='d0n0r_P@ssw0rd_987')
        
        response = self.client.post(reverse('donations:post_donation'), data=self.form_data)
        self.assertEqual(response.status_code, 403) # PermissionDenied returns 403

    def test_donor_dashboard_context_and_leaderboard_rank(self):
        """
        Verify that donor dashboard lists active/past items and computes leaderboard rank.
        """
        # Create another donor to test leaderboard rank sorting
        other_donor = User.objects.create_user(
            username='otherdonor',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=100  # Higher score than donor1 (50)
        )
        
        # Create active donation for self.donor
        Donation.objects.create(
            donor=self.donor,
            food_item='Lasagna',
            quantity='10 servings',
            expiry_time=timezone.now() + datetime.timedelta(hours=2),
            status=DonationStatus.AVAILABLE,
            address='123 Road'
        )

        self.client.login(username='donor1', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('donations:donor_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Leaderboard rank: otherdonor (100) is #1, donor1 (50) is #2
        self.assertEqual(response.context['leaderboard_rank'], 2)
        self.assertEqual(len(response.context['active_donations']), 1)
        self.assertEqual(response.context['active_donations'][0].food_item, 'Lasagna')
