from django.utils import timezone


class AuditCreateMixin:
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


class AuditUpdateMixin:
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AuditMixin(AuditCreateMixin, AuditUpdateMixin):
    pass


class SoftDeleteMixin:
    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at', 'updated_at'])
