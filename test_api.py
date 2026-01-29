#!/usr/bin/env python
"""
Quick API test script to verify the station search endpoint works
"""
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("Testing Obturo Backend API")
print("=" * 60)

# Test 1: Get all stations (no search query)
print("\n1. Testing station search (no query - should return all stations)")
try:
    res = requests.get(f"{API_BASE}/api/map/search/")
    print(f"   Status Code: {res.status_code}")
    if res.status_code == 200:
        stations = res.json()
        print(f"   ✓ Returned {len(stations)} stations")
        if stations:
            first_station = stations[0]
            print(f"   First station: {first_station.get('name', 'N/A')}")
            print(f"   Fields returned: {list(first_station.keys())}")
            print(f"   Full first station:\n{json.dumps(first_station, indent=2)}")
    else:
        print(f"   ✗ Error: {res.text}")
except Exception as e:
    print(f"   ✗ Exception: {e}")

# Test 2: Search by city
print("\n2. Testing station search with query 'Delhi'")
try:
    res = requests.get(f"{API_BASE}/api/map/search/", params={"q": "Delhi"})
    print(f"   Status Code: {res.status_code}")
    if res.status_code == 200:
        stations = res.json()
        print(f"   ✓ Returned {len(stations)} stations for 'Delhi'")
    else:
        print(f"   ✗ Error: {res.text}")
except Exception as e:
    print(f"   ✗ Exception: {e}")

# Test 3: Check if database has stations
print("\n3. Checking database directly...")
try:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obturo_backend.settings')
    import django
    django.setup()
    
    from stations.models import ChargingStation
    count = ChargingStation.objects.count()
    print(f"   ✓ Database has {count} charging stations")
    
    if count > 0:
        sample = ChargingStation.objects.first()
        print(f"   Sample station: {sample.name}")
        print(f"   - Address: {sample.address}")
        print(f"   - Lat/Lon: {sample.latitude}, {sample.longitude}")
        print(f"   - Charger Type: {sample.charger_type}")
        print(f"   - Power: {sample.power_kw} kW")
except Exception as e:
    print(f"   ✗ Exception: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
