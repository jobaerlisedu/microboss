from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_api, name='analytics-dashboard'),
    path('content-trend/', views.content_trend_api, name='analytics-content-trend'),
    path('platform-breakdown/', views.platform_breakdown_api, name='analytics-platform'),
    path('member-performance/', views.member_performance_api, name='analytics-members'),
    path('kpi-summary/', views.kpi_summary_api, name='analytics-kpi'),
    path('assignment-metrics/', views.assignment_metrics_api, name='analytics-assignments'),
    path('script-metrics/', views.script_metrics_api, name='analytics-scripts'),
    path('sponsored-organic/', views.sponsored_vs_organic_api, name='analytics-sponsored'),
    path('monthly-comparison/', views.monthly_comparison_api, name='analytics-comparison'),
    path('user-activity/', views.user_activity_api, name='analytics-activity'),
    path('export/csv/', views.export_csv_api, name='analytics-export-csv'),
    path('daily-trend/', views.daily_trend_api, name='analytics-daily-trend'),
    path('content-list-stats/', views.content_list_stats_api, name='analytics-content-list'),
]
