from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.db.models import Count, Max, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from carpool.models.ride import Ride
from carpool.models.statistics import (
    MonthlyStatistics,
    Organization,
    OrganizationMonthlyStatistics,
    OrganizationStatistics,
    Statistics,
)
from carpool.serializers import (
    MonthlyStatisticsSerializer,
    OrganizationMonthlyStatisticsSerializer,
)


def is_organization_admin(user):
    """Check if user is an admin of at least one organization."""
    return user.administered_organizations.exists()


def is_admin_of_organization(user, organization):
    """Check if user is an admin of a specific organization."""
    return organization.admins.filter(pk=user.pk).exists()


@permission_required(["carpool.view_statistics"])
def statistics_json_monthly(request):
    # Get statistics for the current calendar year
    now = timezone.now()
    current_year = now.year

    monthly_stats = MonthlyStatistics.objects.filter(year=current_year)

    # Use new serializer format with calendar year indexing (0=January, 11=December)
    data = MonthlyStatisticsSerializer.serialize_statistics_json(
        current_year, monthly_stats
    )

    # Add legacy format for backward compatibility
    data["legacy"] = MonthlyStatisticsSerializer.serialize_statistics_legacy(
        monthly_stats
    )

    return JsonResponse(data)


@permission_required(["carpool.view_statistics"])
def statistics(request):
    if Statistics.objects.count() == 0:
        # Create the Statistics object if it does not exist
        Statistics.objects.create()

    context = {
        "last_updated_at": Statistics.objects.first().updated_at,
        "total_users": Statistics.objects.first().total_users,
        "total_rides": Statistics.objects.first().total_rides,
        "total_distance": Statistics.objects.first().total_distance,
        "total_co2": Statistics.objects.first().total_co2,
    }

    return render(request, "rides/back-office/statistics.html", context)


@login_required
@user_passes_test(is_organization_admin)
def organization_statistics_dashboard(request):
    """
    Display the back-office dashboard for organizations.
    Shows all organizations the user is an admin of.
    """
    user_organizations = request.user.administered_organizations.all()

    context = {
        "organizations": user_organizations,
    }

    return render(request, "rides/back-office/organization_dashboard.html", context)


@login_required
def organization_statistics(request, organization_id):
    """
    Display detailed statistics for a specific organization.
    Only admins of that organization can access it.
    """
    organization = get_object_or_404(Organization, pk=organization_id)

    # Check if user is an admin of this organization
    if not is_admin_of_organization(request.user, organization):
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("You don't have access to this organization")

    # Ensure organization statistics exist
    org_stats, _ = OrganizationStatistics.objects.get_or_create(
        organization=organization,
        defaults={
            "total_users": 0,
            "total_rides": 0,
            "total_distance": 0.0,
            "total_co2": 0.0,
        },
    )

    context = {
        "organization": organization,
        "stats": org_stats,
        "last_updated_at": org_stats.updated_at,
    }

    return render(request, "rides/back-office/organization_statistics.html", context)


@login_required
def organization_statistics_json_monthly(request, organization_id):
    """
    Return monthly statistics for an organization as JSON.
    Uses calendar year (January to December, indexed 0-11).
    """
    organization = get_object_or_404(Organization, pk=organization_id)

    if not is_admin_of_organization(request.user, organization):
        return HttpResponseForbidden("You don't have access to this organization")

    now = timezone.now()
    current_year = now.year

    monthly_stats = OrganizationMonthlyStatistics.objects.filter(
        organization=organization, year=current_year
    )

    data = (
        OrganizationMonthlyStatisticsSerializer.serialize_organization_statistics_json(
            organization, current_year, monthly_stats
        )
    )

    return JsonResponse(data)


@login_required
def organization_statistics_json_yearly(request, organization_id):
    """
    Return yearly aggregated statistics for an organization as JSON.
    Aggregates monthly stats by year.
    """
    organization = get_object_or_404(Organization, pk=organization_id)

    if not is_admin_of_organization(request.user, organization):
        return HttpResponseForbidden("You don't have access to this organization")

    yearly_qs = list(
        OrganizationMonthlyStatistics.objects.filter(organization=organization)
        .values("year")
        .annotate(
            rides=Sum("total_rides"),
            rides_carpooled=Sum("total_rides_carpooled"),
            users=Max("total_users"),
            distance_km=Sum("total_distance"),
            co2_kg=Sum("total_co2"),
        )
        .order_by("year")
    )

    data = {
        "labels": [str(y["year"]) for y in yearly_qs],
        "datasets": {
            "rides_proposed": [y["rides"] or 0 for y in yearly_qs],
            "rides_carpooled": [y["rides_carpooled"] or 0 for y in yearly_qs],
            "users": [y["users"] or 0 for y in yearly_qs],
            "distance_km": [round(y["distance_km"] or 0, 2) for y in yearly_qs],
            "co2_kg": [round(y["co2_kg"] or 0, 2) for y in yearly_qs],
        },
    }
    return JsonResponse(data)


@login_required
def organization_statistics_json_weekly(request, organization_id):
    """
    Return the last 12 weeks of ride statistics for an organization.
    Computed on-the-fly from the Ride model.
    """
    from django.db.models.functions import TruncWeek

    organization = get_object_or_404(Organization, pk=organization_id)

    if not is_admin_of_organization(request.user, organization):
        return HttpResponseForbidden("You don't have access to this organization")

    User = get_user_model()
    org_users = User.objects.filter(email__endswith=f"@{organization.email_domain}")
    since = timezone.now() - timedelta(weeks=12)

    base_qs = Ride.objects.filter(driver__in=org_users, start_dt__gte=since)

    proposed_by_week = (
        base_qs.annotate(week=TruncWeek("start_dt"))
        .values("week")
        .annotate(count=Count("uuid", distinct=True))
        .order_by("week")
    )

    carpooled_by_week = (
        base_qs.annotate(rider_count_a=Count("rider", distinct=True))
        .filter(rider_count_a__gt=0)
        .annotate(week=TruncWeek("start_dt"))
        .values("week")
        .annotate(count=Count("uuid", distinct=True))
        .order_by("week")
    )

    proposed_dict = {r["week"]: r["count"] for r in proposed_by_week}
    carpooled_dict = {r["week"]: r["count"] for r in carpooled_by_week}
    all_weeks = sorted(set(list(proposed_dict.keys()) + list(carpooled_dict.keys())))

    data = {
        "labels": [w.strftime("S%W %d/%m/%Y") for w in all_weeks],
        "datasets": {
            "rides_proposed": [proposed_dict.get(w, 0) for w in all_weeks],
            "rides_carpooled": [carpooled_dict.get(w, 0) for w in all_weeks],
        },
    }
    return JsonResponse(data)
