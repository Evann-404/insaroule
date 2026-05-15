from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("carpool", "0012_organization_organizationstatistics_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizationmonthlystatistics",
            name="total_rides_carpooled",
            field=models.IntegerField(default=0),
        ),
    ]
