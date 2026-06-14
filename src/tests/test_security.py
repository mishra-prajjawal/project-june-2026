from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserRole
from donations.models import Donation, DonationStatus
import datetime
from django.utils import timezone

User = get_user_model()

class SecurityAuthorizationTests(TestCase):
    """
    Rigorously tests role boundaries, CSRF middleware blocks,
    and admin action authorization gates.
    """
    def setUp(self):
        # Create users
        self.admin = User.objects.create_superuser(
            username='admin_user',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.ADMIN.value
        )
        
        self.donor = User.objects.create_user(
            username='donor_user',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value
        )

        self.ngo = User.objects.create_user(
            username='ngo_user',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )

        self.unverified_ngo = User.objects.create_user(
            username='unverified_ngo_user',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=False
        )

        # Create food donation listing
        self.donation = Donation.objects.create(
            donor=self.donor,
            food_item='Security Burger',
            quantity='10 portions',
            expiry_time=timezone.now() + datetime.timedelta(hours=2),
            status=DonationStatus.AVAILABLE,
            address='Guard Gate'
        )

    def test_non_admin_cannot_access_admin_dashboard(self):
        """
        Verify that donor and NGO users are blocked from loading the admin panel.
        """
        # 1. Donor
        self.client.login(username='donor_user', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('core:admin_panel'))
        self.assertEqual(response.status_code, 403) # returns PermissionDenied (403)
        self.client.logout()

        # 2. NGO
        self.client.login(username='ngo_user', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('core:admin_panel'))
        self.assertEqual(response.status_code, 403)

    def test_donor_cannot_claim_donation(self):
        """
        Verify that a Donor is blocked from posting claims.
        """
        self.client.login(username='donor_user', password='d0n0r_P@ssw0rd_987')
        response = self.client.post(reverse('donations:claim_donation', kwargs={'donation_id': self.donation.id}))
        self.assertEqual(response.status_code, 403)

    def test_unverified_ngo_cannot_claim_donation(self):
        """
        Verify that an unverified NGO view action redirects back with an error message and status is untouched.
        """
        self.client.login(username='unverified_ngo_user', password='d0n0r_P@ssw0rd_987')
        
        # Act
        response = self.client.post(reverse('donations:claim_donation', kwargs={'donation_id': self.donation.id}))
        
        # Assert: Redirects back to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Verify status is still available
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.AVAILABLE)

    def test_admin_cannot_ban_themselves(self):
        """
        Verify that administrators are blocked from toggling self bans.
        """
        self.client.login(username='admin_user', password='d0n0r_P@ssw0rd_987')
        response = self.client.post(reverse('accounts:toggle_ban', kwargs={'user_id': self.admin.id}))
        
        # Assert: Redirects to admin panel
        self.assertEqual(response.status_code, 302)
        
        # Verify admin is not banned
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_banned)

    def test_csrf_protection_enabled_by_default(self):
        """
        Verify that POST requests fail with 403 Forbidden if CSRF token is enforced but missing.
        """
        # Construct a Client that strictly enforces CSRF checks
        csrf_client = Client(enforce_csrf_checks=True)
        
        # Log in the admin user on the CSRF client
        csrf_client.login(username='admin_user', password='d0n0r_P@ssw0rd_987')
        
        # Attempt a POST request without a token
        response = csrf_client.post(
            reverse('accounts:toggle_ban', kwargs={'user_id': self.donor.id})
        )
        self.assertEqual(response.status_code, 403)
