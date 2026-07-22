from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.content.models import ContentEntry
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.content.serializers import ContentEntrySerializer


class LeaderboardView(APIView):
    def get(self, request):
        limit = request.query_params.get('limit', 5)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 5

        top_users = User.objects.filter(
            is_active=True,
        ).annotate(
            entry_count=Count('content_entries', filter=Q(content_entries__deleted_at__isnull=True)),
        ).order_by('-entry_count')[:limit]

        data = []
        for rank, user in enumerate(top_users, 1):
            data.append({
                'rank': rank,
                'user': UserSerializer(user).data,
                'entry_count': user.entry_count,
            })
        return Response(data)


class UserEntriesDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        entries = ContentEntry.objects.filter(
            member=user, deleted_at__isnull=True,
        ).select_related('member', 'sponsor').order_by('-entry_date')[:100]

        return Response({
            'user': UserSerializer(user).data,
            'total_entries': entries.count(),
            'entries': ContentEntrySerializer(entries, many=True).data,
        })
