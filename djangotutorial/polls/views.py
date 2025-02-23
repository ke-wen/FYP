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
import numpy_financial as npf
from django.views.generic import TemplateView
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import urllib, base64
import pandas as pd
import io

from .models import Propertysale, Propertyrent  # 确保正确导入模型

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

        # Merge options and remove N/A values
        counties = sorted(set(filter(None, chain(rent_counties, sale_counties))))
        bedroom_options = sorted(set(filter(None, chain(rent_bedrooms, sale_bedrooms))))

        # Insert the "All" option
        counties.insert(0, "All") 
        bedroom_options.insert(0, "All")
        
        # Do not show properties by default
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

        # Build filter query
        query = Q(is_active=True)
        if selected_county and selected_county != "All":
            query &= Q(county=selected_county)

        if selected_bedrooms and selected_bedrooms != "All":
            try:
                query &= Q(bedrooms=int(selected_bedrooms))  
            except ValueError:
                pass  

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

        # Fetch matching selling properties for the table
        filtered_sale_properties = Propertysale.objects.filter(query).values('title', 'bedrooms', 'bathrooms', 'price', 'link')

        property_list = []
        for property in filtered_sale_properties:
            property_price = property['price']
            prop_rental_yield = "N/A"
            prop_all_risk_yield = "N/A"

            if property_price is None and rent_avg_price == "N/A":
                property_price = "N/A"

            elif property_price is not None and rent_avg_price == "N/A":
                property_price = float(property_price)

            elif property_price is not None and rent_avg_price != "N/A":
                property_price = float(property_price)
                rent_avg_price_num = float(rent_avg_price[:-2]) 
                
                # Calculate rental yield for this property
                prop_rental_yield = f"{(rent_avg_price_num * 12 / property_price) * 100:.2f} %"

                # Calculate All Risk Yield for this property
                prop_all_risk_yield = calculate_all_risk_yield(
                    property_price, rent_avg_price_num, maintenance_percentage, sale_price_growth_rate,
                    holding_period, income_growth_rate, rental_review_period
                )
                prop_all_risk_yield = f"{prop_all_risk_yield:.2f} %"

            # Append property with yield
            property_list.append({
                **property,
                'rental_yield': prop_rental_yield,
                'all_risk_yield': prop_all_risk_yield
            })
        # Sort by Rental Yield from high to low, N/A at the end
        property_list.sort(key=lambda x: (float(x['rental_yield'].replace(' %', '')) if x['rental_yield'] != "N/A" else -1), reverse=True)
        # Update context with the processed properties
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

        # 获取该县的房产数据，并排除 bedrooms=None 的数据
        query = Q(is_active=True) & Q(county=selected_county) & Q(bedrooms__isnull=False)
        sale_properties = Propertysale.objects.filter(query).values('bedrooms', 'price')
        rent_properties = Propertyrent.objects.filter(query).values('bedrooms', 'price')

        # 计算 Rental Yield
        rental_yield_data = defaultdict(list)

        # 预计算不同房间数的平均租金
        rent_prices_by_bedrooms = defaultdict(list)
        for rent in rent_properties:
            if rent['price'] is not None:  # 确保租金不为空
                rent_prices_by_bedrooms[rent['bedrooms']].append(rent['price'])

        avg_rent_by_bedrooms = {
            k: sum(v) / len(v) for k, v in rent_prices_by_bedrooms.items() if v
        }

        for sale in sale_properties:
            bedrooms = sale['bedrooms']
            sale_price = sale['price']

            if sale_price and bedrooms in avg_rent_by_bedrooms:
                avg_rent = avg_rent_by_bedrooms[bedrooms]
                rental_yield = (avg_rent * 12 / sale_price) * 100
                rental_yield_data[bedrooms].append(rental_yield)

        if not rental_yield_data:
            return render(request, self.template_name, {'error': "No valid Rental Yield data available for this county"})

        # **按照 bedrooms 从小到大排序**
        sorted_bedrooms = sorted(rental_yield_data.keys())
        data = pd.DataFrame({str(k): pd.Series(rental_yield_data[k]) for k in sorted_bedrooms})

        # **创建 Box Plot**
        plt.figure(figsize=(8, 6))
        sns.boxplot(data=data, order=[str(k) for k in sorted_bedrooms])  # 确保 X 轴排序正确

        y_max = max([max(v) for v in rental_yield_data.values()]) if rental_yield_data else 40
        plt.ylim(0, min(40, y_max + 5))  

        plt.xlabel("Number of Bedrooms")
        plt.ylabel("Rental Yield (%)")

        plt.title(f"Rental Yield Box Plot for {selected_county}")

        # **保存图像并转成 Base64**
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()  # 释放 Matplotlib 资源，防止内存泄漏

        graphic = base64.b64encode(image_png).decode()

        return render(request, self.template_name, {'graphic': graphic, 'selected_county': selected_county})

"""
Sql query for test:
SELECT AVG(price) AS avg_rent_price
FROM django_db.polls_propertysale
WHERE is_active = TRUE
  AND county = 'Dublin'
  AND bedrooms = 3;
"""


