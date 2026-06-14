from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import UserRole
from accounts.forms import FoodConnectRegistrationForm

User = get_user_model()

class AccountsAuthTests(TestCase):
    def setUp(self):
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
        # 1. Admin redirects to admin panel
        admin_user = User.objects.create_superuser(
            username='adminuser',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.ADMIN.value
        )
        self.client.login(username='adminuser', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('core:admin_panel'))
        self.client.logout()

        # 2. Donor redirects to donor dashboard
        donor_user = User.objects.create_user(
            username='donoruser',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value
        )
        self.client.login(username='donoruser', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('donations:donor_dashboard'))
        self.client.logout()

        # 3. NGO redirects to NGO dashboard
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
