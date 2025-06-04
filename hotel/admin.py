from django.contrib import admin
from bookit.settings import SERVER_URL, MEDIA_URL
from django.utils.html import format_html

from hotel.models import Hotel


@admin.action(description='Verify selected hotels')
def verify_hotels(modeladmin, request, queryset):

    for hotel in queryset:
        hotel.status = 'Accepted'
        hotel.save()


@admin.action(description='Verify selected hotels discount')
def verify_discounts(modeladmin, request, queryset):

    for hotel in queryset:
        hotel.discount_status = "Active"
        hotel.save()


@admin.action(description='inactive selected hotels discount')
def inactive_discounts(modeladmin, request, queryset):

    for hotel in queryset:
        hotel.discount_status = "Inactive"
        hotel.save()




class HotelAdmin(admin.ModelAdmin):

    actions = [verify_hotels]

    list_display = ['name', 'description', 'location', 'status', 'image_tag', 'hotel_license_tag']

    def image_tag(self, obj):
        if obj.image:
            url = f'{SERVER_URL}{MEDIA_URL}{obj.image.name}'
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="80" height="85" /></a>',
                url,
                url
            )
        return "No image"

    def hotel_license_tag(self, obj):
        if obj.hotel_license:
            url = f'{SERVER_URL}{MEDIA_URL}{obj.hotel_license.name}'
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="80" height="85" /></a>',
                url,
                url
            )
        return "No hotel_license"


admin.site.register(Hotel, HotelAdmin)