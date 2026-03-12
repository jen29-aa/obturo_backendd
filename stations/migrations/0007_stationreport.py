from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stations', '0006_waitlist_expires_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='StationReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(choices=[('broken', 'Charger Broken'), ('queue', 'Long Queue'), ('closed', 'Station Closed'), ('offline', 'Offline / No Power'), ('clean', 'All Clear')], max_length=20)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('upvotes', models.IntegerField(default=0)),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='stations.chargingstation')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
