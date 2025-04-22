from itertools import chain
from django.db.models import F,Avg, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic, View
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.http import Http404
from django.utils import timezone
import matplotlib
matplotlib.use('Agg')
from .models import House
from .models import AverageRent, AverageHousePrice ,Propertyrent, Propertysale
import numpy_financial as npf
from django.views.generic import TemplateView
from collections import defaultdict
import matplotlib.pyplot as plt
from django.shortcuts import redirect
from django.contrib import messages
from .models import Bookmark
import seaborn as sns
import urllib, base64
import pandas as pd
import io
import os



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
        selected_county = request.GET.get('county', '')
        selected_bedrooms = request.GET.get('bedrooms', '')

        rent_counties = Propertyrent.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        sale_counties = Propertysale.objects.filter(is_active=True).values_list('county', flat=True).distinct()
        rent_bedrooms = Propertyrent.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()
        sale_bedrooms = Propertysale.objects.filter(is_active=True).values_list('bedrooms', flat=True).distinct()

        counties = sorted(set(filter(None, chain(rent_counties, sale_counties))))
        bedroom_options = sorted(set(filter(None, chain(rent_bedrooms, sale_bedrooms))))
        counties.insert(0, "All")
        bedroom_options.insert(0, "All")

        if not selected_county and not selected_bedrooms:
            return render(request, self.template_name, {
                'counties': counties,
                'bedroom_options': bedroom_options,
                'selected_county': selected_county,
                'selected_bedrooms': selected_bedrooms,
                'rent_avg_price': "N/A",
                'sale_avg_price': "N/A",
                'rental_yield': "N/A",
                'all_risk_yield': "N/A",
                'all_properties': []
            })

        query = Q(is_active=True)
        if selected_county and selected_county != "All":
            query &= Q(county=selected_county)
        if selected_bedrooms and selected_bedrooms != "All":
            try:
                query &= Q(bedrooms=int(selected_bedrooms))
            except ValueError:
                pass

        rent_avg_price = Propertyrent.objects.filter(query).aggregate(avg_price=Avg('price'))['avg_price']
        sale_avg_price = Propertysale.objects.filter(query).aggregate(avg_price=Avg('price'))['avg_price']
        rent_avg_price = float(rent_avg_price) if rent_avg_price is not None else "N/A"
        sale_avg_price = float(sale_avg_price) if sale_avg_price is not None else "N/A"

        if rent_avg_price != "N/A" and sale_avg_price != "N/A":
            rent_avg_price_num = rent_avg_price
            sale_avg_price_num = sale_avg_price
            rental_yield = f"{(rent_avg_price_num * 12 / sale_avg_price_num) * 100:.2f} %"

            # All Risk Yield example calculation
            all_risk_yield_value = calculate_all_risk_yield(
                initial_investment=sale_avg_price_num,
                monthly_rent=rent_avg_price_num,
                maintenance_percentage=0.34,
                sale_price_growth_rate=0.052,
                holding_period=5,
                income_growth_rate=0.02,
                rental_review_period=1
            )
            all_risk_yield = f"{all_risk_yield_value:.2f} %"
        else:
            rental_yield = "N/A"
            all_risk_yield = "N/A"


        # Identify which properties this user has already bookmarked
        user_identifier = request.session.get('user_id')
        if user_identifier:
            # Return (property_id, bookmark_id) for each bookmarked property
            user_bookmarks = Bookmark.objects.filter(user=user_identifier).values_list('property_id', 'id')
            bookmark_id_by_property_id = {prop_id: bm_id for prop_id, bm_id in user_bookmarks}
        else:
            bookmark_id_by_property_id = {}

        # Build up the property list, noting whether each property is bookmarked
        filtered_sale_properties = Propertysale.objects.filter(query).values(
            'id', 'title', 'bedrooms', 'bathrooms', 'price','rental_yield','all_risk_yield','link'
        )

        property_list = []
        for prop in filtered_sale_properties:
            property_price = prop['price']
            db_rental_yield = prop['rental_yield']      
            db_all_risk_yield = prop['all_risk_yield']  
            if db_rental_yield is not None:
                prop_rental_yield = f"{db_rental_yield:.2f} %"
            else:
                prop_rental_yield = "N/A"

            if db_all_risk_yield is not None:
                prop_all_risk_yield = f"{db_all_risk_yield:.2f} %"
            else:
                prop_all_risk_yield = "N/A"

            property_list.append({
                **prop,
                'rental_yield': prop_rental_yield,
                'all_risk_yield': prop_all_risk_yield,
                # Check if current property is bookmarked
                'bookmark_id': bookmark_id_by_property_id.get(prop['id'])
            })

        # Sort by Rental Yield
        def rental_yield_float(ry):
            return float(ry.replace(' %', '')) if ry != "N/A" else -1

        property_list.sort(key=lambda x: rental_yield_float(x['rental_yield']), reverse=True)

        context = {
            'counties': counties,
            'bedroom_options': bedroom_options,
            'selected_county': selected_county,
            'selected_bedrooms': selected_bedrooms,
            'rent_avg_price': rent_avg_price,
            'sale_avg_price': sale_avg_price,
            'rental_yield': rental_yield,
            'all_risk_yield': all_risk_yield,
            'all_properties': property_list,
        }
        return render(request, self.template_name, context)



