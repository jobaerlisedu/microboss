from datetime import date, timedelta
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .services import AnalyticsService, get_dashboard_data


def _parse_date_params(request):
    today = timezone.now().date()
    days = request.GET.get('days', '30')
    start = request.GET.get('start')
    end = request.GET.get('end')
    period = request.GET.get('period', '')
    if period == 'week':
        start = today - timedelta(days=7)
        end = today
    elif period == 'quarter':
        start = today - timedelta(days=90)
        end = today
    elif period == 'year':
        start = today.replace(month=1, day=1)
        end = today
    elif start and end:
        start = date.fromisoformat(start)
        end = date.fromisoformat(end)
    else:
        try:
            d = int(days)
        except (ValueError, TypeError):
            d = 30
        start = today - timedelta(days=d)
        end = today
    return start, end


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    period = request.GET.get('period', 'month')
    data = get_dashboard_data(period=period)
    return JsonResponse(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_trend_api(request):
    start, end = _parse_date_params(request)
    interval = request.GET.get('interval', 'day')
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.content_trend(interval=interval))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def platform_breakdown_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.platform_breakdown())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def member_performance_api(request):
    start, end = _parse_date_params(request)
    limit = int(request.GET.get('limit', 10))
    svc = AnalyticsService(start_date=start, end_date=end)
    members = svc.member_performance(limit=limit)
    return JsonResponse({'members': members})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kpi_summary_api(request):
    svc = AnalyticsService()
    return JsonResponse(svc.kpi_summary())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assignment_metrics_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.assignment_metrics())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def script_metrics_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.script_metrics())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sponsored_vs_organic_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.sponsored_vs_organic())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_comparison_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.monthly_comparison())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_api(request):
    days = int(request.GET.get('days', 7))
    limit = int(request.GET.get('limit', 20))
    svc = AnalyticsService()
    return JsonResponse({'activity': svc.user_activity_timeline(days=days, limit=limit)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    csv_content = svc.export_summary_csv()
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="analytics-{start}-to-{end}.csv"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_trend_api(request):
    days = int(request.GET.get('days', 7))
    svc = AnalyticsService()
    return JsonResponse(svc.daily_trend(days=days))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_list_stats_api(request):
    start, end = _parse_date_params(request)
    svc = AnalyticsService(start_date=start, end_date=end)
    return JsonResponse(svc.content_list_stats())
