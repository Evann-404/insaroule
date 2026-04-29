from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from carpool.models import Organization, Location, Vehicle
from carpool.models.ride import Ride
from carpool.models.statistics import OrganizationStatistics
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class OrganizationModelTests(TestCase):
    """Tests for the Organization model and User.get_organization() method"""

    def setUp(self):
        self.org1 = Organization.objects.create(
            name="INSA Rennes", email_domain="insa-rennes.fr"
        )
        self.org2 = Organization.objects.create(
            name="Université de Rennes", email_domain="univ-rennes.fr"
        )

    def test_user_get_organization_success(self):
        """Test that a user can retrieve their organization based on email domain"""
        user = User.objects.create_user(
            username="testuser", email="testuser@insa-rennes.fr", password="testpass123"
        )
        org = user.get_organization()
        self.assertEqual(org, self.org1)

    def test_user_get_organization_not_found(self):
        """Test that get_organization returns None for users without matching organization"""
        user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass123"
        )
        org = user.get_organization()
        self.assertIsNone(org)

    def test_user_organization_property(self):
        """Test that the organization property works"""
        user = User.objects.create_user(
            username="testuser", email="testuser@univ-rennes.fr", password="testpass123"
        )
        self.assertEqual(user.organization, self.org2)


class OrganizationViewTests(TestCase):
    """Tests for organization back-office views"""

    def setUp(self):
        self.client = Client()
        self.org1 = Organization.objects.create(
            name="INSA Rennes", email_domain="insa-rennes.fr"
        )
        self.org2 = Organization.objects.create(
            name="Université de Rennes", email_domain="univ-rennes.fr"
        )

        # Create admin users
        self.admin_insa = User.objects.create_user(
            username="admin_insa",
            email="admin@insa-rennes.fr",
            password="testpass123",
            email_verified=True,
        )
        self.org1.admins.add(self.admin_insa)

        self.admin_univ = User.objects.create_user(
            username="admin_univ",
            email="admin@univ-rennes.fr",
            password="testpass123",
            email_verified=True,
        )
        self.org2.admins.add(self.admin_univ)

        # Create regular users
        self.user_insa = User.objects.create_user(
            username="user_insa",
            email="user@insa-rennes.fr",
            password="testpass123",
            email_verified=True,
        )

    def test_organization_dashboard_requires_login(self):
        """Test that the dashboard requires authentication"""
        response = self.client.get(reverse("carpool:bo_organization_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_organization_dashboard_for_admin(self):
        """Test that admins can access the dashboard"""
        self.client.login(username="admin_insa", password="testpass123")
        response = self.client.get(reverse("carpool:bo_organization_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INSA Rennes")

    def test_organization_dashboard_for_non_admin(self):
        """Test that non-admins cannot access the dashboard"""
        self.client.login(username="user_insa", password="testpass123")
        response = self.client.get(reverse("carpool:bo_organization_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_organization_statistics_requires_admin(self):
        """Test that only admins can view organization statistics"""
        self.client.login(username="user_insa", password="testpass123")
        response = self.client.get(
            reverse("carpool:bo_organization_statistics", args=[self.org1.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_organization_statistics_cross_organization_access(self):
        """Test that admins cannot view other organizations' statistics"""
        self.client.login(username="admin_insa", password="testpass123")
        response = self.client.get(
            reverse("carpool:bo_organization_statistics", args=[self.org2.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_organization_statistics_admin_can_view(self):
        """Test that admins can view their organization's statistics"""
        self.client.login(username="admin_insa", password="testpass123")
        response = self.client.get(
            reverse("carpool:bo_organization_statistics", args=[self.org1.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INSA Rennes")


class OrganizationStatisticsTests(TestCase):
    """Tests for organization statistics calculations"""

    def setUp(self):
        self.org = Organization.objects.create(
            name="INSA Rennes", email_domain="insa-rennes.fr"
        )

        # Create users
        self.driver = User.objects.create_user(
            username="driver",
            email="driver@insa-rennes.fr",
            password="testpass123",
            email_verified=True,
        )
        self.rider1 = User.objects.create_user(
            username="rider1",
            email="rider1@insa-rennes.fr",
            password="testpass123",
            email_verified=True,
        )
        self.rider2 = User.objects.create_user(
            username="rider2",
            email="rider2@insa-rennes.fr",
            password="testpass123",
            email_verified=True,
        )

        # Create locations
        self.loc_start = Location.objects.create(
            fulltext="Start",
            street="Start St",
            zipcode="35000",
            city="Rennes",
            lat=48.1,
            lng=-1.6,
        )
        self.loc_end = Location.objects.create(
            fulltext="End",
            street="End St",
            zipcode="35000",
            city="Rennes",
            lat=48.2,
            lng=-1.5,
        )

        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            name="Test Vehicle", driver=self.driver, seats=5, geqCO2_per_km=120
        )

    def test_organization_statistics_creation(self):
        """Test that organization statistics are created"""
        stats, created = OrganizationStatistics.objects.get_or_create(
            organization=self.org
        )
        self.assertTrue(created)
        self.assertEqual(stats.organization, self.org)

    def test_user_count_per_organization(self):
        """Test counting unique users per organization"""
        insa_users = User.objects.filter(email__endswith="@insa-rennes.fr")
        self.assertEqual(insa_users.count(), 3)

    def test_ride_count_per_organization(self):
        """Test counting rides per organization"""
        now = timezone.now()
        ride = Ride.objects.create(
            driver=self.driver,
            start_loc=self.loc_start,
            end_loc=self.loc_end,
            start_dt=now - timedelta(days=1),
            end_dt=now,
            vehicle=self.vehicle,
            seats_offered=4,
        )
        ride.rider.add(self.rider1, self.rider2)

        org_rides = Ride.objects.filter(driver__email__endswith="@insa-rennes.fr")
        self.assertEqual(org_rides.count(), 1)
