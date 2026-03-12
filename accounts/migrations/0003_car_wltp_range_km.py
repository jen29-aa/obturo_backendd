from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_devicetoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='wltp_range_km',
            field=models.FloatField(default=300),
        ),
    ]
