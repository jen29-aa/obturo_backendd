from django.urls import path
from .views import LoginView,SignupView, CarListView, SelectCarView, SmartCarDetailsView
from .views import save_device_token 

urlpatterns = [
    path('cars/', CarListView.as_view()),
    path('select-car/', SelectCarView.as_view()),
    path('car-details/', SmartCarDetailsView.as_view()),
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path("device-token/", save_device_token),
]
