app_name = 'games'

from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_list, name='game_list'),

    path('play/<int:session_id>/', views.play, name='game_play'),
    path('end/<int:session_id>/', views.game_end, name='game_end'),
    
    path('start/<int:game_id>/', views.start_game, name='start'),
    path('start_new/<int:game_id>/', views.start_new_game, name='start_new_game'),
    path('surrender/<int:session_id>/', views.surrender_game, name='surrender_game'),
    path('surrender_all/', views.surrender_all_active_games, name='surrender_all_active_games'),

    path('leaderboard/', views.leaderboard, name='leaderboard'),
    # Последний games - Страница игры
    path('<slug:game_slug>/', views.game_detail, name='game_detail'),
]
