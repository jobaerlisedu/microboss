from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Script, ScriptEditHistory


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ('script_date', 'headline_short', 'writer', 'source', 'status', 'approved_by', 'approved_at')
    list_filter = ('status', 'source', 'script_date')
    search_fields = ('headline', 'writer__username', 'district')
    ordering = ('-script_date',)

    def headline_short(self, obj):
        return obj.headline[:60] if obj.headline else ''
    headline_short.short_description = _('হেডলাইন')


@admin.register(ScriptEditHistory)
class ScriptEditHistoryAdmin(admin.ModelAdmin):
    list_display = ('script', 'headline_short', 'editor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('headline', 'editor__username', 'change_summary')
    ordering = ('-created_at',)

    def headline_short(self, obj):
        return obj.headline[:60] if obj.headline else ''
    headline_short.short_description = _('হেডলাইন')
