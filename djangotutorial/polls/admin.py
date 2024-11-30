from django.contrib import admin
from import_export import resources
from .models import House, AverageHousePrice, HousesRent ,AverageRent , Propertysale ,Propertyrent
from import_export.admin import ImportExportModelAdmin


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
    list_display = ['eircode', 'month', 'value']
    list_filter = ['eircode', 'month']
    search_fields = ['eircode', 'month']

class HousesRentResource(resources.ModelResource):
    class Meta:
        model = HousesRent

class HousesRentAdmin(ImportExportModelAdmin):
    resource_class = HousesRentResource
    list_display = ['title', 'price', 'property_type', 'location', 'bedrooms', 'bathrooms','recorded_date']
    list_filter = ['property_type', 'location', 'bedrooms']
    search_fields = ['title', 'location', 'property_type']

class AverageRentResource(resources.ModelResource):
    class Meta:
        model = AverageRent 
class AverageRentAdmin(ImportExportModelAdmin):
    resource_class = AverageRentResource
    list_display = ['eircode', 'month', 'average_rent']
    list_filter = ['eircode', 'month']
    search_fields = ['eircode', 'month']

class PropertysaleResource(resources.ModelResource):
    class Meta:
        model = Propertysale
class PropertysaleAdmin(ImportExportModelAdmin):
    resource_class = PropertysaleResource
    list_display = ('id', 'title', 'Property_Type', 'price', 'publish_date', 'country')  
    search_fields = ('title', 'Property_Type', 'country')  
    list_filter = ('Property_Type', 'country')  

class PropertyrentResource(resources.ModelResource):
    class Meta:
        model = Propertyrent
class PropertyrentAdmin(ImportExportModelAdmin):
    resource_class = PropertyrentResource
    list_display = ('id', 'title', 'Property_Type', 'price', 'publish_date', 'country')  
    search_fields = ('title', 'Property_Type', 'country')  
    list_filter = ('Property_Type', 'country')  
    
admin.site.register(Propertysale, PropertysaleAdmin)
admin.site.register(Propertyrent, PropertyrentAdmin)
admin.site.register(AverageRent, AverageRentAdmin)
admin.site.register(HousesRent, HousesRentAdmin)    
admin.site.register(House, HouseAdmin)
admin.site.register(AverageHousePrice, AverageHousePriceAdmin)
