"""
WebSocket URL routing
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/station/<int:station_id>/', consumers.StationSlotsConsumer.as_asgi()),
]
