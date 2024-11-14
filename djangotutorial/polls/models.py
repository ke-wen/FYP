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
      

