from itertools import chain
from django.db.models import F,Avg, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic, View
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.http import Http404
from django.utils import timezone
from .models import House
from .models import AverageRent, AverageHousePrice ,Propertyrent, Propertysale
from django.views.generic import TemplateView
# pip install numpy-financial
import numpy_financial as npf

def calculate_all_risk_yield(initial_investment, monthly_rent, maintenance_percentage, sale_price_growth_rate, holding_period, income_growth_rate, rental_review_period=1):
    net_annual_income = monthly_rent * 12
    cash_flows = [-initial_investment]
    final_sale_price = initial_investment * (1 + sale_price_growth_rate) ** holding_period
    for year in range(holding_period):
        growth_cycles = year // rental_review_period
        adjusted_income = net_annual_income * (1 + income_growth_rate) ** growth_cycles
        maintenance_cost = adjusted_income * maintenance_percentage
        net_cash_flow = adjusted_income - maintenance_cost
        cash_flows.append(net_cash_flow)
    cash_flows[-1] += final_sale_price
    equated_yield = npf.irr(cash_flows) * 100
    e = equated_yield / 100
    g = income_growth_rate
    t = rental_review_period
    k0 = e - e * (((1 + g) ** t - 1) / ((1 + e) ** t - 1))
    return k0 * 100

class HomeView(TemplateView):
    template_name = "polls/home.html" 

class IndexView(View):
    template_name = "polls/index.html"

    def get(self, request):
        # Get filter options
        selected_county = request.GET.get('county', '')
        selected_bedrooms = request.GET.get('bedrooms', '')

        # Query all county and bedroom options.
        rent_counties = Propertyrent.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        sale_counties = Propertysale.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        rent_bedrooms = Propertyrent.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()
        sale_bedrooms = Propertysale.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()

        # merge options and remove N/A values
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

        # Format results to two decimal, if no value set as "N/A"
        rent_avg_price = f"{rent_avg_price:.2f} €" if rent_avg_price is not None else "N/A"
        sale_avg_price = f"{sale_avg_price:.2f} €" if sale_avg_price is not None else "N/A"

        # Calculate Rental Yield and All Risk Yield
        if rent_avg_price != "N/A" and sale_avg_price != "N/A":
            rent_avg_price_num = float(rent_avg_price[:-2])  # Remove € and convert to float
            sale_avg_price_num = float(sale_avg_price[:-2])
            rental_yield = f"{(rent_avg_price_num * 12 / sale_avg_price_num) * 100:.2f} %"# Calculate Rental Yield
            # Calculate All Risk Yield
            initial_investment = sale_avg_price_num
            monthly_rent = rent_avg_price_num 
            maintenance_percentage = 0.34
            sale_price_growth_rate = 0.052
            holding_period = 5
            income_growth_rate = 0.02
            rental_review_period = 1

            all_risk_yield = calculate_all_risk_yield(
                initial_investment, monthly_rent, maintenance_percentage, sale_price_growth_rate,
                holding_period, income_growth_rate, rental_review_period
            )
            all_risk_yield = f"{all_risk_yield:.2f} %"
        else:
            rental_yield = "N/A"
            all_risk_yield = "N/A"
        

        context = {
            'counties': counties,
            'bedroom_options': bedroom_options,
            'selected_county': selected_county,
            'selected_bedrooms': selected_bedrooms,
            'rent_avg_price': rent_avg_price,
            'sale_avg_price': sale_avg_price,
            'rental_yield': rental_yield,
            'all_risk_yield': all_risk_yield,
        }
        return render(request, self.template_name, context)


class InformationView(TemplateView):
    template_name = "polls/information.html"

"""
Sql query for test:
SELECT AVG(price) AS avg_rent_price
FROM django_db.polls_propertysale
WHERE is_active = TRUE
  AND county = 'Dublin'
  AND bedrooms = 3;
"""


