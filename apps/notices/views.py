from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Notice
from .serializers import NoticeSerializer


class NoticeListAPIView(generics.ListAPIView):
    queryset = Notice.objects.filter(deleted_at__isnull=True, is_active=True)
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]


class NoticeDetailAPIView(generics.RetrieveAPIView):
    queryset = Notice.objects.filter(deleted_at__isnull=True, is_active=True)
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]
