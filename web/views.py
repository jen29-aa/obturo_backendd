import requests
import math
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from accounts.models import UserCar, Car

API_BASE = "http://127.0.0.1:8000"  # backend base URL


def get_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        res = requests.post(
            f"{API_BASE}/auth/login/",
            json={"username": username, "password": password}
        )

        if res.status_code == 200:
            data = res.json()
            request.session["token"] = data["access"]
            request.session["username"] = username
            request.session.save()
            return redirect("home")

        return render(request, "web/login.html", {"error": "Invalid credentials"})

    return render(request, "web/login.html")

def get_current_user(token):
    """Get current user from token"""
    try:
        res = requests.get(
            f"{API_BASE}/auth/user/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def select_car(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")
    
    # Get the current user from database
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")
    
    # Get current car if exists
    current_car = None
    try:
        user_car = UserCar.objects.get(user=user)
        current_car = user_car.car
    except UserCar.DoesNotExist:
        pass
    
    # Handle POST request to save selected car
    if request.method == "POST":
        car_id = request.POST.get("car_id")
        if car_id:
            try:
                car = Car.objects.get(id=car_id)
                user_car, created = UserCar.objects.update_or_create(
                    user=user,
                    defaults={"car": car}
                )
                # If coming from profile, go back to profile
                next_page = request.GET.get('next', 'stations')
                return redirect(next_page)
            except Car.DoesNotExist:
                pass

    res = requests.get(
        f"{API_BASE}/auth/cars/",
        headers={"Authorization": f"Bearer {token}"}
    )

    if res.status_code == 200:
        cars = res.json()
    else:
        cars = []

    return render(request, "web/select_car.html", {
        "cars": cars,
        "current_car": current_car,
        "username": username
    })



def stations_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    # Get the current user from database
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    # Get selected car
    selected_car = None
    try:
        user_car = UserCar.objects.get(user=user)
        selected_car = user_car.car
    except UserCar.DoesNotExist:
        return redirect("select_car")

    # Get filter parameters
    keyword = request.GET.get("q", "")
    charger_type = request.GET.get("charger_type", "")
    connector_type = request.GET.get("connector_type", "")
    min_power = request.GET.get("min_power", "")
    max_price = request.GET.get("max_price", "")
    user_lat = request.GET.get("lat", "")
    user_lon = request.GET.get("lon", "")
    radius = request.GET.get("radius", "50")  # Default 50 km radius

    # If no search query and no location, show message
    error_msg = None
    if not keyword and not user_lat:
        error_msg = "Please search for a city or use your location to find stations."

    res = requests.get(
        f"{API_BASE}/api/map/search/",
        params={"q": keyword if keyword else ""},
    )

    stations = res.json() if res.status_code == 200 else []
    
    # Calculate distances if user location provided
    if user_lat and user_lon:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            radius = float(radius)
            
            for station in stations:
                if "latitude" in station and "longitude" in station:
                    distance = get_distance(user_lat, user_lon, float(station["latitude"]), float(station["longitude"]))
                    station["distance"] = round(distance, 2)
            
            # Debug: print stations with distances
            print(f"DEBUG: User location: {user_lat}, {user_lon}, Radius: {radius}")
            print(f"DEBUG: Total stations: {len(stations)}")
            stations_with_dist = [s for s in stations if s.get("distance") is not None]
            print(f"DEBUG: Stations with distance calculated: {len(stations_with_dist)}")
            if stations_with_dist:
                print(f"DEBUG: First station distance: {stations_with_dist[0].get('distance')}")
            
            # Filter by radius - only include stations with calculated distance
            stations = [s for s in stations if s.get("distance") is not None and s.get("distance", 999) <= radius]
            print(f"DEBUG: Stations after radius filter ({radius}km): {len(stations)}")
            
            # Sort by distance
            stations = sorted(stations, key=lambda x: x.get("distance", 999))
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error in distance calculation: {e}")
            pass
    
    # Apply other filters
    if charger_type:
        stations = [s for s in stations if s.get("charger_type", "DC") == charger_type]
    if connector_type:
        stations = [s for s in stations if s.get("connector_type", "CCS2") == connector_type]
    if min_power:
        try:
            min_power_val = float(min_power)
            stations = [s for s in stations if s.get("power_kw", 30) >= min_power_val]
        except:
            pass
    if max_price:
        try:
            max_price_val = float(max_price)
            stations = [s for s in stations if s.get("price_per_kwh", 18) <= max_price_val]
        except:
            pass
    
    # Get unique values for filters
    all_stations = res.json() if res.status_code == 200 else []
    charger_types = list(set([s.get("charger_type", "DC") for s in all_stations]))
    connector_types = list(set([s.get("connector_type", "CCS2") for s in all_stations]))
    
    # Debug info
    print(f"DEBUG: Final stations count: {len(stations)}")
    print(f"DEBUG: Error message: {error_msg}")
    print(f"DEBUG: Has location: {bool(user_lat and user_lon)}")
    
    return render(request, "web/stations.html", {
        "stations": stations,
        "selected_car": selected_car,
        "charger_types": sorted(charger_types),
        "connector_types": sorted(connector_types),
        "current_filters": {
            "q": keyword,
            "charger_type": charger_type,
            "connector_type": connector_type,
            "min_power": min_power,
            "max_price": max_price,
            "lat": user_lat,
            "lon": user_lon,
            "radius": radius,
        },
        "has_location": bool(user_lat and user_lon),
        "error_msg": error_msg,
        "auth_token": token,
    })


