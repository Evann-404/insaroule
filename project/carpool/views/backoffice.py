from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.decorators import user_passes_test
from carpool.models.statistics import (
    Statistics,
    MonthlyStatistics,
    Organization,
    OrganizationStatistics,
    OrganizationMonthlyStatistics,
)


def is_organization_admin(user):
    """Check if user is an admin of at least one organization."""
    return user.administered_organizations.exists()


def is_admin_of_organization(user, organization):
    """Check if user is an admin of a specific organization."""
    return organization.admins.filter(pk=user.pk).exists()


@permission_required(["carpool.view_statistics"])
def statistics_json_monthly(request):
    # Get labels for the current academic year (from September to August)
    now = timezone.now()
    if now.month >= 9:
        start_year = now.year
    else:
        start_year = now.year - 1
    labels = []
    for month in range(9, 13):
        labels.append(f"{month:02d}-{start_year}")
    for month in range(1, 9):
        labels.append(f"{month:02d}-{start_year + 1}")
    monthly_stats = MonthlyStatistics.objects.filter_by_academic_year(start_year)
    monthly_total_rides = [stat.total_rides for stat in monthly_stats]
    monthly_total_users = [stat.total_users for stat in monthly_stats]
    monthly_total_distance = [stat.total_distance for stat in monthly_stats]
    monthly_total_co2 = [stat.total_co2 for stat in monthly_stats]

    data = {
        "labels": labels,
        "monthly_total_rides": monthly_total_rides,
        "monthly_total_users": monthly_total_users,
        "monthly_total_distance": monthly_total_distance,
        "monthly_total_co2": monthly_total_co2,
    }

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
    Used for displaying charts in the front-end.
    """
    organization = get_object_or_404(Organization, pk=organization_id)

    # Check if user is an admin of this organization
    if not is_admin_of_organization(request.user, organization):
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("You don't have access to this organization")

    # Get labels for the current academic year (from September to August)
    now = timezone.now()
    if now.month >= 9:
        start_year = now.year
    else:
        start_year = now.year - 1

    labels = []
    for month in range(9, 13):
        labels.append(f"{month:02d}-{start_year}")
    for month in range(1, 9):
        labels.append(f"{month:02d}-{start_year + 1}")

    monthly_stats = OrganizationMonthlyStatistics.objects.filter_by_academic_year(
        organization, start_year
    )

    monthly_total_rides = [stat.total_rides for stat in monthly_stats]
    monthly_total_users = [stat.total_users for stat in monthly_stats]
    monthly_total_distance = [stat.total_distance for stat in monthly_stats]
    monthly_total_co2 = [stat.total_co2 for stat in monthly_stats]

    data = {
        "labels": labels,
        "monthly_total_rides": monthly_total_rides,
        "monthly_total_users": monthly_total_users,
        "monthly_total_distance": monthly_total_distance,
        "monthly_total_co2": monthly_total_co2,
    }

    return JsonResponse(data)
