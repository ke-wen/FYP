from itertools import chain
from django.db.models import F,Avg, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.http import Http404
from django.utils import timezone
from .models import House
from .models import AverageRent, AverageHousePrice ,Propertyrent, Propertysale


class IndexView(generic.View):
    template_name = "polls/index.html"

    def get(self, request):
        # Get filter criteria
        selected_county = request.GET.get('county', '')
        selected_bedrooms = request.GET.get('bedrooms', '')

        # Query distinct counties and bedroom options
        rent_counties = Propertyrent.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        sale_counties = Propertysale.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        rent_bedrooms = Propertyrent.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()
        sale_bedrooms = Propertysale.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()

        # Merge options and remove None values
        counties = sorted(set(filter(None, chain(rent_counties, sale_counties))))
        bedroom_options = sorted(set(filter(None, chain(rent_bedrooms, sale_bedrooms))))

        # Build filter query
        query = Q(is_active=True)
        if selected_county:
            query &= Q(county=selected_county)
        if selected_bedrooms:
            query &= Q(bedrooms=selected_bedrooms)

        # Calculate average rent and sale prices
        rent_avg_price = Propertyrent.objects.filter(query).aggregate(avg_price=Avg('price'))['avg_price']
        sale_avg_price = Propertysale.objects.filter(query).aggregate(avg_price=Avg('price'))['avg_price']

        # Format results to two decimal places with euro symbol, or set as "N/A"
        rent_avg_price = f"{rent_avg_price:.2f} €" if rent_avg_price is not None else "N/A"
        sale_avg_price = f"{sale_avg_price:.2f} €" if sale_avg_price is not None else "N/A"

        context = {
            'counties': counties,
            'bedroom_options': bedroom_options,
            'selected_county': selected_county,
            'selected_bedrooms': selected_bedrooms,
            'rent_avg_price': rent_avg_price,
            'sale_avg_price': sale_avg_price,
        }
        return render(request, self.template_name, context)



"""
Sql query for test:
SELECT AVG(price) AS avg_rent_price
FROM django_db.polls_propertysale
WHERE is_active = TRUE
  AND county = 'Dublin'
  AND bedrooms = 3;
"""


