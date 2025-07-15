from django.contrib import admin
from bookit.settings import SERVER_URL, MEDIA_URL
from django.utils.html import format_html
from .models import Room, RoomLock, RoomType, DiscountStatus
from django.utils import timezone


@admin.action(description='Activate discount for selected rooms')
def activate_discounts(modeladmin, request, queryset):
    for room in queryset:
        room.hotel.discount_status = "Active"
        room.hotel.save()


@admin.action(description='Deactivate discount for selected rooms')
def deactivate_discounts(modeladmin, request, queryset):
    for room in queryset:
        room.hotel.discount_status = "Inactive"
        room.hotel.save()


@admin.action(description='Set as Single room')
def set_single_room(modeladmin, request, queryset):
    queryset.update(room_type=RoomType.SINGLE)


@admin.action(description='Set as Double room')
def set_double_room(modeladmin, request, queryset):
    queryset.update(room_type=RoomType.DOUBLE)


@admin.action(description='Set as Triple room')
def set_triple_room(modeladmin, request, queryset):
    queryset.update(room_type=RoomType.TRIPLE)


class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'room_number', 
        'name', 
        'hotel', 
        'room_type', 
        'price', 
        'discounted_price',
        'image_tag',
        'rate_display'
    ]
    list_filter = ['hotel', 'room_type']
    search_fields = ['room_number', 'name', 'hotel__name']
    actions = [
        activate_discounts,
        deactivate_discounts,
        set_single_room,
        set_double_room,
        set_triple_room
    ]

    def image_tag(self, obj):
        if obj.image:
            url = f'{SERVER_URL}{MEDIA_URL}{obj.image.name}'
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="80" height="85" /></a>',
                url,
                url
            )
        return "No image"
    
    def rate_display(self, obj):
        return f"{obj.rate}/5 ({obj.rate_number} reviews)"
    
    image_tag.short_description = 'Room Image'
    rate_display.short_description = 'Rating'


class RoomLockAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'locked_until', 'is_active']
    list_filter = ['room__hotel', 'user']
    search_fields = ['room__room_number', 'user__email']
    
    def is_active(self, obj):
        return obj.locked_until > timezone.now()
    
    is_active.boolean = True
    is_active.short_description = 'Active Lock'


admin.site.register(Room, RoomAdmin)
admin.site.register(RoomLock, RoomLockAdmin)
