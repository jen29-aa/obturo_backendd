import os
import django
import requests
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "obturo_backend.settings")
django.setup()

from stations.models import ChargingStation

url = "https://api.openchargemap.io/v3/poi/"
params = {
    "output": "json",
    "countrycode": "IN",
    "state": "kerala",
    "maxresults": 5000,
    "key": "96a9e6ad-babb-4c88-aab9-34d33cf7a276"
}

print("Fetching data from OpenChargeMap...")
response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))

# --- CHECK JSON ---
if "application/json" not in response.headers.get("Content-Type", ""):
    print("ERROR: API did NOT return JSON")
    print(response.text[:400])
    exit()

data = response.json()

count = 0

for station in data:
    addr = station.get("AddressInfo", {})
    
    state = (addr.get("StateOrProvince") or "").lower()
    if state != "kerala":
      continue


    ChargingStation.objects.create(
        name=addr.get("Title"),
        latitude=addr.get("Latitude"),
        longitude=addr.get("Longitude"),
        address=addr.get("AddressLine1"),
        total_slots=random.randint(2, 6),
        available_slots=random.randint(0, 3),
        waiting_time=random.randint(0, 15),
        price_per_kwh=random.randint(15, 24),
        speed=random.choice([7, 22, 30, 50, 60]),
        connector_type=random.choice(["CCS2", "Type2", "CHAdeMO"]),
        status=random.choice(["Available", "Busy"])
    )
    
    count += 1

print(f"Imported {count} Kerala EV charging stations!")