class InformationView(TemplateView):
    template_name = "polls/information.html"




class BoxPlotView(View):
    template_name = "polls/boxplot.html"

    def get(self, request):
        selected_county = request.GET.get('county', '')
        if not selected_county:
            return render(request, self.template_name, {'error': "No county selected"})

        query = Q(is_active=True) & Q(county=selected_county) & Q(bedrooms__isnull=False)
        sale_properties = Propertysale.objects.filter(query).values('bedrooms', 'price')
        rent_properties = Propertyrent.objects.filter(query).values('bedrooms', 'price')

        rental_yield_data = defaultdict(list)
        all_risk_yield_data = defaultdict(list)

        # Collect average rent by bedrooms
        rent_prices_by_bedrooms = defaultdict(list)
        for rent in rent_properties:
            if rent['price'] is not None:
                rent_prices_by_bedrooms[rent['bedrooms']].append(float(rent['price']))

        avg_rent_by_bedrooms = {
            k: sum(v) / len(v) for k, v in rent_prices_by_bedrooms.items() if v
        }

        # Calculate yields
        for sale in sale_properties:
            bedrooms = sale['bedrooms']
            sale_price = float(sale['price']) if sale['price'] else None

            if sale_price and bedrooms in avg_rent_by_bedrooms:
                avg_rent = avg_rent_by_bedrooms[bedrooms]

                # Rental Yield
                ry = (avg_rent * 12 / sale_price) * 100
                # Filter outliers
                if ry < 50:
                    rental_yield_data[bedrooms].append(ry)

                # All Risk Yield
                maintenance_percentage = 0.34
                sale_price_growth_rate = 0.052
                holding_period = 5
                income_growth_rate = 0.02
                rental_review_period = 1

                ary = calculate_all_risk_yield(
                    sale_price,
                    avg_rent,
                    maintenance_percentage,
                    sale_price_growth_rate,
                    holding_period,
                    income_growth_rate,
                    rental_review_period
                )
                # Filter outliers
                if ary < 40:
                    all_risk_yield_data[bedrooms].append(ary)

        if not rental_yield_data:
            return render(request, self.template_name, {
                'error': "No valid Rental Yield data available for this county"
            })

        sorted_bedrooms = sorted(rental_yield_data.keys())

        # Rental Yield Box Plot
        buffer_rental = io.BytesIO()
        plt.figure(figsize=(8, 6))
        rental_data = pd.DataFrame({
            str(k): pd.Series(rental_yield_data[k]) for k in sorted_bedrooms
        })
        sns.boxplot(data=rental_data, order=[str(k) for k in sorted_bedrooms])
        ax_rental = plt.gca()

        ylim = ax_rental.get_ylim()
        offset = 0.05 * (ylim[1] - ylim[0])  

        for i, b in enumerate(sorted_bedrooms):
            n = len(rental_yield_data[b])
            ax_rental.text(
                x=i,
                y=ylim[1] - offset,
                s=f"Number on sale: {n}",
                ha='center',
                va='top',
                fontsize=9
            )

        plt.xlabel("Number of Bedrooms")
        plt.ylabel("Rental Yield (%)")
        plt.title(f"Rental Yield Box Plot for {selected_county}")
        plt.savefig(buffer_rental, format="png", bbox_inches='tight')
        buffer_rental.seek(0)
        graphic_rental = base64.b64encode(buffer_rental.getvalue()).decode()
        buffer_rental.close()
        plt.close()

        # All Risk Yield Box Plot
        buffer_all_risk = io.BytesIO()
        if all_risk_yield_data:
            plt.figure(figsize=(8, 6))
            all_risk_data = pd.DataFrame({
                str(k): pd.Series(all_risk_yield_data[k]) for k in sorted_bedrooms
            })
            sns.boxplot(data=all_risk_data, order=[str(k) for k in sorted_bedrooms])
            ax_ary = plt.gca()

            ylim_ary = ax_ary.get_ylim()
            offset_ary = 0.05 * (ylim_ary[1] - ylim_ary[0])

            for i, b in enumerate(sorted_bedrooms):
                n_ary = len(all_risk_yield_data[b])
                ax_ary.text(
                    x=i,
                    y=ylim_ary[1] - offset_ary,
                    s=f"Number on sale: {n_ary}",
                    ha='center',
                    va='top',
                    fontsize=9
                )

            plt.xlabel("Number of Bedrooms")
            plt.ylabel("All Risk Yield (%)")
            plt.title(f"All Risk Yield Box Plot for {selected_county}")
            plt.savefig(buffer_all_risk, format="png", bbox_inches='tight')
            buffer_all_risk.seek(0)
            graphic_all_risk = base64.b64encode(buffer_all_risk.getvalue()).decode()
            buffer_all_risk.close()
            plt.close()
        else:
            graphic_all_risk = None

        return render(request, self.template_name, {
            'graphic_rental': graphic_rental,
            'graphic_all_risk': graphic_all_risk,
            'selected_county': selected_county
        })
