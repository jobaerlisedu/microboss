from django.urls import path
from . import views

app_name = 'leaders'

urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='leaderboard'),
    path('<uuid:user_id>/', views.UserEntriesDetailView.as_view(), name='leaderboard-user-detail'),
]