def station_detail_view(request):
    """Display detailed information for a specific station"""
    token = request.session.get("token")
    if not token:
        return redirect("login")
    
    return render(request, "web/station_detail.html", {
        "auth_token": token,
        "username": request.session.get("username")
    })


def analytics_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")
    
    return render(request, "web/analytics.html", {
        "auth_token": token,
        "username": username
    })


def charging_session_view(request):
    """Display active charging session page"""
    token = request.session.get("token")
    if not token:
        return redirect("login")
    
    return render(request, "web/charging_session.html", {
        "auth_token": token,
        "username": request.session.get("username")
    })


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        # Validate inputs
        if not all([username, email, password, password_confirm]):
            return render(request, "web/signup.html", {"error": "All fields are required"})

        if len(password) < 6:
            return render(request, "web/signup.html", {"error": "Password must be at least 6 characters"})

        if password != password_confirm:
            return render(request, "web/signup.html", {"error": "Passwords do not match"})

        if "@" not in email:
            return render(request, "web/signup.html", {"error": "Invalid email address"})

        res = requests.post(
            f"{API_BASE}/auth/signup/",
            json={"username": username, "email": email, "password": password}
        )

        if res.status_code == 200 or res.status_code == 201:
            # Auto login after signup
            login_res = requests.post(
                f"{API_BASE}/auth/login/",
                json={"username": username, "password": password}
            )
            if login_res.status_code == 200:
                data = login_res.json()
                request.session["token"] = data["access"]
                request.session["username"] = username
                request.session.save()
                return redirect("home")
            return redirect("login")
        else:
            try:
                error = res.json().get("error", "Signup failed")
            except:
                error = "Signup failed. Please try again."
            return render(request, "web/signup.html", {"error": error})

    return render(request, "web/signup.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")


def dashboard_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    selected_car = None
    try:
        user_car = UserCar.objects.get(user=user)
        selected_car = user_car.car
    except UserCar.DoesNotExist:
        pass

    # Get bookings
    bookings_res = requests.get(
        f"{API_BASE}/api/bookings/my/",
        headers={"Authorization": f"Bearer {token}"}
    )
    bookings = bookings_res.json() if bookings_res.status_code == 200 else []

    # Get favorites
    favorites_res = requests.get(
        f"{API_BASE}/api/favourites/list/",
        headers={"Authorization": f"Bearer {token}"}
    )
    favorites = favorites_res.json() if favorites_res.status_code == 200 else []

    return render(request, "web/dashboard.html", {
        "selected_car": selected_car,
        "bookings_count": len(bookings),
        "favorites_count": len(favorites),
        "recent_bookings": bookings[:3],
        "username": username,
        "auth_token": token,
    })


