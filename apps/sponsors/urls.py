from django.urls import path
from . import views

app_name = 'sponsors'

urlpatterns = [
    path('', views.SponsorListCreateView.as_view(), name='sponsor-list'),
    path('<hexuuid:pk>/', views.SponsorDetailView.as_view(), name='sponsor-detail'),
    path('track/', views.SponsorTrackView.as_view(), name='sponsor-track'),
]
