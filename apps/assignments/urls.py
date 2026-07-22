from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.AssignmentListCreateView.as_view(), name='assignment-list'),
    path('<hexuuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),
    path('<hexuuid:pk>/status/', views.AssignmentUpdateStatusView.as_view(), name='assignment-status'),
    path('stats/', views.AssignmentStatsView.as_view(), name='assignment-stats'),
]
