"""
Serializers for carpool models, particularly for statistics data.
Uses calendar year indexing: 0=January, 11=December
"""

from django.utils import timezone
from carpool.models.statistics import MonthlyStatistics, Statistics


# Month indices for the chart (0-based, where 0=January to 11=December)
MONTH_NAMES = {
    0: "January",
    1: "February",
    2: "March",
    3: "April",
    4: "May",
    5: "June",
    6: "July",
    7: "August",
    8: "September",
    9: "October",
    10: "November",
    11: "December",
}


class MonthlyStatisticsSerializer:
    """Serialize monthly statistics to a clean JSON format."""

    @staticmethod
    def serialize_month_data(stat: MonthlyStatistics, month_index: int) -> dict:
        """
        Serialize a single monthly statistic.

        Args:
            stat: MonthlyStatistics object
            month_index: Month index (0-11, where 0=January)

        Returns:
            Dictionary with serialized month data
        """
        return {
            "month": stat.month,
            "year": stat.year,
            "rides": stat.total_rides,
            "users": stat.total_users,
            "distance_km": round(stat.total_distance, 2),
            "co2_kg": round(stat.total_co2, 2),
        }

    @staticmethod
    def serialize_calendar_year(year: int, monthly_stats_queryset) -> dict:
        """
        Serialize all monthly statistics for a calendar year (January to December).
        Returns data indexed by month number (0-11, where 0=January, 11=December).

        Args:
            year: Calendar year
            monthly_stats_queryset: QuerySet of MonthlyStatistics objects filtered by year

        Returns:
            Dictionary with structured data for the calendar year
        """
        months_data = {}
        totals = {
            "rides": 0,
            "users": 0,
            "distance_km": 0.0,
            "co2_kg": 0.0,
        }

        # Calendar year order: Jan through Dec (months 1-12)
        for chart_index in range(12):
            calendar_month = chart_index + 1  # 1-12

            # Find the stat for this month
            stat = None
            for s in monthly_stats_queryset:
                if s.month == calendar_month and s.year == year:
                    stat = s
                    break

            if stat:
                month_data = MonthlyStatisticsSerializer.serialize_month_data(
                    stat, chart_index
                )
            else:
                # Empty month
                month_data = {
                    "month": calendar_month,
                    "year": year,
                    "rides": 0,
                    "users": 0,
                    "distance_km": 0.0,
                    "co2_kg": 0.0,
                }

            months_data[str(chart_index)] = month_data

            # Accumulate totals
            totals["rides"] += month_data["rides"]
            totals["users"] += month_data["users"]
            totals["distance_km"] += month_data["distance_km"]
            totals["co2_kg"] += month_data["co2_kg"]

        return {
            "months": months_data,
            "totals": {
                "rides": totals["rides"],
                "users": totals["users"],
                "distance_km": round(totals["distance_km"], 2),
                "co2_km": round(totals["co2_kg"], 2),
            },
        }

    @staticmethod
    def serialize_statistics_json(year: int, monthly_stats_queryset) -> dict:
        """
        Serialize statistics to a clean, well-structured JSON format.
        Uses calendar year (January to December, indexed 0-11).

        Args:
            year: Calendar year (e.g., 2025)
            monthly_stats_queryset: QuerySet of MonthlyStatistics objects

        Returns:
            Complete statistics JSON structure
        """
        now = timezone.now()
        calendar_year_data = MonthlyStatisticsSerializer.serialize_calendar_year(
            year, monthly_stats_queryset
        )

        return {
            "meta": {
                "generated_at": now.isoformat(),
                "version": "2.0",
                "calendar_year": year,
                "month_indexing": "0=January, 11=December",
            },
            "data": calendar_year_data,
            # Flat arrays for backward compatibility
            "labels": MonthlyStatisticsSerializer._generate_labels(year),
        }

    @staticmethod
    def _generate_labels(year: int) -> list:
        """Generate labels in format 'MM-YYYY' for backward compatibility."""
        labels = []
        for month in range(1, 13):
            labels.append(f"{month:02d}-{year}")
        return labels

    @staticmethod
    def serialize_statistics_legacy(monthly_stats_queryset) -> dict:
        """
        Serialize statistics in the legacy format for backward compatibility.
        Returns separate arrays for each metric.
        """
        # Sort by month
        monthly_stats_list = sorted(monthly_stats_queryset, key=lambda s: s.month)

        return {
            "monthly_total_rides": [stat.total_rides for stat in monthly_stats_list],
            "monthly_total_users": [stat.total_users for stat in monthly_stats_list],
            "monthly_total_distance": [
                round(stat.total_distance, 2) for stat in monthly_stats_list
            ],
            "monthly_total_co2": [
                round(stat.total_co2, 2) for stat in monthly_stats_list
            ],
        }


