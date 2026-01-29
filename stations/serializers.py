from rest_framework import serializers
from django.db.models import Avg
from django.utils import timezone
from .models import (
    ChargingStation,
    Booking,
    FavouriteStation,
    PeerCharger,
    PeerBooking,
    StationRating,
)
from accounts.models import User


# =====================================================
# CHARGING STATION SERIALIZER
# =====================================================
class ChargingStationSerializer(serializers.ModelSerializer):
    avg_rating = serializers.SerializerMethodField()
    facilities_list = serializers.SerializerMethodField()

    class Meta:
        model = ChargingStation
        fields = [
            'id', 'name', 'address', 'latitude', 'longitude', 
            'charger_type', 'connector_type', 'power_kw', 'price_per_kwh',
            'available_slots', 'total_slots', 'waiting_time', 'avg_rating',
            'image_url', 'description', 'phone_number', 'email', 'operating_hours',
            'facilities', 'facilities_list', 'is_open_24_7', 'has_parking', 
            'has_restroom', 'has_cafe', 'has_wifi', 'verified', 'last_updated'
        ]

    def get_avg_rating(self, obj):
        avg = StationRating.objects.filter(station=obj).aggregate(
            Avg('rating')
        )['rating__avg']
        return round(avg or 0, 2)
    
    def get_facilities_list(self, obj):
        if obj.facilities:
            return [f.strip() for f in obj.facilities.split(',') if f.strip()]
        return []


# =====================================================
# BOOKING SERIALIZER
# =====================================================
class BookingSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_id = serializers.IntegerField(source='station.id', read_only=True)
    created_at = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'station_id', 'station_name', 'start_time', 'end_time',
            'status', 'created_at'
        ]

    def get_created_at(self, obj):
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%Y-%m-%d %H:%M')
        return None

    def get_start_time(self, obj):
        if obj.start_time:
            local_time = timezone.localtime(obj.start_time)
            return local_time.strftime('%Y-%m-%d %H:%M')
        return None

    def get_end_time(self, obj):
        if obj.end_time:
            local_time = timezone.localtime(obj.end_time)
            return local_time.strftime('%Y-%m-%d %H:%M')
        return None


# =====================================================
# USER PROFILE SERIALIZER
# =====================================================
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# =====================================================
# FAVOURITE STATION SERIALIZER
# =====================================================
class FavouriteStationSerializer(serializers.ModelSerializer):
    station = ChargingStationSerializer(read_only=True)

    class Meta:
        model = FavouriteStation
        fields = ['id', 'station', 'added_at']


# =====================================================
# PEER CHARGER SERIALIZER
# =====================================================
class PeerChargerSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = PeerCharger
        fields = [
            'id', 'name', 'owner', 'owner_name', 'latitude', 'longitude',
            'address', 'connector_type', 'power_kw', 'price_per_kwh',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'owner', 'owner_name', 'created_at']


# =====================================================
# PEER BOOKING SERIALIZER
# =====================================================
class PeerBookingSerializer(serializers.ModelSerializer):
    charger = PeerChargerSerializer(read_only=True)
    charger_id = serializers.PrimaryKeyRelatedField(
        queryset=PeerCharger.objects.filter(is_active=True),
        source='charger',
        write_only=True,
    )

    class Meta:
        model = PeerBooking
        fields = [
            'id', 'charger', 'charger_id', 'renter', 'start_time', 'end_time',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'renter', 'status', 'created_at', 'charger']

