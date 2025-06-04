from django.contrib import admin

from hotelManager.models import HotelManager


@admin.action(description='Verify selected hotel managers')
def verify_hotel_managers(modeladmin, request, queryset):

    for hotel_manager in queryset:
        hotel_manager.status = 'Accepted'
        hotel_manager.save()




class HotelManagerAdmin(admin.ModelAdmin):

    actions = [verify_hotel_managers]

    list_display = ['get_name', 'get_last_name', 'national_code', 'status']


    def get_name(self, obj):
        return obj.user.name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_phone_number(self, obj):
        return obj.user.phone_number

    get_name.admin_order_field = 'user__first_name'
    get_name.short_description = 'First Name'

    get_last_name.admin_order_field = 'user__last_name'
    get_last_name.short_description = 'Last Name'



admin.site.register(HotelManager, HotelManagerAdmin)