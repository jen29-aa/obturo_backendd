from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Waitlist, Booking, ChargingStation
from accounts.models import DeviceToken
from .firebase import send_push_notification


# ---------------------------------------------------------
# Utility: Reorder waitlist (1..N)
# ---------------------------------------------------------
def reorder_waitlist(station):
    """
    Ensures waitlist positions are sequential (1, 2, 3, ...).
    Must be called after deleting/promoting entries.
    """
    entries = Waitlist.objects.filter(station=station).order_by("created_at", "id")

    with transaction.atomic():
        for idx, entry in enumerate(entries, start=1):
            if entry.position != idx:
                entry.position = idx
                entry.save(update_fields=["position"])


# ---------------------------------------------------------
# Estimate waiting time (very simple heuristic)
# ---------------------------------------------------------
def estimate_wait_time(station, user_position):
    """
    Predict waiting time in minutes:
    waiting_time ≈ position * average booking duration
    """
    recent = Booking.objects.filter(station=station, status="completed").order_by("-end_time")[:10]

    if recent.exists():
        durations = [(b.end_time - b.start_time).total_seconds() / 60.0 for b in recent]
        avg_duration = sum(durations) / len(durations)
    else:
        avg_duration = 30  # fallback default

    return round(user_position * avg_duration)


# ---------------------------------------------------------
# Promotion logic (used by scheduler + cancel handler)
# ---------------------------------------------------------
def promote_waitlist_for_station(station, notify=True, max_promote=None):
    """
    Promotes earliest users from waitlist into new bookings.
    Called by scheduler AND cancel_booking().
    """

    promoted_bookings = []
    promoted_users = []

    active_count = Booking.objects.filter(station=station, status="active").count()
    free_slots = station.total_slots - active_count
    if free_slots <= 0:
        return [], []

    to_promote = free_slots if max_promote is None else min(max_promote, free_slots)

    waiting = (
        Waitlist.objects
        .filter(station=station)
        .order_by("position", "created_at")[:to_promote]
    )

    for entry in waiting:
        with transaction.atomic():
            start = timezone.now() + timedelta(minutes=5)
            end = start + timedelta(minutes=30)

            booking = Booking.objects.create(
                user=entry.user,
                station=station,
                start_time=start,
                end_time=end,
                status="active",
            )

            promoted_bookings.append(booking.id)
            promoted_users.append(entry.user_id)

            entry.delete()

            # Notify promoted user
            if notify:
                tokens = DeviceToken.objects.filter(user=booking.user)
                for t in tokens:
                    send_push_notification(
                        t.token,
                        title="Slot Available",
                        body=f"You have been promoted from the waitlist at {station.name}. "
                             f"Slot from {start.strftime('%H:%M')} to {end.strftime('%H:%M')}.",
                    )

    reorder_waitlist(station)

    return promoted_bookings, promoted_users


# ---------------------------------------------------------
# API utility: Get user waitlist position + ETA
# ---------------------------------------------------------
def get_waitlist_info(user, station):
    """
    Returns user's waitlist position + estimated wait time.
    Used by get_waitlist_position API.
    """
    try:
        entry = Waitlist.objects.get(user=user, station=station)
    except Waitlist.DoesNotExist:
        return None

    position = entry.position
    eta = estimate_wait_time(station, position)

    return {
        "position": position,
        "estimated_wait_minutes": eta
    }