class GlobalStatisticsSerializer:
    """Serialize global statistics."""

    @staticmethod
    def serialize(stat: Statistics) -> dict:
        """
        Serialize global statistics.

        Args:
            stat: Statistics object

        Returns:
            Dictionary with serialized global statistics
        """
        return {
            "meta": {
                "updated_at": stat.updated_at.isoformat(),
                "version": "2.0",
            },
            "data": {
                "total_rides": stat.total_rides,
                "total_users": stat.total_users,
                "total_distance_km": round(stat.total_distance, 2),
                "total_co2_kg": round(stat.total_co2, 2),
            },
        }


class OrganizationMonthlyStatisticsSerializer:
    """Serialize organization monthly statistics."""

    @staticmethod
    def serialize_organization_calendar_year(
        organization, year, monthly_stats_queryset
    ) -> dict:
        """
        Serialize all monthly statistics for an organization's calendar year (Jan-Dec).

        Args:
            organization: Organization object
            year: Calendar year
            monthly_stats_queryset: QuerySet of OrganizationMonthlyStatistics objects

        Returns:
            Dictionary with structured data for the calendar year
        """
        months_data = {}
        totals = {
            "rides": 0,
            "rides_carpooled": 0,
            "users": 0,
            "distance_km": 0.0,
            "co2_kg": 0.0,
        }

        # Calendar year order: Jan through Dec (months 1-12)
        for chart_index in range(12):
            calendar_month = chart_index + 1  # 1-12

            # Find the stat for this month
            stat = None
            for s in monthly_stats_queryset:
                if s.month == calendar_month and s.year == year:
                    stat = s
                    break

            if stat:
                month_data = {
                    "month": stat.month,
                    "year": stat.year,
                    "rides": stat.total_rides,
                    "rides_carpooled": stat.total_rides_carpooled,
                    "users": stat.total_users,
                    "distance_km": round(stat.total_distance, 2),
                    "co2_kg": round(stat.total_co2, 2),
                }
            else:
                # Empty month
                month_data = {
                    "month": calendar_month,
                    "year": year,
                    "rides": 0,
                    "rides_carpooled": 0,
                    "users": 0,
                    "distance_km": 0.0,
                    "co2_kg": 0.0,
                }

            months_data[str(chart_index)] = month_data

            # Accumulate totals
            totals["rides"] += month_data["rides"]
            totals["rides_carpooled"] += month_data["rides_carpooled"]
            totals["users"] += month_data["users"]
            totals["distance_km"] += month_data["distance_km"]
            totals["co2_kg"] += month_data["co2_kg"]

        return {
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "email_domain": organization.email_domain,
            },
            "months": months_data,
            "totals": {
                "rides": totals["rides"],
                "rides_carpooled": totals["rides_carpooled"],
                "users": totals["users"],
                "distance_km": round(totals["distance_km"], 2),
                "co2_kg": round(totals["co2_kg"], 2),
            },
        }

    @staticmethod
    def serialize_organization_statistics_json(
        organization, year, monthly_stats_queryset
    ) -> dict:
        """
        Serialize organization statistics to clean JSON format.
        Uses calendar year (January to December, indexed 0-11).

        Args:
            organization: Organization object
            year: Calendar year
            monthly_stats_queryset: QuerySet of OrganizationMonthlyStatistics objects

        Returns:
            Complete statistics JSON structure
        """
        now = timezone.now()
        calendar_year_data = OrganizationMonthlyStatisticsSerializer.serialize_organization_calendar_year(
            organization, year, monthly_stats_queryset
        )

        return {
            "meta": {
                "generated_at": now.isoformat(),
                "version": "2.0",
                "calendar_year": year,
                "month_indexing": "0=January, 11=December",
            },
            "data": calendar_year_data,
            # Flat arrays for backward compatibility
            "labels": MonthlyStatisticsSerializer._generate_labels(year),
        }

    @staticmethod
    def serialize_organization_statistics_legacy(monthly_stats_queryset) -> dict:
        """
        Serialize organization statistics in legacy format for backward compatibility.
        """
        # Sort by month
        monthly_stats_list = sorted(monthly_stats_queryset, key=lambda s: s.month)

        return {
            "monthly_total_rides": [stat.total_rides for stat in monthly_stats_list],
            "monthly_total_users": [stat.total_users for stat in monthly_stats_list],
            "monthly_total_distance": [
                round(stat.total_distance, 2) for stat in monthly_stats_list
            ],
            "monthly_total_co2": [
                round(stat.total_co2, 2) for stat in monthly_stats_list
            ],
        }
