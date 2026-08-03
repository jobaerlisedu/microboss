from django.http import FileResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.content.models import ContentEntry
from .pdf_utils import generate_content_report, WEASYPRINT_AVAILABLE


class ContentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entries = ContentEntry.objects.filter(
            deleted_at__isnull=True,
        ).select_related('member', 'sponsor').order_by('-entry_date')

        month = request.query_params.get('month')
        if month:
            entries = entries.filter(entry_date__startswith=month)

        title = 'Content Report'
        if month:
            title += f' - {month}'

        result = generate_content_report(entries, title=title)
        if isinstance(result, FileResponse) or isinstance(result, HttpResponse):
            return result
        return FileResponse(result, as_attachment=True, filename='content_report.pdf')
