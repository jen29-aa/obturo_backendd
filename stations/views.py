from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone
from django.db import models
from django.db import transaction
from datetime import datetime, timedelta
import math
import numpy as np

from .models import (
    ChargingStation,
    Booking,
    FavouriteStation,
    PeerCharger,
    PeerBooking,
    StationRating,
    UserPenalty,
    Waitlist,
)
from .serializers import (
    ChargingStationSerializer,
    BookingSerializer,
    FavouriteStationSerializer,
    UserProfileSerializer,
    PeerChargerSerializer,
    PeerBookingSerializer,
)
from accounts.models import UserCar, DeviceToken
from .firebase import send_push_notification

# Waitlist service (centralized)
from .waitlist_service import (
    promote_waitlist_for_station,
    get_waitlist_info,
    reorder_waitlist,
)

# -------------------------
# Utility: penalty helper
# -------------------------
def add_penalty(user, points):
    """
    Corrected add_penalty that updates penalty_points and optionally blocks user.
    Ensure your UserPenalty model has 'penalty_points' and optional 'blocked_until'.
    """
    pen, _ = UserPenalty.objects.get_or_create(user=user)
    # Some models use 'penalty_points' name — adjust if your model uses different attr
    if hasattr(pen, "penalty_points"):
        pen.penalty_points += points
    else:
        # fallback to 'points' if older model
        pen.points = getattr(pen, "points", 0) + points

    # Blocking rules (example thresholds)
    try:
        if pen.penalty_points >= 5:
            pen.blocked_until = timezone.now() + timedelta(days=7)
        elif pen.penalty_points >= 3:
            pen.blocked_until = timezone.now() + timedelta(hours=24)
    except Exception:
        # if blocked_until field not present, ignore
        pass

    pen.save()

# -------------------------
# Utility: distance
# -------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# -------------------------
# Utility: route proximity
# -------------------------
def is_station_near_route(station, route_points, max_distance_km):
    for pt in route_points:
        d = calculate_distance(pt["lat"], pt["lng"], station.latitude, station.longitude)
        if d <= max_distance_km:
            return True
    return False


