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
from donations import services as donations_services
from events.signals import donation_posted, donation_claimed

User = get_user_model()

class DonationsWorkflowTests(TestCase):
    def setUp(self):
        # Setup signals spy
        self.posted_spy = Mock()
        donation_posted.connect(self.posted_spy)

        self.claimed_spy = Mock()
        donation_claimed.connect(self.claimed_spy)

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

        self.unverified_ngo = User.objects.create_user(
            username='unverifiedngo',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=False
        )

        self.banned_ngo = User.objects.create_user(
            username='bannedngo',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True,
            is_banned=True
        )

        # Create base test donation
        self.donation = Donation.objects.create(
            donor=self.donor,
            food_item='Lasagna',
            quantity='20 servings',
            expiry_time=timezone.now() + datetime.timedelta(hours=4),
            status=DonationStatus.AVAILABLE,
            address='789 Pasta Road'
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
        
        response = self.client.post(reverse('donations:post_donation'), data=self.form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'donations/post_success.html')

        donation = Donation.objects.get(food_item='Spaghetti Bolognese')
        self.assertEqual(donation.donor, self.donor)
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)

        self.assertEqual(self.posted_spy.call_count, 1)

    def test_post_donation_by_non_donor_denied(self):
        """
        Verify that a non-donor (like an NGO) is blocked from posting donations.
        """
        self.client.login(username='ngo1', password='d0n0r_P@ssw0rd_987')
        response = self.client.post(reverse('donations:post_donation'), data=self.form_data)
        self.assertEqual(response.status_code, 403)

    def test_donor_dashboard_context_and_leaderboard_rank(self):
        """
        Verify that donor dashboard lists active/past items and computes leaderboard rank.
        """
        other_donor = User.objects.create_user(
            username='otherdonor',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=100
        )
        
        self.client.login(username='donor1', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('donations:donor_dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['leaderboard_rank'], 2)
        self.assertEqual(len(response.context['active_donations']), 1)

    def test_claim_donation_success_and_fires_signal(self):
        """
        Verify that a verified NGO can successfully claim an available donation,
        setting state to Claimed and emitting a signal.
        """
        claimed = donations_services.claim_donation(self.donation.id, self.ngo)
        
        self.assertEqual(claimed.status, DonationStatus.CLAIMED)
        self.assertEqual(claimed.claimed_by, self.ngo)
        
        self.assertEqual(self.claimed_spy.call_count, 1)
        self.assertEqual(self.claimed_spy.call_args[1]['donation'], claimed)

    def test_claim_donation_already_claimed_fails(self):
        """
        Verify that claiming an already claimed donation fails with ValueError (concurrency safety).
        """
        # Claim it first
        donations_services.claim_donation(self.donation.id, self.ngo)
        
        # Try claiming again
        other_ngo = User.objects.create_user(
            username='otherngo',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )
        with self.assertRaises(ValueError):
            donations_services.claim_donation(self.donation.id, other_ngo)

    def test_claim_donation_expired_fails(self):
        """
        Verify that claiming an expired donation fails.
        """
        expired_donation = Donation.objects.create(
            donor=self.donor,
            food_item='Old bread',
            quantity='5 loaves',
            expiry_time=timezone.now() - datetime.timedelta(hours=1),
            status=DonationStatus.AVAILABLE,
            address='123 Road'
        )
        with self.assertRaises(ValueError):
            donations_services.claim_donation(expired_donation.id, self.ngo)

    def test_claim_donation_unverified_ngo_fails(self):
        """
        Verify that an unverified NGO is blocked from claiming.
        """
        with self.assertRaises(PermissionDenied):
            donations_services.claim_donation(self.donation.id, self.unverified_ngo)

    def test_claim_donation_banned_ngo_fails(self):
        """
        Verify that a banned NGO is blocked from claiming.
        """
        with self.assertRaises(PermissionDenied):
            donations_services.claim_donation(self.donation.id, self.banned_ngo)
