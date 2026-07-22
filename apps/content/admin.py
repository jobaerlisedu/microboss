from django.contrib import admin
from .models import ContentEntry


@admin.register(ContentEntry)
class ContentEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_date', 'entry_time', 'member', 'headline_short', 'sponsor', 'slug')
    list_filter = ('entry_date', 'sponsor', 'member')
    search_fields = ('headline', 'slug', 'member__username')
    ordering = ('-entry_date', '-entry_time')
    date_hierarchy = 'entry_date'

    def headline_short(self, obj):
        return obj.headline[:60] if obj.headline else ''
    headline_short.short_description = 'The Headline'
