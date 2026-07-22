from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('assign_date', 'caption_short', 'reporter', 'reporter_user', 'status', 'district', 'member')
    list_filter = ('status', 'assign_date', 'deleted_at')
    search_fields = ('caption', 'reporter', 'district', 'member__username', 'reporter_user__full_name')
    ordering = ('-assign_date',)
    list_per_page = 50
    date_hierarchy = 'assign_date'
    autocomplete_fields = ('member', 'reporter_user')
    actions = ['soft_delete_selected']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'reporter_user', 'created_by', 'updated_by',
        )

    def caption_short(self, obj):
        return obj.caption[:60] if obj.caption else ''
    caption_short.short_description = _('ক্যাপশন')

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and request.method == 'POST':
            obj.soft_delete(user=request.user)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('../')
        return super().delete_view(request, object_id, extra_context)

    @admin.action(description=_('Soft delete selected assignments'))
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)
        self.message_user(request, _('Selected assignments soft-deleted successfully.'))
