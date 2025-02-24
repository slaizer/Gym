from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('my_gym_app.urls')),  # Ensure this matches your app's name
]

