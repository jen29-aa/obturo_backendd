from django.contrib import admin
from .models import ChargingStation, Booking, RecentlyViewedStation


@admin.register(ChargingStation)
class ChargingStationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "charger_type",
        "connector_type",
        "power_kw",
        "available_slots",
        "total_slots",
        "status",
    )
    search_fields = ("name", "address")
    list_filter = ("charger_type", "connector_type", "status", "verified")
    ordering = ("name",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "station", "start_time", "end_time", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "station__name")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Booking Info", {
            "fields": ("id", "user", "station", "status", "created_at")
        }),
        ("Time", {
            "fields": ("start_time", "end_time")
        }),
    )


@admin.register(RecentlyViewedStation)
class RecentlyViewedStationAdmin(admin.ModelAdmin):
    list_display = ("user", "station", "viewed_at")
    list_filter = ("viewed_at",)
    search_fields = ("user__username", "station__name")
    readonly_fields = ("viewed_at",)
    ordering = ("-viewed_at",)
