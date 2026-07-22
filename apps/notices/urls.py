from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    path('', views.NoticeListAPIView.as_view(), name='notice-list'),
    path('<hexuuid:pk>/', views.NoticeDetailAPIView.as_view(), name='notice-detail'),
]