# -------------------------
# Utility: TOPSIS
# -------------------------
def topsis(matrix, weights, impacts):
    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights, dtype=float)

    # Normalize with zero-safety
    norm = np.linalg.norm(matrix, axis=0)
    norm[norm == 0] = 1
    nm = matrix / norm

    # Weighting
    wm = nm * weights

    impacts_arr = np.array(impacts)

    # Ideal best & worst
    ideal_best = np.where(impacts_arr == "+", wm.max(axis=0), wm.min(axis=0))
    ideal_worst = np.where(impacts_arr == "+", wm.min(axis=0), wm.max(axis=0))

    # Distances
    d_best = np.sqrt(((wm - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((wm - ideal_worst) ** 2).sum(axis=1))

    denom = d_best + d_worst
    denom[denom == 0] = 1

    return (d_worst / denom).tolist()


# -------------------------
# DRY: nearby stations
# -------------------------
def _get_nearby_station_tuples(user_lat: float, user_lng: float, radius_km: float):
    result = []
    for st in ChargingStation.objects.all():
        dist = calculate_distance(user_lat, user_lng, st.latitude, st.longitude)
        if dist <= radius_km:
            result.append((st, dist))
    result.sort(key=lambda x: x[1])
    return result


# -------------------------
# Utility: parse iso datetime (returns timezone-aware in settings tz)
# -------------------------
def parse_iso_datetime(dt_str):
    """
    Accepts ISO-like strings (e.g., '2025-12-07T12:15' or '2025-12-07T12:15:00').
    Converts to timezone-aware datetime using project timezone.
    """
    # Python's fromisoformat can parse 'YYYY-MM-DDTHH:MM[:SS][.ffffff][+HH:MM]'
    dt = datetime.fromisoformat(dt_str)
    tz = timezone.get_current_timezone()
    if dt.tzinfo is None:
        return timezone.make_aware(dt, tz)
    return dt.astimezone(tz)


# ---------------------------------------------------------
# 1. GET ALL STATIONS
# ---------------------------------------------------------
@api_view(["GET"])
def get_all_stations(request):
    stations = ChargingStation.objects.all().order_by("id")
    return Response(ChargingStationSerializer(stations, many=True).data)


# ---------------------------------------------------------
# 2. NEARBY STATIONS (detailed – for list view)
# ---------------------------------------------------------
@api_view(["GET"])
def get_nearby_stations(request):
    try:
        user_lat = float(request.GET.get("lat"))
        user_lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return Response({"error": "lat and lng are required"}, status=400)

    radius = float(request.GET.get("radius", 10))  # km

    station_tuples = _get_nearby_station_tuples(user_lat, user_lng, radius)

    found = []
    for st, dist in station_tuples:
        item = ChargingStationSerializer(st).data
        item["distance_km"] = round(dist, 2)
        found.append(item)

    return Response({"count": len(found), "stations": found})


# ---------------------------------------------------------
# 3. CREATE BOOKING (with auto-waitlist)
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):
    user = request.user
   # ---------------------------------------------------------
    # BLOCKED USER VALIDATION
    # ---------------------------------------------------------
    from django.utils import timezone

    pen = UserPenalty.objects.filter(user=user).first()


    if pen and pen.blocked_until and pen.blocked_until > timezone.now():
        return Response(
        {
            "error": f"You are blocked until {pen.blocked_until.strftime('%Y-%m-%d %H:%M')}"
        },
        status=403
    )


    station_id = request.data.get("station_id")
    start_time = request.data.get("start_time")
    end_time = request.data.get("end_time")

    if not all([station_id, start_time, end_time]):
        return Response({"error": "station_id, start_time, end_time required"}, status=400)

    try:
        start = parse_iso_datetime(start_time)
        end = parse_iso_datetime(end_time)
    except Exception:
        return Response({"error": "Invalid datetime format"}, status=400)

    if end <= start:
        return Response({"error": "Invalid time range"}, status=400)

    try:
        station = ChargingStation.objects.get(id=station_id)
    except ChargingStation.DoesNotExist:
        return Response({"error": "Station not found"}, status=404)

    # Overlap check (active bookings that intersect requested window)
    overlapping = Booking.objects.filter(
        station=station,
        status="active",
        start_time__lt=end,
        end_time__gt=start,
    ).count()

    # If full -> add to waitlist
    if overlapping >= station.total_slots:
        existing = Waitlist.objects.filter(user=user, station=station).first()
        if existing:
            return Response({
                "message": "Station is full. You are already in the waitlist.",
                "position": existing.position,
            }, status=202)

        last = Waitlist.objects.filter(station=station).order_by("-position").first()
        next_pos = (last.position + 1) if last else 1

        Waitlist.objects.create(user=user, station=station, position=next_pos)

        # Notify user
        tokens = DeviceToken.objects.filter(user=user)
        for t in tokens:
            send_push_notification(
                t.token,
                title="Added to Waitlist",
                body=f"Station {station.name} is full. Your waitlist position: {next_pos}",
            )

        # Re-order is not strictly necessary here (we appended at end),
        # but if any concurrent modifications happen we can call reorder.
        reorder_waitlist(station)

        return Response({
            "message": "Station is full. You have been added to the waitlist.",
            "position": next_pos,
        }, status=202)

    # Free slot -> create booking
    booking = Booking.objects.create(
        user=user,
        station=station,
        start_time=start,
        end_time=end,
        status="active",
    )
    # decrease available slot
    station.available_slots = max(0, station.available_slots - 1)
    station.save()

    # Notify user
    tokens = DeviceToken.objects.filter(user=user)
    for t in tokens:
        send_push_notification(
            t.token,
            title="Booking Confirmed",
            body=f"You booked {station.name} from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}",
        )

    return Response({
        "message": "Booking created",
        "booking_id": booking.id,
    })


# ---------------------------------------------------------
# 4. SMART FILTERING (car-based)
# ---------------------------------------------------------
class SmartFilteredStations(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_car = UserCar.objects.get(user=request.user)
        except UserCar.DoesNotExist:
            return Response({"error": "Car not selected"}, status=400)

        car = user_car.car

        stations = ChargingStation.objects.filter(connector_type=car.connector_type)

        if getattr(car, "max_dc_power_kw", 0) >= 30:
            stations = stations.order_by(
                models.Case(
                    models.When(charger_type="DC", then=0),
                    models.When(charger_type="AC", then=1),
                    default=2,
                    output_field=models.IntegerField(),
                ),
                "-power_kw",
            )
        else:
            stations = stations.order_by(
                models.Case(
                    models.When(charger_type="AC", then=0),
                    models.When(charger_type="DC", then=1),
                    default=2,
                    output_field=models.IntegerField(),
                ),
                "-power_kw",
            )

        data = ChargingStationSerializer(stations, many=True).data
        return Response(data)


# ---------------------------------------------------------
# 5. TOPSIS – CUSTOM WEIGHTED MCDM
# ---------------------------------------------------------
@api_view(["POST"])
def topsis_custom(request):
    user_lat = request.data.get("lat")
    user_lng = request.data.get("lng")
    radius = float(request.data.get("radius", 15))
    top_n = int(request.data.get("top_n", 5))
    weights_dict = request.data.get("weights") or {}

    if user_lat is None or user_lng is None:
        return Response({"error": "lat and lng required"}, status=400)

    try:
        user_lat = float(user_lat)
        user_lng = float(user_lng)
    except (TypeError, ValueError):
        return Response({"error": "lat and lng must be numbers"}, status=400)

    if not isinstance(weights_dict, dict):
        return Response({"error": "weights must be a JSON object"}, status=400)

    required = [
        "available_slots",
        "power_kw",
        "waiting_time",
        "charging_time",
        "price_per_kwh",
        "distance",
    ]

    for k in required:
        if k not in weights_dict:
            return Response({"error": f"Weight '{k}' missing"}, status=400)

    weights = [float(weights_dict[k]) for k in required]

    nearby = []
    for st in ChargingStation.objects.all():
        dist = calculate_distance(user_lat, user_lng, st.latitude, st.longitude)
        if dist <= radius:
            st._distance = dist
            nearby.append(st)

    if not nearby:
        return Response({"error": "No stations near your location"}, status=404)

    matrix, data = [], []

    for st in nearby:
        charging_time = st.power_kw / st.speed if getattr(st, "speed", 0) else 0

        row = [
            st.available_slots,
            st.power_kw,
            st.waiting_time,
            charging_time,
            st.price_per_kwh,
            st._distance,
        ]
        matrix.append(row)

        data.append(
            {
                "id": st.id,
                "name": st.name,
                "available_slots": st.available_slots,
                "power_kw": st.power_kw,
                "waiting_time": st.waiting_time,
                "charging_time": round(charging_time, 2),
                "price_per_kwh": st.price_per_kwh,
                "distance": round(st._distance, 2),
            }
        )

    impacts = ["+", "+", "-", "-", "-", "-"]
    scores = topsis(matrix, weights, impacts)

    for i, s in enumerate(scores):
        data[i]["score"] = round(s, 4)

    ranked = sorted(data, key=lambda x: x["score"], reverse=True)
    return Response(ranked[:top_n])


# ---------------------------------------------------------
# 6. BOOKING HISTORY
# ---------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    qs = Booking.objects.filter(user=request.user).order_by("-start_time")
    status_filter = request.GET.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)

    return Response(BookingSerializer(qs, many=True).data)


# ---------------------------------------------------------
# 7. CANCEL BOOKING (immediate promotion)
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    booking_id = request.data.get("booking_id")
    if not booking_id:
        return Response({"error": "booking_id required"}, status=400)

    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    if booking.status != "active":
        return Response({"error": "Only active bookings can be cancelled"}, status=400)

    now_ = timezone.now()
    if booking.start_time <= now_:
        return Response({"error": "Booking already started"}, status=400)

    # Late cancel penalty (within 10 minutes of start)
    if booking.start_time - now_ <= timedelta(minutes=10):
        pen, _ = UserPenalty.objects.get_or_create(user=request.user)
        pen.late_cancel_count = getattr(pen, "late_cancel_count", 0) + 1
        pen.penalty_points = getattr(pen, "penalty_points", 0) + 1
        pen.save()

    station = booking.station
    booking.status = "cancelled"
    booking.save()

    # notify user
    tokens = DeviceToken.objects.filter(user=request.user)
    for t in tokens:
        send_push_notification(
            t.token,
            title="Booking Cancelled",
            body=f"Your booking at {station.name} has been cancelled.",
        )

    # immediate promotion using centralized service
    promote_waitlist_for_station(station, notify=True)

    return Response({"message": "Booking cancelled"})


# ---------------------------------------------------------
# 7b. GET WAITLIST POSITION
# ---------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_waitlist_position(request):
    station_id = request.GET.get("station_id")
    if not station_id:
        return Response({"error": "station_id required"}, status=400)

    try:
        station = ChargingStation.objects.get(id=station_id)
    except ChargingStation.DoesNotExist:
        return Response({"error": "Station not found"}, status=404)

    info = get_waitlist_info(request.user, station)
    if not info:
        return Response({"message": "User not in waitlist"}, status=404)

    return Response({
        "station_id": station.id,
        "position": info["position"],
        "estimated_wait_minutes": info["estimated_wait_minutes"]
    })


# ---------------------------------------------------------
# 8. GET / UPDATE PROFILE
# ---------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data

    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)
    user.save()

    return Response({"message": "Profile updated"})


