from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('content-report/', views.ContentReportView.as_view(), name='content-report'),
    path('script-pdf/<uuid:script_id>/', views.ScriptPdfView.as_view(), name='script-pdf'),
]
