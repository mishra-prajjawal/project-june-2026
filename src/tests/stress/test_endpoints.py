import time
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserRole

User = get_user_model()

class EndpointStressTests(TestCase):
    """
    Measures processing latencies by executing loops of GET queries
    against hot endpoints: home page, donor dashboard, and NGO dashboard.
    """
    def setUp(self):
        # Create test users
        self.donor = User.objects.create_user(
            username='donor_stress',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value,
            impact_score=150
        )
        self.ngo = User.objects.create_user(
            username='ngo_stress',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.NGO.value,
            is_verified=True
        )

    def test_hot_endpoints_performance(self):
        """
        Hits core views 30 times in a loop, records latency profiles, and logs results.
        """
        endpoints = [
            ('Home Page (Leaderboard)', reverse('core:home'), None),
            ('Donor Dashboard', reverse('donations:donor_dashboard'), self.donor),
            ('NGO Dashboard (Feed)', reverse('donations:ngo_dashboard'), self.ngo),
        ]

        iterations = 30
        results = {}

        print("\n\n=== STARTING ENDPOINT STRESS / LATENCY BENCHMARKS ===")
        
        for name, url, auth_user in endpoints:
            if auth_user:
                self.client.login(username=auth_user.username, password='d0n0r_P@ssw0rd_987')

            latencies = []
            for _ in range(iterations):
                start = time.perf_counter()
                response = self.client.get(url)
                end = time.perf_counter()
                
                self.assertEqual(response.status_code, 200)
                latencies.append((end - start) * 1000)  # ms

            if auth_user:
                self.client.logout()

            avg_lat = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            
            results[name] = {
                'min': min_lat,
                'max': max_lat,
                'avg': avg_lat
            }
            
            print(f"Endpoint: {name:<26} | Iterations: {iterations} | Min: {min_lat:5.1f}ms | Max: {max_lat:5.1f}ms | Avg: {avg_lat:5.1f}ms")
            
        print("=====================================================\n")

        # Verify that average latencies are well within the <2s requirement (<2000ms)
        for name, stats in results.items():
            self.assertLess(stats['avg'], 2000.0, f"Average latency for {name} exceeded 2 seconds threshold!")
