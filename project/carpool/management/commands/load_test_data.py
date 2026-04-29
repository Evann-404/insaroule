from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from carpool.models import Location, Vehicle, Organization
from carpool.models.ride import Ride
from carpool.models.statistics import OrganizationStatistics

User = get_user_model()


class Command(BaseCommand):
    help = "Load test data for organizations and rides"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating test data..."))

        # Create organizations
        org1, _ = Organization.objects.get_or_create(
            name="INSA Rennes", defaults={"email_domain": "insa-rennes.fr"}
        )
        org2, _ = Organization.objects.get_or_create(
            name="Université de Rennes", defaults={"email_domain": "univ-rennes.fr"}
        )
        org3, _ = Organization.objects.get_or_create(
            name="École Polytechnique",
            defaults={"email_domain": "polytechnique.edu.fr"},
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Created {3} organizations"))

        # Create test users for each organization
        users_data = [
            # INSA Rennes admins
            ("admin_insa", "admin_insa@insa-rennes.fr", org1),
            ("contact_insa", "contact_insa@insa-rennes.fr", org1),
            # INSA Rennes regular users
            ("user1_insa", "user1@insa-rennes.fr", org1),
            ("user2_insa", "user2@insa-rennes.fr", org1),
            ("user3_insa", "user3@insa-rennes.fr", org1),
            ("user4_insa", "user4@insa-rennes.fr", org1),
            ("user5_insa", "user5@insa-rennes.fr", org1),
            # Université de Rennes admin
            ("admin_univ", "admin_univ@univ-rennes.fr", org2),
            # Université de Rennes regular users
            ("user1_univ", "user1@univ-rennes.fr", org2),
            ("user2_univ", "user2@univ-rennes.fr", org2),
            ("user3_univ", "user3@univ-rennes.fr", org2),
            # École Polytechnique admin
            ("admin_poly", "admin_poly@polytechnique.edu.fr", org3),
            # École Polytechnique regular users
            ("user1_poly", "user1@polytechnique.edu.fr", org3),
            ("user2_poly", "user2@polytechnique.edu.fr", org3),
        ]

        created_users = {}
        for username, email, org in users_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "email_verified": True,
                },
            )
            user.set_password("password123")
            user.save()
            created_users[username] = user

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(created_users)} test users")
        )

        # Add admins to organizations
        org1.admins.add(created_users["admin_insa"], created_users["contact_insa"])
        org2.admins.add(created_users["admin_univ"])
        org3.admins.add(created_users["admin_poly"])

        self.stdout.write(self.style.SUCCESS("✓ Set organization admins"))

        # Create test locations
        locations_data = [
            (
                "INSA Rennes Campus",
                "Avenue d'Edgar Chablé",
                "35700",
                "Rennes",
                48.1122,
                -1.6430,
            ),
            (
                "Centre-Ville Rennes",
                "Place de la République",
                "35000",
                "Rennes",
                48.1102,
                -1.6846,
            ),
            (
                "Université de Rennes Campus",
                "Boulevard de Verdun",
                "35000",
                "Rennes",
                48.1069,
                -1.7000,
            ),
            ("Gare SNCF Rennes", "Avenue Janvier", "35000", "Rennes", 48.1045, -1.6708),
        ]

        created_locations = {}
        for fulltext, street, zipcode, city, lat, lng in locations_data:
            location, _ = Location.objects.get_or_create(
                fulltext=fulltext,
                defaults={
                    "street": street,
                    "zipcode": zipcode,
                    "city": city,
                    "lat": lat,
                    "lng": lng,
                },
            )
            created_locations[fulltext] = location

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(created_locations)} test locations")
        )

        # Create test vehicles
        vehicles_data = [
            ("Peugeot 308", created_users["user1_insa"], 5, 120),
            ("Renault Clio", created_users["user2_insa"], 5, 110),
            ("Citroën C5", created_users["user3_insa"], 5, 130),
            ("Tesla Model 3", created_users["user1_univ"], 5, 0),
            ("Volkswagen Golf", created_users["user1_poly"], 5, 115),
        ]

        created_vehicles = {}
        for name, driver, seats, co2_per_km in vehicles_data:
            vehicle, _ = Vehicle.objects.get_or_create(
                name=name,
                driver=driver,
                defaults={
                    "seats": seats,
                    "geqCO2_per_km": co2_per_km,
                },
            )
            created_vehicles[name] = vehicle

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(created_vehicles)} test vehicles")
        )

        # Create test rides
        now = timezone.now()
        rides_data = [
            # Rides for INSA users
            (
                created_users["user1_insa"],
                created_locations["INSA Rennes Campus"],
                created_locations["Centre-Ville Rennes"],
                now - timedelta(days=20),
                now - timedelta(days=20, hours=-3),
                created_vehicles["Peugeot 308"],
                [created_users["user2_insa"]],
            ),
            (
                created_users["user2_insa"],
                created_locations["Centre-Ville Rennes"],
                created_locations["INSA Rennes Campus"],
                now - timedelta(days=15),
                now - timedelta(days=15, hours=-2, minutes=-30),
                created_vehicles["Renault Clio"],
                [created_users["user3_insa"], created_users["user4_insa"]],
            ),
            (
                created_users["user3_insa"],
                created_locations["INSA Rennes Campus"],
                created_locations["Gare SNCF Rennes"],
                now - timedelta(days=10),
                now - timedelta(days=10, hours=-1, minutes=-30),
                created_vehicles["Citroën C5"],
                [created_users["user1_insa"]],
            ),
            (
                created_users["user1_insa"],
                created_locations["Gare SNCF Rennes"],
                created_locations["Centre-Ville Rennes"],
                now - timedelta(days=5),
                now - timedelta(days=5, hours=-1),
                created_vehicles["Peugeot 308"],
                [created_users["user5_insa"]],
            ),
            (
                created_users["user2_insa"],
                created_locations["INSA Rennes Campus"],
                created_locations["Université de Rennes Campus"],
                now - timedelta(days=2),
                now - timedelta(days=2, hours=-2),
                created_vehicles["Renault Clio"],
                [created_users["user4_insa"]],
            ),
            # Rides for Université users
            (
                created_users["user1_univ"],
                created_locations["Université de Rennes Campus"],
                created_locations["Centre-Ville Rennes"],
                now - timedelta(days=18),
                now - timedelta(days=18, hours=-1, minutes=-45),
                created_vehicles["Tesla Model 3"],
                [created_users["user2_univ"]],
            ),
            (
                created_users["user2_univ"],
                created_locations["Centre-Ville Rennes"],
                created_locations["Université de Rennes Campus"],
                now - timedelta(days=12),
                now - timedelta(days=12, hours=-2),
                created_vehicles["Tesla Model 3"],
                [created_users["user3_univ"]],
            ),
            # Rides for École Polytechnique users
            (
                created_users["user1_poly"],
                created_locations["INSA Rennes Campus"],
                created_locations["Centre-Ville Rennes"],
                now - timedelta(days=8),
                now - timedelta(days=8, hours=-1, minutes=-30),
                created_vehicles["Volkswagen Golf"],
                [created_users["user2_poly"]],
            ),
        ]

        for driver, start_loc, end_loc, start_dt, end_dt, vehicle, riders in rides_data:
            ride, created = Ride.objects.get_or_create(
                driver=driver,
                start_loc=start_loc,
                end_loc=end_loc,
                start_dt=start_dt,
                defaults={
                    "end_dt": end_dt,
                    "vehicle": vehicle,
                    "seats_offered": 4,
                    "payment_method": "CASH",
                    "geometry": None,
                    "duration": end_dt - start_dt,
                },
            )
            if created:
                ride.rider.set(riders)
                ride.save()

        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(rides_data)} test rides"))

        # Create organization statistics (will be updated by task normally)
        for org in [org1, org2, org3]:
            stats, _ = OrganizationStatistics.objects.get_or_create(
                organization=org,
                defaults={
                    "total_users": 0,
                    "total_rides": 0,
                    "total_distance": 0.0,
                    "total_co2": 0.0,
                },
            )

        self.stdout.write(self.style.SUCCESS("✓ Created organization statistics"))

        # Run the statistics calculation task
        from carpool.tasks import compute_organization_statistics

        compute_organization_statistics()

        self.stdout.write(
            self.style.SUCCESS(self.style.SUCCESS("✅ Test data loaded successfully!"))
        )
        self.stdout.write(self.style.SUCCESS("\nTest Admins:"))
        self.stdout.write(
            "  INSA Rennes: admin_insa@insa-rennes.fr (password: password123)"
        )
        self.stdout.write(
            "  INSA Rennes: contact_insa@insa-rennes.fr (password: password123)"
        )
        self.stdout.write(
            "  Université de Rennes: admin_univ@univ-rennes.fr (password: password123)"
        )
        self.stdout.write(
            "  École Polytechnique: admin_poly@polytechnique.edu.fr (password: password123)"
        )
        self.stdout.write(
            self.style.SUCCESS("\nAll accounts have password: password123")
        )
