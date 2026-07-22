from django.contrib import admin
from django.urls import path, include, register_converter
from django.conf import settings
from config.converters import HexUUIDConverter

register_converter(HexUUIDConverter, 'hexuuid')
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import AllowAny
import apps.common.views

urlpatterns = [
    path('api/v1/schema/', get_schema_view(
        title='Phoenix CMS API',
        description='Enterprise content management API for Channel One',
        version='1.0.0',
        urlconf='config.urls',
        renderer_classes=[JSONRenderer],
        permission_classes=[AllowAny],
        authentication_classes=[],
    ), name='openapi-schema'),
    path('', apps.common.views.root_redirect),
    path('cms/', include('apps.cms.urls')),
    path('cms-admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/entries/', include('apps.content.urls')),
    path('api/v1/sponsors/', include('apps.sponsors.urls')),
    path('api/v1/content-lists/', include('apps.contentlist.urls')),
    path('api/v1/assignments/', include('apps.assignments.urls')),
    path('api/v1/scripts/', include('apps.scripts.urls')),
    path('api/v1/leaders/', include('apps.leaders.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/notices/', include('apps.notices.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/hr/', include('apps.hr.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