# django ploty



def bookmark_property(request):
    if request.method == 'POST':
        property_id = request.POST.get('property_id')
        user_identifier = request.session.get('user_id', None)
        
        # Create a user identifier if none exists
        if not user_identifier:
            import uuid
            user_identifier = str(uuid.uuid4())
            request.session['user_id'] = user_identifier
        
        # Check if already bookmarked
        existing = Bookmark.objects.filter(property_id=property_id, user=user_identifier).exists()
        
        if not existing:
            property_obj = get_object_or_404(Propertysale, id=property_id)
            Bookmark.objects.create(property=property_obj, user=user_identifier)
            
        return redirect(request.META.get('HTTP_REFERER', 'polls:property_calculator'))

def view_bookmarks(request):
    user_identifier = request.session.get('user_id', None)
    
    if not user_identifier:
        bookmarks = []
    else:
        bookmarks = Bookmark.objects.filter(user=user_identifier).select_related('property')
        
    return render(request, 'polls/bookmarks.html', {'bookmarks': bookmarks})

def remove_bookmark(request, bookmark_id):
    user_identifier = request.session.get('user_id', None)
    
    if user_identifier:
        bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=user_identifier)
        bookmark.delete()
    next_url = request.META.get('HTTP_REFERER', 'polls:property_calculator')
    return redirect(next_url)





class DashboardView(View):
    template_name = "polls/dashboard.html"

    def get(self, request):
        charts = {
            'chart_boxplot': 'dashboard_charts/chart_boxplot.png',
            'chart_heatmap': 'dashboard_charts/chart_heatmap.png',
            'chart_feature_importance': 'dashboard_charts/chart_feature_importance.png',
            'chart_scatter': 'dashboard_charts/chart_scatter.png',
            'chart_price_hist': 'dashboard_charts/chart_price_hist.png',
            'chart_timeseries': 'dashboard_charts/chart_timeseries.png',
        }
        return render(request, self.template_name, charts)






"""
Sql query for test:
SELECT AVG(price) AS avg_rent_price
FROM django_db.polls_propertysale
WHERE is_active = TRUE
  AND county = 'Dublin'
  AND bedrooms = 3;
"""