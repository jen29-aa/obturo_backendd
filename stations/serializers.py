from rest_framework import serializers
from .models import ChargingStation
from .models import (
    ChargingStation,
    Booking,
    FavouriteStation,
    PeerCharger,
    PeerBooking,
)


class ChargingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargingStation
        fields = '__all__'

from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

###BOOKING AND HISTORY

from rest_framework import serializers
from .models import ChargingStation, Booking   # Booking already imported? if not, import it.

class BookingSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "station",
            "station_name",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
from rest_framework import serializers
from .models import ChargingStation, FavouriteStation
from accounts.models import User


class ChargingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargingStation
        fields = "__all__"


# -------------------------
# USER PROFILE SERIALIZER
# -------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


# -------------------------
# FAVOURITE STATION SERIALIZER
# -------------------------
class FavouriteStationSerializer(serializers.ModelSerializer):
    station = ChargingStationSerializer()

    class Meta:
        model = FavouriteStation
        fields = ["id", "station", "added_at"]

from rest_framework import serializers

class PeerChargerSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = PeerCharger
        fields = [
            "id",
            "name",
            "owner",
            "owner_name",
            "latitude",
            "longitude",
            "address",
            "connector_type",
            "power_kw",
            "price_per_kwh",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "owner", "owner_name", "created_at"]


class PeerBookingSerializer(serializers.ModelSerializer):
    charger = PeerChargerSerializer(read_only=True)
    charger_id = serializers.PrimaryKeyRelatedField(
        queryset=PeerCharger.objects.filter(is_active=True),
        source="charger",
        write_only=True,
    )

    class Meta:
        model = PeerBooking
        fields = [
            "id",
            "charger",
            "charger_id",
            "renter",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "renter", "status", "created_at", "charger"]

from django.db.models import Avg
from .models import StationRating

class ChargingStationSerializer(serializers.ModelSerializer):
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = ChargingStation
        fields = "__all__"  # includes avg_rating automatically

    def get_avg_rating(self, obj):
        avg = StationRating.objects.filter(station=obj).aggregate(
            Avg("rating")
        )["rating__avg"]
        return round(avg or 0, 2)

