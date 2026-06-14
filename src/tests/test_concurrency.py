import datetime
import threading
import queue
from django.test import TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import utils as db_utils
from accounts.models import UserRole
from donations.models import Donation, DonationStatus
from donations import services as donations_services

User = get_user_model()

class ClaimConcurrencyTests(TransactionTestCase):
    """
    Rigorously tests simultaneous claims on a single available food item.
    Utilizes TransactionTestCase to preserve atomic database transaction boundaries
    across background worker threads.
    """
    def setUp(self):
        # Create donor
        self.donor = User.objects.create_user(
            username='donor_concurrency',
            password='d0n0r_P@ssw0rd_987',
            role=UserRole.DONOR.value
        )
        
        # Create active food donation
        self.donation = Donation.objects.create(
            donor=self.donor,
            food_item='Confrontation Soup',
            quantity='50 portions',
            expiry_time=timezone.now() + datetime.timedelta(hours=5),
            status=DonationStatus.AVAILABLE,
            address='101 Concurrency Lane'
        )

        # Create 5 verified recipient NGOs
        self.ngos = []
        for i in range(5):
            ngo = User.objects.create_user(
                username=f'ngo_thread_{i}',
                password='d0n0r_P@ssw0rd_987',
                role=UserRole.NGO.value,
                is_verified=True
            )
            self.ngos.append(ngo)

    def test_simultaneous_claims_prevent_double_claiming(self):
        """
        Fires 5 simultaneous claims from 5 different NGOs against 1 food donation.
        Asserts that exactly 1 wins, and the other 4 are safely rejected.
        Supports both row-level locking (MySQL/Postgres) and file-level locking (SQLite).
        """
        results_queue = queue.Queue()
        threads = []

        # Background thread worker
        def claim_worker(ngo_user):
            try:
                donations_services.claim_donation(self.donation.id, ngo_user)
                results_queue.put(('success', ngo_user.username))
            except (ValueError, db_utils.OperationalError) as e:
                # ValueError: Caught status mismatch (MySQL/Postgres row lock blocks and reads updated state)
                # OperationalError: Caught file-lock timeout (SQLite fallback locks the entire db file)
                results_queue.put(('collision', ngo_user.username, str(e)))
            except Exception as e:
                # Capture any other unexpected system crash
                results_queue.put(('error', ngo_user.username, str(e)))

        # Spawn all threads
        for ngo in self.ngos:
            t = threading.Thread(target=claim_worker, args=(ngo,))
            threads.append(t)
            t.start()

        # Wait for threads to execute
        for t in threads:
            t.join()

        # Parse worker outcomes
        successes = []
        collisions = []
        errors = []

        while not results_queue.empty():
            res = results_queue.get()
            if res[0] == 'success':
                successes.append(res)
            elif res[0] == 'collision':
                collisions.append(res)
            else:
                errors.append(res)

        # Verify assertions: exactly 1 wins, 4 get rejected (collided), 0 crash
        self.assertEqual(len(successes), 1, f"Exactly 1 NGO should successfully claim: {successes}")
        self.assertEqual(len(collisions), 4, f"4 NGOs should fail/collide: {collisions}")
        self.assertEqual(len(errors), 0, f"0 unexpected system errors should be thrown: {errors}")

        # Verify DB updates match the winning thread
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.CLAIMED)
        self.assertEqual(self.donation.claimed_by.username, successes[0][1])
