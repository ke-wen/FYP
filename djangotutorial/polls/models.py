import datetime
from django.db import models
from django.contrib import admin
from django.utils import timezone




#Records of House sales
class House(models.Model): 
    date_of_sale = models.DateField(verbose_name="Date of Sale (dd/mm/yyyy)")
    address = models.CharField(max_length=255, verbose_name="Address")
    county = models.CharField(max_length=100, verbose_name="County")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Price (€)")
    description_of_property = models.CharField(max_length=255, verbose_name="Description of Property")

    def __str__(self):
        return f"{self.address}, {self.county} {self.description_of_property}- Sold on {self.date_of_sale.strftime('%d/%m/%Y')} for €{self.price}"

class AverageHousePrice(models.Model):
    eircode = models.CharField(max_length=20, verbose_name='Eircode Output')
    month = models.CharField(max_length=20, verbose_name='Month')
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='VALUE')

    def __str__(self):
        return f"{self.month} - {self.eircode} - {self.value}"
      

class HousesRent(models.Model):
    title = models.CharField(max_length=255, verbose_name='Property Title')
    price = models.PositiveIntegerField(verbose_name='Price')
    daft_link = models.URLField(max_length=500, verbose_name='Daft.ie Link')
    property_type = models.CharField(max_length=50, verbose_name='Property Type')
    location = models.CharField(max_length=100, verbose_name='Location')
    bedrooms = models.PositiveIntegerField(verbose_name='Number of Bedrooms',null=True, blank=True )
    bathrooms = models.PositiveIntegerField(verbose_name='Number of Bathrooms',null=True,blank=True )
    recorded_date = models.DateTimeField(verbose_name='Recorded Date',null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.location}"


class AverageRent(models.Model):
    eircode = models.CharField(max_length=20, verbose_name='Eircode')
    month = models.CharField(max_length=20, verbose_name='Month')
    average_rent = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Average Rent')

    def __str__(self):
        return f"{self.eircode} - {self.month} - €{self.average_rent}"

class Propertysale(models.Model):
    id = models.IntegerField(primary_key=True)  
    title = models.CharField(max_length=255, blank=True, null=True)  
    ecode = models.CharField(max_length=50, blank=True, null=True)  
    Property_Type = models.CharField(max_length=50, blank=True, null=True)  
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  
    publish_date = models.DateTimeField(blank=True, null=True)  
    bedrooms = models.PositiveIntegerField(blank=True, null=True)  
    bathrooms = models.PositiveIntegerField(blank=True, null=True)   
    propertySize = models.CharField(max_length=50, blank=True, null=True) 
    country = models.CharField(max_length=100, blank=True, null=True)  
    link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.Property_Type}"

class Propertyrent(models.Model):
    id = models.IntegerField(primary_key=True)  
    title = models.CharField(max_length=255, blank=True, null=True)  
    ecode = models.CharField(max_length=50, blank=True, null=True)  
    Property_Type = models.CharField(max_length=50, blank=True, null=True)  
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  
    publish_date = models.DateTimeField(blank=True, null=True)  
    bedrooms = models.PositiveIntegerField(blank=True, null=True)  
    bathrooms = models.PositiveIntegerField(blank=True, null=True)  
    link = models.URLField(max_length=500, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)  

    def __str__(self):
        return f"{self.title} - {self.Property_Type}"