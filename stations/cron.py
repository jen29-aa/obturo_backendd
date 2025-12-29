from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from stations.models import ChargingStation, Booking
import random

def update_station_status():
    print("Running charger simulation job...")

    stations = ChargingStation.objects.all()

    for st in stations:
        # 1. Free slots from completed bookings
        active_bookings = Booking.objects.filter(
            station_id=st.id,
            status="active",
            end_time__lt=timezone.now()
        )

        if active_bookings.exists():
            for bk in active_bookings:
                bk.status = "completed"
                bk.save()
                st.available_slots = min(st.available_slots + 1, st.total_slots)

        # 2. Random "AI-like" simulation
        # Randomly free or occupy slots
        if random.random() < 0.5 and st.available_slots < st.total_slots:
            st.available_slots += 1

        if random.random() < 0.3 and st.available_slots > 0:
            st.available_slots -= 1

        # Random waiting time (simulate rush hours)
        st.waiting_time = random.randint(1, 15)

        # Random status
        st.status = random.choice(["Available", "Busy"])

        st.save()

    print("Charger simulation updated successfully.")


def start_scheduler():
    scheduler = BackgroundScheduler()
    # run every 2 minutes
    scheduler.add_job(update_station_status, "interval", minutes=2)
    scheduler.start()
