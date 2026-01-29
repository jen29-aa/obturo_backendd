from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Car, UserCar
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class CarListView(APIView):
    def get(self, request):
        cars = Car.objects.all().values()
        return Response(list(cars))


class SelectCarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        car_id = request.data.get("car_id")

        try:
            car = Car.objects.get(id=car_id)
        except Car.DoesNotExist:
            return Response({"error": "Invalid car ID"}, status=400)

        user_car, created = UserCar.objects.get_or_create(user=request.user)
        user_car.car = car
        user_car.save()

        return Response({"message": "Car saved successfully"})


class SmartCarDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_car = UserCar.objects.get(user=request.user)
        except UserCar.DoesNotExist:
            return Response({"error": "No car selected"}, status=404)

        car = user_car.car

        if car.max_dc_power_kw >= 30:
            recommended = "DC Fast Charging"
            speed_kw = car.max_dc_power_kw
        else:
            recommended = "AC Slow Charging"
            speed_kw = car.max_ac_power_kw

        return Response({
            "name": car.name,
            "battery_capacity_kwh": car.battery_capacity_kwh,
            "connector_type": car.connector_type,
            "recommended_charger": recommended,
            "charging_speed_kw": speed_kw
        })

class SignupView(APIView):
    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        # Validate inputs
        if not username or not email or not password:
            return Response({"error": "Username, email, and password are required"}, status=400)

        if len(password) < 6:
            return Response({"error": "Password must be at least 6 characters"}, status=400)

        if len(username) < 3:
            return Response({"error": "Username must be at least 3 characters"}, status=400)

        if not ("@" in email and "." in email):
            return Response({"error": "Invalid email format"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=400)

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            return Response({"message": "User created successfully", "user_id": user.id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=400)

        user = User.objects.filter(username=username).first()

        if user is None or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=400)

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=200)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeviceToken

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_device_token(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "token is required"}, status=400)

    DeviceToken.objects.update_or_create(
        user=request.user,
        token=token,
    )

    return Response({"message": "Token saved"})
