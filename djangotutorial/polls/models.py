import datetime
from django.db import models
from django.contrib import admin
from django.utils import timezone



class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    def __str__(self):
        return self.question_text    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

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
    month = models.CharField(max_length=20, verbose_name='Month')
    dwelling_status = models.CharField(max_length=100, verbose_name='Dwelling Status')
    eircode = models.CharField(max_length=20, verbose_name='Eircode Output')
    stamp_duty_event = models.CharField(max_length=100, verbose_name='Stamp Duty Event')
    type_of_buyer = models.CharField(max_length=100, verbose_name='Type of Buyer')
    unit = models.CharField(max_length=10, default='Euro', verbose_name='UNIT')
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='VALUE')

    def __str__(self):
        return f"{self.month} - {self.eircode} - {self.value}"
      

class HousesRent(models.Model):
    title = models.CharField(max_length=255, verbose_name='Property Title')
    price = models.CharField(max_length=50, verbose_name='Price')
    daft_link = models.URLField(max_length=500, verbose_name='Daft.ie Link')
    property_type = models.CharField(max_length=50, verbose_name='Property Type')
    location = models.CharField(max_length=100, verbose_name='Location')
    facilities = models.JSONField(blank=True, null=True, verbose_name='Facilities')  
    bedrooms = models.PositiveIntegerField(verbose_name='Number of Bedrooms')
    bathrooms = models.PositiveIntegerField(verbose_name='Number of Bathrooms')

    def __str__(self):
        return f"{self.title} - {self.location}"


class AverageRent(models.Model):
    eircode = models.CharField(max_length=20, verbose_name='Eircode')
    month = models.CharField(max_length=20, verbose_name='Month')
    average_rent = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Average Rent')

    def __str__(self):
        return f"{self.eircode} - {self.month} - €{self.average_rent}"