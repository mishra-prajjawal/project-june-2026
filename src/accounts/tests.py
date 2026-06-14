from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import PermissionDenied
from unittest.mock import Mock

from accounts.models import UserRole
from accounts.forms import FoodConnectRegistrationForm
from accounts import services as accounts_services
from events.signals import ngo_verified, user_banned

User = get_user_model()

class AccountsAuthTests(TestCase):
    def setUp(self):
        # Spies for signals
        self.verified_spy = Mock()
        ngo_verified.connect(self.verified_spy)

        self.banned_spy = Mock()
        user_banned.connect(self.banned_spy)

        self.donor_data = {
            'username': 'testdonor',
            'password1': 'd0n0r_P@ssw0rd_987',
            'password2': 'd0n0r_P@ssw0rd_987',
            'role': UserRole.DONOR.value,
            'contact_info': '555-1111',
            'address': '123 Donor Way'
        }
        
        # Test document file
        self.test_doc = SimpleUploadedFile(
            "cert.pdf", 
            b"NGO Registration Content", 
            content_type="application/pdf"
        )
        
        self.ngo_data = {
            'username': 'testngo',
            'password1': 'd0n0r_P@ssw0rd_987',
            'password2': 'd0n0r_P@ssw0rd_987',
            'role': UserRole.NGO.value,
            'contact_info': '555-2222',
            'address': '456 NGO Boulevard',
            'verification_document': self.test_doc
        }

        # Create an admin user for admin actions testing
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.ADMIN.value
        )
        
        # Create a regular donor to test authorization blocks
        self.regular_donor = User.objects.create_user(
            username='regulardonor',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value
        )

    def test_donor_registration_is_auto_verified(self):
        """
        Verify that registering a Donor succeeds and is auto-verified.
        """
        form = FoodConnectRegistrationForm(data=self.donor_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        
        self.assertEqual(user.role, UserRole.DONOR.value)
        self.assertTrue(user.is_verified)
        self.assertFalse(user.is_banned)
        self.assertTrue(user.check_password('d0n0r_P@ssw0rd_987'))

    def test_ngo_registration_starts_unverified(self):
        """
        Verify that registering an NGO succeeds with document upload, and is unverified by default.
        """
        form = FoodConnectRegistrationForm(
            data=self.ngo_data, 
            files={'verification_document': self.test_doc}
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        
        self.assertEqual(user.role, UserRole.NGO.value)
        self.assertFalse(user.is_verified)
        self.assertTrue(bool(user.verification_document))

    def test_ngo_registration_fails_without_document(self):
        """
        Verify that registering an NGO fails form validation if verification_document is missing.
        """
        data = self.ngo_data.copy()
        del data['verification_document']
        
        form = FoodConnectRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('verification_document', form.errors)

    def test_banned_user_is_logged_out_on_dashboard_access(self):
        """
        Verify that a banned user visiting the dashboard is logged out and redirected to login.
        """
        user = User.objects.create_user(
            username='banneduser',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            is_banned=True
        )
        self.client.login(username='banneduser', password='d0n0r_P@ssw0rd_987')
        
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('login'))
        
        # Verify user is logged out
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_routing_redirects_by_role(self):
        """
        Verify that dashboard router sends users to appropriate stubs based on their role.
        """
        self.client.login(username='adminuser', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('core:admin_panel'))
        self.client.logout()

        self.client.login(username='regulardonor', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('donations:donor_dashboard'))
        self.client.logout()

        ngo_user = User.objects.create_user(
            username='ngouser',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )
        self.client.login(username='ngouser', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('donations:ngo_dashboard'))
        self.client.logout()

    def test_ngo_verification_by_admin_succeeds_and_fires_signal(self):
        """
        Verify that an Admin user can verify an NGO, setting is_verified=True and firing a signal.
        """
        ngo_user = User.objects.create_user(
            username='pendingngo',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=False
        )
        
        # Act
        verified_user = accounts_services.verify_ngo_user(ngo_user.id, self.admin_user)
        
        # Assert
        self.assertTrue(verified_user.is_verified)
        self.assertEqual(self.verified_spy.call_count, 1)
        self.assertEqual(self.verified_spy.call_args[1]['ngo_user'], verified_user)

    def test_ngo_rejection_deletes_ngo(self):
        """
        Verify that rejecting an NGO deletes their registration.
        """
        ngo_user = User.objects.create_user(
            username='badngo',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=False
        )
        
        # Act
        accounts_services.reject_ngo_user(ngo_user.id, self.admin_user)
        
        # Assert
        self.assertFalse(User.objects.filter(id=ngo_user.id).exists())

    def test_toggle_user_ban_fires_signal_on_ban(self):
        """
        Verify that toggling a user ban status works and fires a signal when banned.
        """
        user_to_ban = User.objects.create_user(
            username='spammer',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value
        )
        
        # Ban
        banned_user = accounts_services.toggle_user_ban(user_to_ban.id, self.admin_user)
        self.assertTrue(banned_user.is_banned)
        self.assertEqual(self.banned_spy.call_count, 1)
        self.assertEqual(self.banned_spy.call_args[1]['target_user'], banned_user)
        
        # Unban (should not fire banned signal again)
        unbanned_user = accounts_services.toggle_user_ban(user_to_ban.id, self.admin_user)
        self.assertFalse(unbanned_user.is_banned)
        self.assertEqual(self.banned_spy.call_count, 1)

    def test_non_admin_denied_from_admin_actions(self):
        """
        Verify that a non-admin user cannot invoke verification or ban services.
        """
        ngo_user = User.objects.create_user(
            username='ngo_test',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value
        )
        
        with self.assertRaises(PermissionDenied):
            accounts_services.verify_ngo_user(ngo_user.id, self.regular_donor)

        with self.assertRaises(PermissionDenied):
            accounts_services.toggle_user_ban(ngo_user.id, self.regular_donor)
            
        with self.assertRaises(PermissionDenied):
            accounts_services.reject_ngo_user(ngo_user.id, self.regular_donor)