def bookings_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    error_msg = None

    # Handle cancel booking POST request
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        
        if action == "cancel" and booking_id:
            cancel_res = requests.post(
                f"{API_BASE}/api/bookings/cancel/",
                json={"booking_id": int(booking_id)},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if cancel_res.status_code == 200:
                return redirect("bookings")  # Reload to show updated status
            else:
                error_msg = cancel_res.json().get("error", "Failed to cancel booking")
                print(f"Cancel error: {error_msg}")
    
    # Get bookings
    bookings_res = requests.get(
        f"{API_BASE}/api/bookings/my/",
        headers={"Authorization": f"Bearer {token}"}
    )
    bookings = bookings_res.json() if bookings_res.status_code == 200 else []

    return render(request, "web/bookings.html", {
        "bookings": bookings,
        "username": username,
        "auth_token": token,
        "error_msg": error_msg,
    })


def profile_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    selected_car = None
    try:
        user_car = UserCar.objects.get(user=user)
        selected_car = user_car.car
    except UserCar.DoesNotExist:
        pass

    return render(request, "web/profile.html", {
        "user": user,
        "selected_car": selected_car,
        "username": username
    })


def favorites_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    # Get favorites
    favorites_res = requests.get(
        f"{API_BASE}/api/favourites/list/",
        headers={"Authorization": f"Bearer {token}"}
    )
    favorites = favorites_res.json() if favorites_res.status_code == 200 else []

    return render(request, "web/favorites.html", {
        "favorites": favorites,
        "username": username,
        "auth_token": token,
    })


def peer_chargers_view(request):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    # Get peer chargers nearby
    chargers_res = requests.get(
        f"{API_BASE}/api/p2p/chargers/nearby/",
        headers={"Authorization": f"Bearer {token}"}
    )
    chargers = chargers_res.json() if chargers_res.status_code == 200 else []

    return render(request, "web/peer_chargers.html", {
        "chargers": chargers,
        "username": username,
        "auth_token": token,
    })


def book_station_view(request, station_id):
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    if request.method == "POST":
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        book_res = requests.post(
            f"{API_BASE}/api/book/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "station_id": station_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )

        if book_res.status_code == 200:
            return redirect("bookings")
        else:
            error = book_res.json().get("error", "Booking failed")
            return render(request, "web/book.html", {"error": error, "station_id": station_id})

    return render(request, "web/book.html", {"station_id": station_id})


def ranking_view(request):
    """Smart station ranking with custom TOPSIS weights"""
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        redirect("login")

    # Get selected car
    selected_car = None
    try:
        user_car = UserCar.objects.get(user=user)
        selected_car = user_car.car
    except UserCar.DoesNotExist:
        pass

    # Get location parameters
    user_lat = request.GET.get("lat", "")
    user_lon = request.GET.get("lon", "")
    radius = request.GET.get("radius", "50")

    return render(request, "web/ranking.html", {
        "selected_car": selected_car,
        "auth_token": token,
        "username": username,
        "current_filters": {
            "lat": user_lat,
            "lon": user_lon,
            "radius": radius,
        },
        "has_location": bool(user_lat and user_lon),
    })


def route_map_view(request):
    """Route map page: show route between source and destination with available stations along route"""
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")

    # Provide auth token to template for booking calls if needed
    return render(request, "web/route_map.html", {
        "user": user,
        "auth_token": token,
    })


def home_view(request):
    """Home page with all features overview"""
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")
    
    # Check if user has selected a car
    try:
        UserCar.objects.get(user=user)
    except UserCar.DoesNotExist:
        # New user needs to select a car first
        return redirect("select_car")

    return render(request, "web/home.html", {
        "user": user,
        "auth_token": token,
    })


def geocode_view(request):
    """Proxy endpoint for geocoding to avoid CORS issues"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'error': 'Query parameter required'}, status=400)
    
    try:
        import requests
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&limit=1"
        headers = {'User-Agent': 'Obturo EV Charging App'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return JsonResponse({
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'display_name': data[0]['display_name']
                })
            return JsonResponse({'error': 'No results found'}, status=404)
        return JsonResponse({'error': f'Geocoding service error: {response.status_code}'}, status=response.status_code)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def admin_dashboard_view(request):
    """Admin dashboard page"""
    token = request.session.get("token")
    username = request.session.get("username")
    
    if not token:
        return redirect("login")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("login")
    
    # Check if user is staff/admin
    if not user.is_staff:
        return redirect("home")
    
    return render(request, "web/admin_dashboard.html", {
        "username": username,
        "auth_token": token,
    })
