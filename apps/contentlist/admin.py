from django.contrib import admin
from .models import ContentListItem


@admin.register(ContentListItem)
class ContentListItemAdmin(admin.ModelAdmin):
    list_display = ('list_date', 'content_short', 'source', 'district', 'footage_source', 'member')
    list_filter = ('source', 'footage_source', 'list_date')
    search_fields = ('content', 'district', 'member__username')
    ordering = ('-list_date',)

    def content_short(self, obj):
        return obj.content[:60] if obj.content else ''
    content_short.short_description = 'Content'
