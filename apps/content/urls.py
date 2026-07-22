from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('', views.ContentEntryListCreateView.as_view(), name='entry-list'),
    path('<hexuuid:pk>/', views.ContentEntryDetailView.as_view(), name='entry-detail'),
    path('stats/', views.ContentEntryStatsView.as_view(), name='entry-stats'),
    path('by-month/<int:year>/<int:month>/', views.ContentEntryByMonthView.as_view(), name='entry-by-month'),
]
