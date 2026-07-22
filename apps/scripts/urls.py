from django.urls import path
from . import views

app_name = 'scripts'

urlpatterns = [
    path('', views.ScriptListCreateView.as_view(), name='script-list'),
    path('<hexuuid:pk>/', views.ScriptDetailView.as_view(), name='script-detail'),
    path('<hexuuid:pk>/submit/', views.ScriptSubmitView.as_view(), name='script-submit'),
    path('<hexuuid:pk>/approve/', views.ScriptApproveView.as_view(), name='script-approve'),
    path('stats/', views.ScriptStatsView.as_view(), name='script-stats'),
]
