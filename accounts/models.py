from django.db import models
from django.contrib.auth.models import User

class Car(models.Model):
    name = models.CharField(max_length=100)
    battery_capacity_kwh = models.FloatField()
    max_dc_power_kw = models.FloatField()
    max_ac_power_kw = models.FloatField()
    connector_type = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class UserCar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} → {self.car.name}"

from django.db import models
from django.contrib.auth.models import User

class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=300, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.token[:20]}"
