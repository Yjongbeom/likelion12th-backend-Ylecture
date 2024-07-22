from django.contrib import admin
from django.urls import path

from custom_auth.views import AuthAPIView, RegisterAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', AuthAPIView.as_view()),
    path('register/', RegisterAPIView.as_view()),
]
