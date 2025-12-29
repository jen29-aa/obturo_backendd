from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# ====================================
# 1. MAIN CHARGING STATION MODEL
# ====================================
class ChargingStation(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(null=True, blank=True)

    charger_type = models.CharField(max_length=10, default="DC")  # AC or DC
    connector_type = models.CharField(max_length=100, default="CCS2")
    power_kw = models.FloatField(default=30.0)

    total_slots = models.IntegerField(default=4)
    available_slots = models.IntegerField(default=2)

    price_per_kwh = models.FloatField(default=18.0)
    waiting_time = models.IntegerField(default=5)
    speed = models.IntegerField(default=50)

    status = models.CharField(max_length=20, default="Available")

    def __str__(self):
        return self.name


# ====================================
# 2. NORMAL STATION BOOKING
# ====================================
class Booking(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey(ChargingStation, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.station} - {self.status}"


# ====================================
# 3. FAVOURITE STATIONS
# ====================================
class FavouriteStation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey(ChargingStation, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "station")

    def __str__(self):
        return f"{self.user} -> {self.station}"


# ====================================
# 4. P2P CHARGER SHARING
# ====================================
class PeerCharger(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="peer_chargers"
    )
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    connector_type = models.CharField(max_length=50, default="CCS2")
    power_kw = models.FloatField(default=7.0)
    price_per_kwh = models.FloatField(default=15.0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class PeerBooking(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    )

    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="peer_bookings"
    )
    charger = models.ForeignKey(
        PeerCharger,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.renter} -> {self.charger} ({self.status})"


# ====================================
# 5. STATION RATINGS
# ====================================
class StationRating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="station_ratings"
    )
    station = models.ForeignKey(
        ChargingStation,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    rating = models.IntegerField()  # 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "station")

    def __str__(self):
        return f"{self.station} - {self.rating}"


# ====================================
# 6. PENALTY SYSTEM
# ====================================
class UserPenalty(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    no_show_count = models.IntegerField(default=0)
    late_cancel_count = models.IntegerField(default=0)
    penalty_points = models.IntegerField(default=0)

    blocked_until = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.penalty_points} pts"



# ====================================
# 7. WAITLIST (SMART QUEUE)
# ====================================
class Waitlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    station = models.ForeignKey(
        ChargingStation, on_delete=models.CASCADE, related_name="waitlist_entries"
    )

    # Position in the queue (IMPORTANT → this column caused your error!)
    position = models.IntegerField(default=1)

    # Whether the user already got a “slot available” notification
    notified = models.BooleanField(default=False)

    # Helps ordering correctly
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "station")
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.user.username} → {self.station.name} (pos {self.position})"
