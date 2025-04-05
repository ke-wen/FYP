# polls/management/commands/update_yields.py
from django.core.management.base import BaseCommand
from django.db.models import Avg
from polls.models import Propertysale, Propertyrent
import numpy_financial as npf
from decimal import Decimal

class Command(BaseCommand):
    help = "Update Rental Yield & All Risk Yield for Propertysale"

    def calculate_all_risk_yield(self, initial_investment, monthly_rent):

        maintenance_percentage = 0.34
        sale_price_growth_rate = 0.052
        holding_period = 5
        income_growth_rate = 0.02
        rental_review_period = 1

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

        irr_float = npf.irr(cash_flows)  
        e = irr_float
        g = income_growth_rate
        t = rental_review_period
        k0 = e - e * (((1 + g) ** t - 1) / ((1 + e) ** t - 1))
        return k0 * 100  

    def handle(self, *args, **options):
        #get the average rent float corresponding to (county, bedrooms)
        rent_info = (
            Propertyrent.objects
            .filter(is_active=True)
            .values('county', 'bedrooms')
            .annotate(avg_rent=Avg('price'))
        )
        rent_map = {}
        for r in rent_info:
            c = r['county']
            b = r['bedrooms']
            if c and b and r['avg_rent'] is not None:
                rent_map[(c, b)] = float(r['avg_rent']) 

        # Traverse Property Sale
        updated_count = 0
        sales = Propertysale.objects.filter(is_active=True)
        for prop in sales:
            if prop.price is None or prop.county is None or prop.bedrooms is None:
                continue
            if (prop.county, prop.bedrooms) not in rent_map:
                continue

            price_float = float(prop.price)  
            rent_float = rent_map[(prop.county, prop.bedrooms)]
            if price_float <= 0 or rent_float <= 0:
                continue

            rental_yield_val = (rent_float * 12 / price_float) * 100  # float
            all_risk_yield_val = self.calculate_all_risk_yield(price_float, rent_float)  # float

            # Save calculated yield
            prop.rental_yield = Decimal(f"{rental_yield_val:.2f}")
            prop.all_risk_yield = Decimal(f"{all_risk_yield_val:.2f}")
            prop.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} properties."))
