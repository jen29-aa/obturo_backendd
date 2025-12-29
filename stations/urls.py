from django.urls import path
from .views import (
    get_all_stations,
    get_nearby_stations,
    create_booking,
    SmartFilteredStations,
    topsis_custom,
    my_bookings,
    cancel_booking,
    get_profile,
    update_profile,
    toggle_favourite,
    list_favourites,
    map_nearby_stations,
    stations_along_route,
    best_charge_stops,
    station_search,
    save_device_token,
    # P2P:
    p2p_create_charger,
    p2p_nearby_chargers,
    p2p_create_booking,
    p2p_approve,
    p2p_my_bookings,
    p2p_owner_requests,
    rate_station,
    station_rating,
    station_full_info
)


urlpatterns = [
    # Stations
    path("stations/", get_all_stations),
    path("stations/nearby/", get_nearby_stations),

    # Booking
    path("book/", create_booking),
    path("bookings/my/", my_bookings),
    path("bookings/cancel/", cancel_booking),

    # Smart filter
    path("stations/smart/", SmartFilteredStations.as_view()),

    # TOPSIS
    path("stations/topsis/", topsis_custom),

    # Profile
    path("profile/", get_profile),
    path("profile/update/", update_profile),

    # Favourites
    path("favourites/toggle/", toggle_favourite),
    path("favourites/list/", list_favourites),

    # Map / route
    path("map/nearby/", map_nearby_stations),
    path("map/route/stations/", stations_along_route),
    path("map/route/best-stops/", best_charge_stops),
    path("map/search/", station_search),
    path("device-token/", save_device_token),

    # P2P sharing
    path("p2p/charger/create/", p2p_create_charger),
    path("p2p/chargers/nearby/", p2p_nearby_chargers),
    path("p2p/book/", p2p_create_booking),
    path("p2p/book/decision/", p2p_approve),
    path("p2p/bookings/my/", p2p_my_bookings),
    path("p2p/owner/requests/", p2p_owner_requests),

    #ratings
    path("stations/rate/", rate_station),
    path("stations/<int:station_id>/rating/", station_rating),

    path("stations/full-info/", station_full_info),


]


