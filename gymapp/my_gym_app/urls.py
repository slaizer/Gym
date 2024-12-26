from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='root'),  # Handle root URL ("/") by showing the login page
    path('login/', views.login_page, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
