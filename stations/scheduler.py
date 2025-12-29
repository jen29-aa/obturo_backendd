from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now, timedelta
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from accounts.models import DeviceToken
from .models import Booking, UserPenalty, Waitlist
from .firebase import send_push_notification


# ---------------------------------------------------------
# Helper: Add penalty to user
# ---------------------------------------------------------
def add_penalty(user, points):
    pen, _ = UserPenalty.objects.get_or_create(user=user)

    pen.penalty_points += points
    pen.no_show_count += 1

    # Auto-block rules
    if pen.penalty_points >= 5:
        pen.blocked_until = timezone.now() + timedelta(days=7)
    elif pen.penalty_points >= 3:
        pen.blocked_until = timezone.now() + timedelta(hours=24)

    pen.save()
    print(f"[Penalty] Penalty applied → {user.username} | Total = {pen.penalty_points}")


# ---------------------------------------------------------
# Queue Promotion Logic
# ---------------------------------------------------------
def promote_from_queue(station):
    next_user = (
        Waitlist.objects.filter(station=station, notified=False)
        .order_by("created_at")
        .first()
    )

    if not next_user:
        return

    tokens = DeviceToken.objects.filter(user=next_user.user)
    for t in tokens:
        send_push_notification(
            t.token,
            title="Charging Slot Available",
            body=f"A slot at {station.name} is available. Book within 10 minutes!"
        )

    next_user.notified = True
    next_user.save()

    print(f"[Queue] Notified {next_user.user.username} for {station.name}")


# ---------------------------------------------------------
# Reminder Notifications
# ---------------------------------------------------------
def send_booking_reminders():
    print("[Scheduler] Checking upcoming bookings...")

    upcoming = Booking.objects.filter(
        status="active",
        start_time__lte=now() + timedelta(minutes=10),
        start_time__gte=now()
    )

    print(f"[Scheduler] Upcoming bookings: {len(upcoming)}")

    for b in upcoming:
        tokens = DeviceToken.objects.filter(user=b.user)
        for t in tokens:
            send_push_notification(
                t.token,
                title="Charging Reminder",
                body=f"Your charging at {b.station.name} starts in 10 minutes."
            )


# ---------------------------------------------------------
# Auto-complete expired bookings + no-show penalty + queue
# ---------------------------------------------------------
def mark_completed_bookings():
    print(f"[Scheduler] Running mark_completed_bookings at {now()}")

    expired = Booking.objects.filter(
        status="active",
        end_time__lt=now()
    )

    print(f"[Scheduler] Found {len(expired)} expired bookings")

    for b in expired:

        # No-show penalty if user never started session
        if b.start_time + timedelta(minutes=10) < now():
            print(f"[Penalty] No-show → booking {b.id}")
            add_penalty(b.user, 1)

        # Mark booking completed
        b.status = "completed"
        b.save()
        print(f"[Scheduler] Marked booking {b.id} completed")

        # Free slot
        station = b.station
        station.available_slots += 1
        station.save()

        # Promote next from queue
        promote_from_queue(station)


# ---------------------------------------------------------
# APScheduler Startup Logic
# ---------------------------------------------------------
_scheduler = None

def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return

    print("[Scheduler] Starting APScheduler...")

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(send_booking_reminders, "interval", minutes=1)
    _scheduler.add_job(mark_completed_bookings, "interval", minutes=1)

    _scheduler.start()
