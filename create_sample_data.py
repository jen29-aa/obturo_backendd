#!/usr/bin/env python
"""
Simple script to create sample charging stations if the database is empty
Run this if import_stations.py doesn't work or you want quick test data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obturo_backend.settings')
django.setup()

from stations.models import ChargingStation

# Sample stations data
SAMPLE_STATIONS = [
    {
        "name": "Delhi Charging Hub",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "address": "123 Rajpath, New Delhi",
        "charger_type": "DC",
        "connector_type": "CCS2",
        "power_kw": 50.0,
        "total_slots": 4,
        "available_slots": 2,
        "price_per_kwh": 18.0,
        "waiting_time": 5,
        "speed": 50,
        "status": "Available"
    },
    {
        "name": "Mumbai EV Station",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "address": "456 Marine Drive, Mumbai",
        "charger_type": "DC",
        "connector_type": "Type2",
        "power_kw": 30.0,
        "total_slots": 3,
        "available_slots": 1,
        "price_per_kwh": 20.0,
        "waiting_time": 10,
        "speed": 30,
        "status": "Available"
    },
    {
        "name": "Bangalore Fast Charge",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "address": "789 MG Road, Bangalore",
        "charger_type": "AC",
        "connector_type": "CCS2",
        "power_kw": 22.0,
        "total_slots": 5,
        "available_slots": 3,
        "price_per_kwh": 15.0,
        "waiting_time": 2,
        "speed": 22,
        "status": "Available"
    },
    {
        "name": "Hyderabad Power Station",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "address": "321 Hitech City, Hyderabad",
        "charger_type": "DC",
        "connector_type": "CHAdeMO",
        "power_kw": 60.0,
        "total_slots": 2,
        "available_slots": 1,
        "price_per_kwh": 19.0,
        "waiting_time": 8,
        "speed": 60,
        "status": "Available"
    },
    {
        "name": "Chennai Green Charge",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "address": "654 Nungambakkam, Chennai",
        "charger_type": "AC",
        "connector_type": "Type2",
        "power_kw": 11.0,
        "total_slots": 4,
        "available_slots": 2,
        "price_per_kwh": 16.0,
        "waiting_time": 3,
        "speed": 11,
        "status": "Available"
    },
]

def create_sample_stations():
    count = ChargingStation.objects.count()
    
    if count > 0:
        print(f"Database already has {count} stations. Skipping creation.")
        return
    
    print("Creating sample charging stations...")
    
    for station_data in SAMPLE_STATIONS:
        station = ChargingStation.objects.create(**station_data)
        print(f"  ✓ Created: {station.name}")
    
    print(f"\n✓ Successfully created {len(SAMPLE_STATIONS)} sample stations!")

if __name__ == "__main__":
    create_sample_stations()
