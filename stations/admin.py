from django.contrib import admin
from .models import ChargingStation, Booking

@admin.register(ChargingStation)
class ChargingStationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "charger_type", "connector_type", "power_kw", "status")
    search_fields = ("name", "address")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "station", "start_time", "end_time", "status")
    list_filter = ("status", "station")
    search_fields = ("user__username", "station__name")
