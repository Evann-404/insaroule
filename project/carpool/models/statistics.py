from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Statistics(models.Model):
    """
    Model used to store overall statistics about the application.

    Used to avoid recalculating statistics on each request to the back-office.
    This model contains only 1 record that is updated daily by a Celery task.
    """

    # Last time the statistics were updated
    updated_at = models.DateTimeField(auto_now=True)

    # Global statistics
    total_users = models.IntegerField(default=0)
    total_rides = models.IntegerField(default=0)
    total_distance = models.FloatField(default=0.0)
    total_co2 = models.FloatField(default=0.0)

    class Meta:
        verbose_name = _("Statistic")
        verbose_name_plural = _("Statistics")


class MonthlyStatisticsManager(models.Manager):
    def filter_by_academic_year(self, start_year):
        """
        Filter MonthlyStatistics by academic year.
        """
        return self.filter(
            models.Q(year=start_year, month__gte=9)
            | models.Q(year=start_year + 1, month__lt=9)
        )


class MonthlyStatistics(models.Model):
    """
    Monthly statistics about the application usage.

    This model is updated monthly by a Celery task. The current month statistics
    is updated daily by the same Celery task that updates the overall statistics.
    """

    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.IntegerField()

    # Monthly statistics
    total_users = models.IntegerField(default=0)
    total_rides = models.IntegerField(default=0)
    total_distance = models.FloatField(default=0.0)
    total_co2 = models.FloatField(default=0.0)

    objects = MonthlyStatisticsManager()

    class Meta:
        unique_together = ("month", "year")
        verbose_name = _("Monthly statistic")
        verbose_name_plural = _("Monthly statistics")


class Organization(models.Model):
    """
    Represents a school/organization. Users are linked via email domain.
    Admins can access the back-office for their organization.
    """

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email_domain = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Email domain"),
        help_text=_(
            "e.g. insa-rennes.fr — users with this domain are linked to this organization"
        ),
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="administered_organizations",
        verbose_name=_("Admins"),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")


class OrganizationStatistics(models.Model):
    """
    All-time aggregated stats for an organization.
    Updated daily by Celery task.
    """

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="statistics",
    )
    updated_at = models.DateTimeField(auto_now=True)
    total_users = models.IntegerField(default=0)
    total_rides = models.IntegerField(default=0)
    total_distance = models.FloatField(default=0.0)
    total_co2 = models.FloatField(default=0.0)

    class Meta:
        verbose_name = _("Organization statistic")
        verbose_name_plural = _("Organization statistics")


class OrganizationMonthlyStatisticsManager(models.Manager):
    def filter_by_academic_year(self, organization, start_year):
        return self.filter(
            organization=organization,
        ).filter(
            models.Q(year=start_year, month__gte=9)
            | models.Q(year=start_year + 1, month__lt=9)
        )


class OrganizationMonthlyStatistics(models.Model):
    """
    Monthly stats per organization.
    Updated daily by Celery task for the current month.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="monthly_statistics",
    )
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.IntegerField()
    total_users = models.IntegerField(default=0)
    total_rides = models.IntegerField(default=0)
    total_distance = models.FloatField(default=0.0)
    total_co2 = models.FloatField(default=0.0)

    objects = OrganizationMonthlyStatisticsManager()

    class Meta:
        unique_together = ("organization", "month", "year")
        verbose_name = _("Organization monthly statistic")
        verbose_name_plural = _("Organization monthly statistics")