# ---------------------------------------------------------
# 9. FAVOURITES
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_favourite(request):
    station_id = request.data.get("station_id")
    if not station_id:
        return Response({"error": "station_id required"}, status=400)

    try:
        station = ChargingStation.objects.get(id=station_id)
    except ChargingStation.DoesNotExist:
        return Response({"error": "Station not found"}, status=404)

    fav, created = FavouriteStation.objects.get_or_create(
        user=request.user,
        station=station,
    )

    if not created:
        fav.delete()
        return Response({"message": "Removed from favourites"})

    return Response({"message": "Added to favourites"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_favourites(request):
    favs = FavouriteStation.objects.filter(user=request.user).order_by("-added_at")
    serializer = FavouriteStationSerializer(favs, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------
# 10. MAP MARKERS / ROUTE / BEST STOPS / SEARCH
# ---------------------------------------------------------
@api_view(["GET"])
def map_nearby_stations(request):
    try:
        user_lat = float(request.GET.get("lat"))
        user_lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return Response({"error": "lat and lng are required"}, status=400)

    radius = float(request.GET.get("radius", 10))  # km

    station_tuples = _get_nearby_station_tuples(user_lat, user_lng, radius)

    result = [
        {
            "id": st.id,
            "name": st.name,
            "latitude": st.latitude,
            "longitude": st.longitude,
            "distance_km": round(dist, 2),
        }
        for st, dist in station_tuples
    ]

    return Response(result)


def min_distance_to_route(station, route_points):
    distances = [
        calculate_distance(station.latitude, station.longitude, pt["lat"], pt["lng"])
        for pt in route_points
    ]
    return min(distances)


@api_view(["POST"])
def stations_along_route(request):
    route = request.data.get("route")
    radius = float(request.data.get("radius", 5))
    connector = request.data.get("connector")

    if not route:
        return Response({"error": "Route points required"}, status=400)

    qs = ChargingStation.objects.all()
    if connector:
        qs = qs.filter(connector_type=connector)

    result = []
    for st in qs:
        if is_station_near_route(st, route, radius):
            dist = min_distance_to_route(st, route)
            result.append({
                "id": st.id,
                "name": st.name,
                "lat": st.latitude,
                "lng": st.longitude,
                "distance_from_route": round(dist, 2),
                "available_slots": st.available_slots,
                "power_kw": st.power_kw,
                "price_per_kwh": st.price_per_kwh,
                "waiting_time": st.waiting_time,
            })

    return Response(result)


@api_view(["POST"])
def best_charge_stops(request):
    route = request.data.get("route")
    radius = float(request.data.get("radius", 5))
    max_stops = int(request.data.get("max_stops", 3))

    if not route:
        return Response({"error": "Route points required"}, status=400)

    candidates = []
    for st in ChargingStation.objects.all():
        if is_station_near_route(st, route, radius):
            dist = min_distance_to_route(st, route)
            score = (st.available_slots * 2) + (st.power_kw * 1.5) - (dist * 0.5)
            candidates.append({
                "id": st.id,
                "name": st.name,
                "distance_from_route": round(dist, 2),
                "available_slots": st.available_slots,
                "power_kw": st.power_kw,
                "score": round(score, 2)
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return Response(candidates[:max_stops])


@api_view(["GET"])
def station_search(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return Response([])

    stations = ChargingStation.objects.filter(name__icontains=q)[:20]
    result = [{"id": st.id, "name": st.name, "lat": st.latitude, "lng": st.longitude} for st in stations]
    return Response(result)


# ---------------------------------------------------------
# 11. DEVICE TOKEN (FCM)
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_device_token(request):
    token = request.data.get("token")
    if not token:
        return Response({"error": "token required"}, status=400)

    # store or update token for this user
    DeviceToken.objects.update_or_create(user=request.user, defaults={"token": token})

    return Response({"message": "Token saved"})


# ---------------------------------------------------------
# 12. P2P APIs
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def p2p_create_charger(request):
    data = request.data.copy()
    serializer = PeerChargerSerializer(data=data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
def p2p_nearby_chargers(request):
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return Response({"error": "lat and lng required"}, status=400)

    radius = float(request.GET.get("radius", 10))
    connector = request.GET.get("connector")

    chargers = PeerCharger.objects.filter(is_active=True)
    if connector:
        chargers = chargers.filter(connector_type=connector)

    result = []
    for ch in chargers:
        dist = calculate_distance(lat, lng, ch.latitude, ch.longitude)
        if dist <= radius:
            result.append({
                "id": ch.id,
                "name": ch.name,
                "owner": ch.owner.username,
                "latitude": ch.latitude,
                "longitude": ch.longitude,
                "connector_type": ch.connector_type,
                "power_kw": ch.power_kw,
                "price_per_kwh": ch.price_per_kwh,
                "distance_km": round(dist, 2),
            })

    result.sort(key=lambda x: x["distance_km"])
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def p2p_create_booking(request):
    charger_id = request.data.get("charger_id")
    start_time = request.data.get("start_time")
    end_time = request.data.get("end_time")

    if not all([charger_id, start_time, end_time]):
        return Response({"error": "charger_id, start_time, end_time required"}, status=400)

    try:
        charger = PeerCharger.objects.get(id=charger_id, is_active=True)
    except PeerCharger.DoesNotExist:
        return Response({"error": "Charger not found"}, status=404)

    try:
        start = parse_iso_datetime(start_time)
        end = parse_iso_datetime(end_time)
    except Exception:
        return Response({"error": "Invalid datetime format"}, status=400)

    if end <= start:
        return Response({"error": "Invalid time range"}, status=400)

    overlap = PeerBooking.objects.filter(
        charger=charger,
        status__in=["pending", "approved"],
        start_time__lt=end,
        end_time__gt=start,
    ).exists()

    if overlap:
        return Response({"error": "Slot not available for this charger"}, status=409)

    booking = PeerBooking.objects.create(
        renter=request.user,
        charger=charger,
        start_time=start,
        end_time=end,
        status="pending",
    )

    owner_tokens = DeviceToken.objects.filter(user=charger.owner)
    for t in owner_tokens:
        send_push_notification(
            t.token,
            title="New P2P booking request",
            body=f"{request.user.username} requested your charger '{charger.name}'",
        )

    return Response({"message": "Booking created, waiting for owner approval", "booking_id": booking.id})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def p2p_approve(request):
    booking_id = request.data.get("booking_id")
    action = request.data.get("action")  # "approve" or "reject"

    if not booking_id or action not in ["approve", "reject"]:
        return Response({"error": "booking_id and valid action required"}, status=400)

    try:
        booking = PeerBooking.objects.get(id=booking_id)
    except PeerBooking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    if booking.charger.owner != request.user:
        return Response({"error": "Not authorized"}, status=403)

    if booking.status != "pending":
        return Response({"error": "Booking already processed"}, status=400)

    booking.status = "approved" if action == "approve" else "rejected"
    booking.save()

    renter_tokens = DeviceToken.objects.filter(user=booking.renter)
    status_text = "approved" if action == "approve" else "rejected"
    for t in renter_tokens:
        send_push_notification(t.token, title=f"P2P booking {status_text}", body=f"Your booking for {booking.charger.name} was {status_text}.")

    return Response({"message": f"Booking {status_text}."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def p2p_my_bookings(request):
    qs = PeerBooking.objects.filter(renter=request.user).order_by("-start_time")
    serializer = PeerBookingSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def p2p_owner_requests(request):
    qs = PeerBooking.objects.filter(charger__owner=request.user, status="pending").order_by("-created_at")
    serializer = PeerBookingSerializer(qs, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------
# 13. Ratings & station info
# ---------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_station(request):
    station_id = request.data.get("station_id")
    rating = request.data.get("rating")

    if not station_id or rating is None:
        return Response({"error": "station_id and rating required"}, status=400)

    try:
        rating_val = int(rating)
    except (TypeError, ValueError):
        return Response({"error": "rating must be an integer 1-5"}, status=400)

    if rating_val < 1 or rating_val > 5:
        return Response({"error": "rating must be 1-5"}, status=400)

    try:
        station = ChargingStation.objects.get(id=station_id)
    except ChargingStation.DoesNotExist:
        return Response({"error": "Station not found"}, status=404)

    obj, created = StationRating.objects.update_or_create(
        user=request.user,
        station=station,
        defaults={"rating": rating_val},
    )

    return Response({"message": "Rating saved" if created else "Rating updated", "rating": rating_val})


from django.db.models import Avg, Count


@api_view(["GET"])
def station_rating(request, station_id):
    avg = StationRating.objects.filter(station_id=station_id).aggregate(avg=Avg("rating"))["avg"]
    return Response({"station_id": station_id, "avg_rating": round(avg or 0, 2)})


@api_view(["GET"])
def station_full_info(request):
    try:
        user_lat = float(request.GET.get("lat"))
        user_lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return Response({"error": "lat and lng required"}, status=400)

    try:
        radius = float(request.GET.get("radius", 20))
    except ValueError:
        return Response({"error": "radius must be a number"}, status=400)

    connector = request.GET.get("connector")
    charger_type = request.GET.get("charger_type")
    min_power = request.GET.get("min_power")
    max_price = request.GET.get("max_price")
    min_rating = request.GET.get("min_rating")
    sort_by = request.GET.get("sort", "distance")

    qs = ChargingStation.objects.all()
    if connector:
        qs = qs.filter(connector_type__iexact=connector)
    if charger_type:
        qs = qs.filter(charger_type__iexact=charger_type)
    if min_power:
        qs = qs.filter(power_kw__gte=float(min_power))
    if max_price:
        qs = qs.filter(price_per_kwh__lte=float(max_price))

    result = []
    for st in qs:
        dist = calculate_distance(user_lat, user_lng, st.latitude, st.longitude)
        if dist <= radius:
            rating = StationRating.objects.filter(station=st).aggregate(avg=Avg("rating"))["avg"]
            rating = round(rating or 0, 2)

            if min_rating and rating < float(min_rating):
                continue

            result.append({
                "id": st.id,
                "name": st.name,
                "latitude": st.latitude,
                "longitude": st.longitude,
                "connector_type": st.connector_type,
                "charger_type": st.charger_type,
                "power_kw": st.power_kw,
                "price_per_kwh": st.price_per_kwh,
                "available_slots": st.available_slots,
                "distance_km": round(dist, 2),
                "avg_rating": rating,
            })

    if sort_by == "distance":
        result.sort(key=lambda x: x["distance_km"])
    elif sort_by == "rating":
        result.sort(key=lambda x: x["avg_rating"], reverse=True)
    elif sort_by == "power":
        result.sort(key=lambda x: x["power_kw"], reverse=True)
    elif sort_by == "slots":
        result.sort(key=lambda x: x["available_slots"], reverse=True)
    elif sort_by == "price":
        result.sort(key=lambda x: x["price_per_kwh"])

    return Response(result)
