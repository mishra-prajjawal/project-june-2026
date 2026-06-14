import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from accounts.models import UserRole
from donations.models import Donation, DonationStatus, QualityFeedback

User = get_user_model()

class FoodConnectIntegrationTests(TestCase):
    """
    Simulates the entire platform user flow from end-to-end.
    Journeys: NGO Register -> Admin Verify -> Donor Register -> Post -> Claim -> Collect -> Feedback.
    """
    def test_full_platform_food_donation_lifecycle(self):
        # 1. Register NGO user (starts unverified)
        pdf_file = SimpleUploadedFile("license.pdf", b"NGO License Proof", content_type="application/pdf")
        reg_response = self.client.post(reverse('accounts:register'), {
            'username': 'integration_ngo',
            'password1': 'ngo_P@ssw0rd_987',
            'password2': 'ngo_P@ssw0rd_987',
            'role': UserRole.NGO.value,
            'contact_info': '555-9000',
            'address': 'NGO Main Office',
            'verification_document': pdf_file
        })
        self.assertEqual(reg_response.status_code, 302) # Redirects to login
        
        ngo_user = User.objects.get(username='integration_ngo')
        self.assertEqual(ngo_user.role, UserRole.NGO.value)
        self.assertFalse(ngo_user.is_verified)

        # 2. Register/Setup Admin and log in
        admin_user = User.objects.create_superuser(
            username='integration_admin',
            password='admin_P@ssw0rd_987',
            role=UserRole.ADMIN.value
        )
        self.client.login(username='integration_admin', password='admin_P@ssw0rd_987')

        # 3. Admin verifies NGO
        verify_response = self.client.post(reverse('accounts:verify_ngo', kwargs={'user_id': ngo_user.id}))
        self.assertEqual(verify_response.status_code, 302) # Redirects back to admin dashboard
        
        ngo_user.refresh_from_db()
        self.assertTrue(ngo_user.is_verified)
        self.client.logout()

        # 4. Register Donor user
        donor_reg = self.client.post(reverse('accounts:register'), {
            'username': 'integration_donor',
            'password1': 'donor_P@ssw0rd_987',
            'password2': 'donor_P@ssw0rd_987',
            'role': UserRole.DONOR.value,
            'contact_info': '555-8000',
            'address': 'Gourmet Kitchens Ltd'
        })
        self.assertEqual(donor_reg.status_code, 302)
        
        donor_user = User.objects.get(username='integration_donor')
        self.assertEqual(donor_user.role, UserRole.DONOR.value)
        self.assertTrue(donor_user.is_verified)

        # 5. Log in Donor and Post food donation
        self.client.login(username='integration_donor', password='donor_P@ssw0rd_987')
        post_response = self.client.post(reverse('donations:post_donation'), {
            'food_item': '50 Servings of Hot Pasta',
            'quantity': '50 servings',
            'expiry_time': (timezone.now() + datetime.timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'),
            'address': 'Gourmet Kitchens Back Gate',
            'latitude': 12.9716,
            'longitude': 77.5946
        })
        self.assertEqual(post_response.status_code, 200) # Renders success animated overlay
        self.assertTemplateUsed(post_response, 'donations/post_success.html')
        
        donation = Donation.objects.get(food_item='50 Servings of Hot Pasta')
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)
        self.assertEqual(donation.donor, donor_user)
        self.client.logout()

        # 6. Log in NGO and Claim donation
        self.client.login(username='integration_ngo', password='ngo_P@ssw0rd_987')
        claim_response = self.client.post(reverse('donations:claim_donation', kwargs={'donation_id': donation.id}))
        self.assertEqual(claim_response.status_code, 302) # Redirects to NGO dashboard
        
        donation.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.CLAIMED)
        self.assertEqual(donation.claimed_by, ngo_user)

        # 7. NGO Confirms pickup/collection
        collect_response = self.client.post(reverse('donations:collect_donation', kwargs={'donation_id': donation.id}))
        self.assertEqual(collect_response.status_code, 302) # Redirects to feedback survey page
        self.assertIn(reverse('donations:submit_feedback', kwargs={'donation_id': donation.id}), collect_response.url)
        
        donation.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.COLLECTED)
        self.assertIsNotNone(donation.collected_at)

        # 8. NGO Submits Quality Feedback
        feedback_response = self.client.post(reverse('donations:submit_feedback', kwargs={'donation_id': donation.id}), {
            'acceptable': 'yes'
        })
        self.assertEqual(feedback_response.status_code, 302) # Redirects back to NGO dashboard
        
        # Verify feedback saved
        feedback = QualityFeedback.objects.get(donation=donation)
        self.assertTrue(feedback.acceptable)
        self.assertEqual(feedback.ngo, ngo_user)

        # 9. Verify Donor social impact points incremented: '50 servings' -> awards 50 points
        donor_user.refresh_from_db()
        self.assertEqual(donor_user.impact_score, 50)
        self.client.logout()
