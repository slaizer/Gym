from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='root'),
    path('login/', views.login_page, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-courses/<str:username>/', views.manage_courses, name='manage_courses'),
    path('assign-users/', views.assign_users, name='assign_users'),  # New feature
    path('logout/', views.logout_view, name='logout'),
    path('manage-workouts/<str:username>/', views.manage_workouts, name='manage_workouts'),
    path('manage-food/<str:username>/', views.manage_food, name='manage_food'),
    path('captin-manage-users/', views.captin_manage_users, name='captin_manage_users'),
    path('captin/workout-videos/', views.manage_workout_videos, name='manage_workout_videos'),
    path('captin/cooking-videos/', views.manage_cooking_videos, name='manage_cooking_videos'),
    path('captin/workout-videos/', views.manage_workout_videos, name='manage_workout_videos'),
    path('captin/cooking-videos/', views.manage_cooking_videos, name='manage_cooking_videos'),
    path('upload-video/', views.upload_video_link, name='upload_video_link'),  # New video upload URL
    path('remove-video/<str:video_type>/<int:video_id>/', views.remove_video, name='remove_video'),
    path('base/', views.base_page, name='base_page'),
    path('update-weight/', views.update_weight, name='update_weight'),

]
