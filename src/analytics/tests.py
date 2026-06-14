import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserRole
from donations.models import Donation, DonationStatus, QualityFeedback

User = get_user_model()

class AnalyticsViewsTests(TestCase):
    def setUp(self):
        # Create test users
        self.donor = User.objects.create_user(
            username='donor1',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=100
        )
        self.ngo = User.objects.create_user(
            username='ngo1',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )

        now = timezone.now()

        # Create 1 collected donation for self.donor
        d1 = Donation.objects.create(
            donor=self.donor,
            food_item='25 servings of curry',
            quantity='25 servings',
            expiry_time=now + datetime.timedelta(hours=2),
            status=DonationStatus.COLLECTED,
            claimed_by=self.ngo,
            address='123 Road',
            collected_at=now - datetime.timedelta(days=1)
        )
        QualityFeedback.objects.create(
            donation=d1,
            ngo=self.ngo,
            acceptable=True
        )

        # Create another collected donation for a different donor
        other_donor = User.objects.create_user(
            username='donor2',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=50
        )
        d2 = Donation.objects.create(
            donor=other_donor,
            food_item='15 packs of sandwiches',
            quantity='15 servings',
            expiry_time=now + datetime.timedelta(hours=3),
            status=DonationStatus.COLLECTED,
            claimed_by=self.ngo,
            address='456 Lane',
            collected_at=now - datetime.timedelta(days=2)
        )
        QualityFeedback.objects.create(
            donation=d2,
            ngo=self.ngo,
            acceptable=False  # rejected feedback
        )

    def test_report_page_anonymous_redirects(self):
        """
        Verify that an unauthenticated user is redirected to the login page.
        """
        response = self.client.get(reverse('analytics:report'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_report_page_context_and_calculation_correctness(self):
        """
        Verify that the analytics report correctly aggregates and processes stats.
        """
        self.client.login(username='donor1', password='d0n0r_P@ssw0rd_987')
        response = self.client.get(reverse('analytics:report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/report.html')

        metrics = response.context['metrics']
        
        # Total servings: 25 (d1) + 15 (d2) = 40
        self.assertEqual(metrics['total_servings'], 40)
        
        # Total kilograms: 40 * 0.3 = 12.0
        self.assertEqual(metrics['total_kgs'], 12.0)
        
        # Total listings saved: 2
        self.assertEqual(metrics['total_listings_saved'], 2)
        
        # Quality rate: 1 accepted (d1) out of 2 = 50.0%
        self.assertEqual(metrics['quality_rate'], 50.0)

        # Personal contribution for donor1: d1 only (25 servings, 1 listing)
        self.assertEqual(metrics['my_listings'], 1)
        self.assertEqual(metrics['my_servings'], 25)

        # Chart datasets
        chart_data = response.context['chart_data']
        self.assertEqual(len(chart_data['labels']), 6)
        self.assertIn(timezone.now().strftime('%b %Y'), chart_data['labels'])
