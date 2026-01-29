"""
Station Data Population Script
================================
This script provides utilities to populate charging station details
such as images, ratings, facilities, and contact information.

Note: Actual web scraping of real station data would require:
1. Identifying data sources (Tata Power website, Google Maps, etc.)
2. Web scraping libraries (BeautifulSoup, Selenium)
3. Handling anti-scraping measures
4. Legal compliance with terms of service

This script provides a template for manual/programmatic data entry.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obturo_backend.settings')
django.setup()

from stations.models import ChargingStation
from django.utils import timezone


def populate_sample_data():
    """
    Populate first 5 stations with sample data to demonstrate the feature.
    In production, you would:
    - Use web scraping APIs
    - Integrate with Tata Power APIs if available
    - Manual data entry through admin interface
    - Import from CSV/JSON files
    """
    
    # Get first 5 stations
    stations = ChargingStation.objects.all()[:5]
    
    # Sample data templates
    sample_images = [
        "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=1200",  # EV charging station
        "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=1200",  # Modern charging
        "https://images.unsplash.com/photo-1614030424754-24d0eebd46b2?w=1200",  # Tesla charger
        "https://images.unsplash.com/photo-1609743522471-83c84ce23e32?w=1200",  # Charging plug
        "https://images.unsplash.com/photo-1617886322207-7859ace658eb?w=1200",  # EV station
    ]
    
    sample_descriptions = [
        "Premium charging facility with modern amenities. Located at a convenient location with easy access from the highway.",
        "Fast charging station equipped with latest technology. Perfect for quick stops during long journeys.",
        "Family-friendly charging hub with comfortable waiting area and refreshments available nearby.",
        "High-power charging station ideal for rapid charging. Well-maintained facility with 24/7 security.",
        "Conveniently located charging point with ample parking space and nearby shopping facilities.",
    ]
    
    for i, station in enumerate(stations):
        station.image_url = sample_images[i]
        station.description = sample_descriptions[i]
        station.phone_number = f"+91 {8000000000 + i}"
        station.email = f"support.station{station.id}@tatapower.com"
        station.operating_hours = "24/7"
        station.is_open_24_7 = True
        station.has_parking = True
        station.has_restroom = True
        station.has_cafe = i % 2 == 0  # Every other station has cafe
        station.has_wifi = True
        station.facilities = "ATM, Security Camera, Well Lit"
        station.verified = True
        station.last_updated = timezone.now()
        station.save()
        
        print(f"✓ Updated: {station.name}")
    
    print(f"\n✅ Successfully populated data for {len(stations)} stations")


def bulk_update_from_csv(csv_file):
    """
    Template function to bulk update stations from CSV file.
    
    CSV Format:
    station_id,image_url,description,phone_number,email,operating_hours,facilities,has_parking,has_restroom,has_cafe,has_wifi
    """
    import csv
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        updated_count = 0
        
        for row in reader:
            try:
                station = ChargingStation.objects.get(id=row['station_id'])
                
                # Update fields if provided
                if row.get('image_url'):
                    station.image_url = row['image_url']
                if row.get('description'):
                    station.description = row['description']
                if row.get('phone_number'):
                    station.phone_number = row['phone_number']
                if row.get('email'):
                    station.email = row['email']
                if row.get('operating_hours'):
                    station.operating_hours = row['operating_hours']
                if row.get('facilities'):
                    station.facilities = row['facilities']
                
                # Boolean fields
                station.has_parking = row.get('has_parking', '').lower() == 'true'
                station.has_restroom = row.get('has_restroom', '').lower() == 'true'
                station.has_cafe = row.get('has_cafe', '').lower() == 'true'
                station.has_wifi = row.get('has_wifi', '').lower() == 'true'
                
                station.verified = True
                station.last_updated = timezone.now()
                station.save()
                
                updated_count += 1
                print(f"✓ Updated station {station.id}: {station.name}")
                
            except ChargingStation.DoesNotExist:
                print(f"✗ Station {row['station_id']} not found")
            except Exception as e:
                print(f"✗ Error updating station {row.get('station_id')}: {e}")
        
        print(f"\n✅ Successfully updated {updated_count} stations from CSV")


def create_sample_csv():
    """Create a sample CSV file template for bulk updates"""
    import csv
    
    filename = 'station_data_template.csv'
    
    # Get first 10 stations
    stations = ChargingStation.objects.all()[:10]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'station_id', 'name', 'image_url', 'description', 'phone_number', 
            'email', 'operating_hours', 'facilities', 'has_parking', 
            'has_restroom', 'has_cafe', 'has_wifi'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for station in stations:
            writer.writerow({
                'station_id': station.id,
                'name': station.name,
                'image_url': '',
                'description': '',
                'phone_number': '',
                'email': '',
                'operating_hours': '24/7',
                'facilities': '',
                'has_parking': 'true',
                'has_restroom': 'true',
                'has_cafe': 'false',
                'has_wifi': 'true'
            })
    
    print(f"✅ Created template CSV file: {filename}")
    print(f"   Contains {len(stations)} stations ready for data entry")


def set_all_24_7():
    """Set all stations to 24/7 operation (common for Tata Power stations)"""
    count = ChargingStation.objects.update(
        is_open_24_7=True,
        operating_hours="24/7",
        last_updated=timezone.now()
    )
    print(f"✅ Set {count} stations to 24/7 operation")


def set_basic_facilities():
    """Set basic facilities for all stations (common amenities)"""
    count = ChargingStation.objects.update(
        has_parking=True,
        has_restroom=True,
        has_wifi=True,
        has_cafe=False,
        facilities="24/7 Security, CCTV Surveillance, Well Lit Area",
        verified=True,
        last_updated=timezone.now()
    )
    print(f"✅ Set basic facilities for {count} stations")


def show_statistics():
    """Show statistics about station data completeness"""
    total = ChargingStation.objects.count()
    
    stats = {
        'Total Stations': total,
        'With Images': ChargingStation.objects.exclude(image_url__isnull=True).exclude(image_url='').count(),
        'With Description': ChargingStation.objects.exclude(description__isnull=True).exclude(description='').count(),
        'With Phone': ChargingStation.objects.exclude(phone_number__isnull=True).exclude(phone_number='').count(),
        'With Email': ChargingStation.objects.exclude(email__isnull=True).exclude(email='').count(),
        'Verified': ChargingStation.objects.filter(verified=True).count(),
        '24/7 Open': ChargingStation.objects.filter(is_open_24_7=True).count(),
        'With Parking': ChargingStation.objects.filter(has_parking=True).count(),
        'With WiFi': ChargingStation.objects.filter(has_wifi=True).count(),
    }
    
    print("\n" + "=" * 50)
    print("STATION DATA COMPLETENESS")
    print("=" * 50)
    
    for key, value in stats.items():
        percentage = (value / total * 100) if total > 0 else 0
        print(f"{key:20}: {value:4} / {total} ({percentage:5.1f}%)")
    
    print("=" * 50 + "\n")


def add_ratings_to_all_stations():
    """Add sample ratings to all stations"""
    from stations.models import StationRating
    from accounts.models import User
    import random
    
    stations = ChargingStation.objects.all()
    users = list(User.objects.all()[:20])  # Use first 20 users
    
    if not users:
        print("❌ No users found. Create some users first.")
        return
    
    ratings_added = 0
    stations_updated = 0
    
    for station in stations:
        # Add 3-7 random ratings per station (even if some exist)
        num_ratings = random.randint(3, 7)
        current_ratings = StationRating.objects.filter(station=station).count()
        
        if current_ratings < num_ratings:
            for i in range(num_ratings - current_ratings):
                try:
                    user = random.choice(users)
                    rating = random.randint(3, 5)  # Ratings from 3-5 stars
                    
                    # Create or get - unique per user per station
                    sr, created = StationRating.objects.get_or_create(
                        user=user,
                        station=station,
                        defaults={'rating': rating}
                    )
                    if created:
                        ratings_added += 1
                except Exception as e:
                    pass
            
            if ratings_added > current_ratings:
                stations_updated += 1
    
    print(f"✅ Added {ratings_added} new ratings")
    print(f"✅ {stations_updated} stations updated")



if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("OBTURO STATION DATA POPULATION UTILITY")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sample":
            print("Populating sample data for first 5 stations...\n")
            populate_sample_data()
            
        elif command == "csv":
            if len(sys.argv) > 2:
                print(f"Importing data from {sys.argv[2]}...\n")
                bulk_update_from_csv(sys.argv[2])
            else:
                print("Error: Please provide CSV filename")
                print("Usage: python populate_station_data.py csv <filename.csv>")
                
        elif command == "template":
            print("Creating CSV template...\n")
            create_sample_csv()
            
        elif command == "24-7":
            print("Setting all stations to 24/7 operation...\n")
            set_all_24_7()
            
        elif command == "facilities":
            print("Setting basic facilities for all stations...\n")
            set_basic_facilities()
            
        elif command == "stats":
            show_statistics()
            
        elif command == "ratings":
            print("Adding ratings to all stations...\n")
            add_ratings_to_all_stations()
            
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage instructions"""
    print("Available commands:")
    print()
    print("  sample      - Populate first 5 stations with sample data")
    print("  csv <file>  - Bulk import from CSV file")
    print("  template    - Create a CSV template file")
    print("  24-7        - Set all stations to 24/7 operation")
    print("  facilities  - Set basic facilities for all stations")
    print("  ratings     - Add random ratings to all stations")
    print("  stats       - Show data completeness statistics")
    print()
    print("Examples:")
    print("  python populate_station_data.py sample")
    print("  python populate_station_data.py template")
    print("  python populate_station_data.py csv station_data.csv")
    print("  python populate_station_data.py ratings")
    print("  python populate_station_data.py stats")
    print()
