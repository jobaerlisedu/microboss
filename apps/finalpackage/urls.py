from django.urls import path
from . import views

app_name = 'finalpackage'

urlpatterns = [
    path('', views.FinalPackageListCreateView.as_view(), name='finalpackage-list'),
    path('<hexuuid:pk>/', views.FinalPackageDetailView.as_view(), name='finalpackage-detail'),
    path('stats/', views.FinalPackageStatsView.as_view(), name='finalpackage-stats'),
]
