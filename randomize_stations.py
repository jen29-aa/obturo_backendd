import random
from stations.models import ChargingStation

def randomize():
    connector_options = ["CCS2", "Type2", "CHAdeMO", "GB/T"]
    charger_type_options = ["AC", "DC"]
    power_options = [7, 11, 22, 30, 50, 60, 120, 150]

    stations = ChargingStation.objects.all()

    for st in stations:
        st.connector_type = random.choice(connector_options)
        st.charger_type = random.choice(charger_type_options)
        st.power_kw = random.choice(power_options)

        st.available_slots = random.randint(1, st.total_slots)
        st.speed = random.randint(30, 100)
        st.waiting_time = random.randint(1, 20)

        st.save()

    print("✔ Stations randomized successfully.")
