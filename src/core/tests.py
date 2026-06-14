from django.test import TestCase
from django.urls import reverse

class HomeViewTests(TestCase):
    def test_home_page_status_code(self):
        """
        Verify that the landing page renders successfully with 200 OK.
        """
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
