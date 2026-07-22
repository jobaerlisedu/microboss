import io
import logging
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponse

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except OSError as e:
    logger.warning(f'WeasyPrint not available: {e}. Using fallback HTML render.')
    WEASYPRINT_AVAILABLE = False


def generate_content_report(entries, title='Content Report'):
    html = render_to_string('reports/content_report.html', {
        'title': title,
        'entries': entries,
        'generated_at': timezone.now(),
        'total': len(entries),
    })
    if WEASYPRINT_AVAILABLE:
        pdf_file = io.BytesIO()
        HTML(string=html).write_pdf(pdf_file)
        pdf_file.seek(0)
        return pdf_file
    else:
        return _html_fallback(html, 'content_report.html')


def generate_script_pdf(script):
    html = render_to_string('reports/script_pdf.html', {
        'script': script,
    })
    if WEASYPRINT_AVAILABLE:
        pdf_file = io.BytesIO()
        HTML(string=html).write_pdf(pdf_file)
        pdf_file.seek(0)
        return pdf_file
    else:
        return _html_fallback(html, f'{script.filename}.html')


def _html_fallback(html_string, filename):
    """Return HTML file when WeasyPrint is unavailable"""
    response = HttpResponse(html_string, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
