from django.contrib import admin
from .models import FinalPackage


@admin.register(FinalPackage)
class FinalPackageAdmin(admin.ModelAdmin):
    list_display = ('package_date', 'title_short', 'producer', 'status', 'assignment', 'member')
    list_filter = ('status', 'package_date', 'deleted_at')
    search_fields = ('title', 'producer', 'member__username', 'editor')
    ordering = ('-package_date',)
    list_per_page = 50
    date_hierarchy = 'package_date'
    autocomplete_fields = ('member', 'editor_user')
    actions = ['soft_delete_selected']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member', 'editor_user', 'assignment')

    def title_short(self, obj):
        return obj.title[:60] if obj.title else ''
    title_short.short_description = 'Title'

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

    @admin.action(description='Soft delete selected packages')
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete(user=request.user)
        self.message_user(request, 'Selected packages soft-deleted successfully.')
