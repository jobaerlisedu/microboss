from django.urls import path
from . import views

app_name = 'contentlist'

urlpatterns = [
    path('', views.ContentListListCreateView.as_view(), name='contentlist-list'),
    path('<hexuuid:pk>/', views.ContentListDetailView.as_view(), name='contentlist-detail'),
    path('stats/', views.ContentListStatsView.as_view(), name='contentlist-stats'),
]
