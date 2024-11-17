from django.contrib import admin
from import_export import resources
from .models import Choice, Question, House, AverageHousePrice, HousesRent ,AverageRent
from import_export.admin import ImportExportModelAdmin


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]

class HouseResource(resources.ModelResource):
    class Meta:
        model = House

class HouseAdmin(ImportExportModelAdmin):
    resource_class = HouseResource
    list_display = ('address', 'county', 'price', 'date_of_sale', 'description_of_property')
    list_filter = ('county', 'date_of_sale')
    search_fields = ('address', 'description_of_property')

class AverageHousePriceResource(resources.ModelResource):
    class Meta:
        model = AverageHousePrice

class AverageHousePriceAdmin(ImportExportModelAdmin):
    resource_class = AverageHousePriceResource
    list_display = ['month', 'dwelling_status', 'eircode', 'stamp_duty_event', 'type_of_buyer', 'unit', 'value']
    list_filter = ['month', 'eircode', 'type_of_buyer']
    search_fields = ['eircode', 'dwelling_status']

class HousesRentResource(resources.ModelResource):
    class Meta:
        model = HousesRent

class HousesRentAdmin(ImportExportModelAdmin):
    resource_class = HousesRentResource
    list_display = ['title', 'price', 'property_type', 'location', 'bedrooms', 'bathrooms']
    list_filter = ['property_type', 'location', 'bedrooms']
    search_fields = ['title', 'location', 'property_type']

class AverageRentResource(resources.ModelResource):
    class Meta:
        model = AverageRent
class AverageRentAdmin(ImportExportModelAdmin):
    list_display = ['eircode', 'month', 'average_rent']
    list_filter = ['eircode', 'month']
    search_fields = ['eircode', 'month']

admin.site.register(AverageRent, AverageRentAdmin)
admin.site.register(HousesRent, HousesRentAdmin)    
admin.site.register(House, HouseAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AverageHousePrice, AverageHousePriceAdmin)