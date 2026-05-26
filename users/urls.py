
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('sessions/', views.user_sessions, name='user_sessions'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/toggle-hidden/', views.toggle_hidden_games, name='toggle_hidden_games'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('profile/game/<int:game_id>/delete/', views.delete_game, name='delete_game'),
    path('', views.users_list, name='users_list'),
]
