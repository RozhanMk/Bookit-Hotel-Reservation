from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'hotel', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'hotel']
    search_fields = ['customer__user__name', 'customer__user__last_name', 'customer__user__email', 'hotel__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer__user', 'hotel')