from django.core.management.base import BaseCommand
from django.conf import settings
from polls.models import Propertysale
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mticker
from sklearn.preprocessing import LabelEncoder

class Command(BaseCommand):
    help = 'Generate static dashboard charts for Propertysale model'

    def handle(self, *args, **kwargs):
        output_dir = os.path.join(settings.BASE_DIR, "polls", "static", "dashboard_charts")
        os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(list(Propertysale.objects.all().values(
            'price', 'bedrooms', 'bathrooms', 'propertySize', 'Property_Type', 'county', 'ecode', 'publish_date','rental_yield','all_risk_yield_plus'
        )))

        # Property Type Merge Function
        def normalize_property_type(ptype):
            if not ptype or str(ptype).strip().lower() in ['', 'property']:
                return 'Other'

            ptype = str(ptype).strip().lower()

            if ptype in ['semi-d', 'semi-detached', 'terrace', 'detached', 'duplex',
                        'end of terrace', 'bungalow', 'townhouse', 'house', 'houses']:
                return 'House'
            elif ptype in ['apartment', 'studio', 'flat', 'bedsit']:
                return 'Apartment'
            elif ptype in ['site', 'land', 'development site']:
                return 'Site'
            else:
                return 'Other'

        df['Property_Type'] = df['Property_Type'].apply(normalize_property_type)


        if df.empty:
            self.stdout.write(self.style.WARNING("No data found."))
            return

        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
        df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')

        def convert_size(size):
            if pd.isna(size): return np.nan
            if isinstance(size, (int, float)): return float(size)
            s = str(size).strip()
            if 'm²' in s:
                try: return float(s.replace('m²', '').strip())
                except: return np.nan
            elif 'ac' in s:
                try: return float(s.replace('ac', '').strip()) * 4046.86
                except: return np.nan
            else:
                try: return float(s)
                except: return np.nan

        df['propertySize'] = df['propertySize'].apply(convert_size).astype(float)
        df['propertySize'] = df.groupby('bedrooms')['propertySize'].transform(lambda x: x.fillna(x.mean()))
        df['propertySize'].fillna(df['propertySize'].median(), inplace=True)

        for col in ['bathrooms', 'bedrooms', 'Property_Type']:
            df[col].fillna(df[col].mode()[0], inplace=True)

        if 'ecode' in df.columns and 'county' in df.columns:
            df['ecode'] = df.groupby('county')['ecode'].transform(lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown"))

        df['Property_Type'] = df['Property_Type'].fillna('Other')

        df['price'] = df.groupby(['county', 'bedrooms'])['price'].transform(lambda x: x.fillna(x.mean()))
        df['price'] = df.groupby('county')['price'].transform(lambda x: x.fillna(x.mean()))
        df['price'].fillna(df['price'].median(), inplace=True)

        df['publish_date'] = pd.to_datetime(df['publish_date'], errors='coerce')
        df.dropna(subset=['publish_date'], inplace=True)
        df['year_month'] = df['publish_date'].dt.to_period('M')

        df_full = df.copy()
        q_low = df['price'].quantile(0.01)
        q_hi = df['price'].quantile(0.99)
        filtered_price_df = df[(df['price'] >= q_low) & (df['price'] <= q_hi)]

        # Property Type Price Distributi Box plot
        plt.figure(figsize=(8, 5))
        sns.boxplot(x='Property_Type', y='price', data=filtered_price_df)
        plt.title("Price Distribution by Property Type")
        plt.xticks(rotation=45)
        plt.ylabel("Price (€)")
        ax = plt.gca()
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))        
        plt.savefig(os.path.join(output_dir, 'chart_boxplot.png'), bbox_inches='tight')
        plt.close()

        # Correlation heat map
        for col in ['Property_Type', 'county', 'ecode']:
            df_full[col] = LabelEncoder().fit_transform(df_full[col].astype(str))

        corr_features = ['price', 'bedrooms', 'bathrooms', 'propertySize', 'Property_Type', 'county']
        corr_matrix = df_full[corr_features].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Feature Correlation Heatmap")
        plt.savefig(os.path.join(output_dir, 'chart_heatmap.png'), bbox_inches='tight')
        plt.close()

        # Area vs Price Scatter plot (≤ 1000 Square meter)
        df_small = filtered_price_df[filtered_price_df['propertySize'] <= 1000]
        plt.figure(figsize=(6, 5))
        plt.scatter(df_small['propertySize'], df_small['price'], alpha=0.5)
        plt.title("Price vs Property Size (≤ 1000m²)")
        plt.xlabel("Property Size (m²)")
        plt.ylabel("Price (€)")
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_scatter.png'), bbox_inches='tight')
        plt.close()

        # Price Histogram
        plt.figure(figsize=(8, 5))
        ax = sns.histplot(filtered_price_df['price'], bins=50, kde=True, color='blue')
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        plt.title('Filtered Property Price Distribution')
        plt.xlabel("Price (€)")
        plt.ylabel("Frequency")
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(output_dir, 'chart_price_hist.png'), bbox_inches='tight')
        plt.close()

        # Time trend chart for the past 12 months
        monthly_avg = filtered_price_df.groupby('year_month')['price'].mean().sort_index()
        full_month_index = pd.date_range(end=pd.Timestamp.today(), periods=12, freq='M').to_period('M')
        monthly_avg = monthly_avg.reindex(full_month_index)
        months = [m.to_timestamp() for m in full_month_index]
        plt.figure(figsize=(8, 4))
        plt.plot(months, monthly_avg.values, marker='o')
        plt.title("Average Property Price in the Past Year")
        plt.xlabel("Month")
        plt.ylabel("Average Price (€)")
        ax = plt.gca()
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        plt.xticks(months, [m.strftime('%b %Y') for m in months], rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_timeseries.png'), bbox_inches='tight')
        plt.close()

        # Top 10 most expensive counties
        county_avg_price = filtered_price_df.groupby('county')['price'].mean().sort_values(ascending=False)

        plt.figure(figsize=(8, 4))
        county_avg_price.head(10).sort_values().plot(kind='barh', color='#BA68C8')
        plt.title('Top 10 Most Expensive Counties (Dublin by Postal Districts)')
        plt.xlabel('Average Price (€)')
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_expensive.png'), bbox_inches='tight')
        plt.close()

        # Top 10 least expensive counties
        plt.figure(figsize=(8, 4))
        county_avg_price.tail(10).sort_values().plot(kind='barh', color='#4DB6E2')
        plt.title('Top 10 Least Expensive Counties (Dublin by Postal Districts)')
        plt.xlabel('Average Price (€)')
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_cheap.png'), bbox_inches='tight')
        plt.close()

        # Top 10 counties by Rental Yield
        df_Rental = filtered_price_df[filtered_price_df['county'].notna() & (filtered_price_df['county'] != 'Unknown')]
        rental_yield_df = df_Rental.dropna(subset=['rental_yield'])
        county_avg_yield = rental_yield_df.groupby('county')['rental_yield'].mean().sort_values(ascending=False)

        # Highest rental yield counties
        plt.figure(figsize=(8, 4))
        (county_avg_yield.head(10) / 100).sort_values().plot(kind='barh', color='#FFA726')
        plt.title('Top 10 Highest Rental Yield Counties (AVG annual rent/AVG property price)', fontsize=12)
        plt.xlabel('Average Rental Yield (%)', fontsize=10)
        plt.ylabel('County', fontsize=10)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_high_rental.png'), bbox_inches='tight')
        plt.close()

        # Lowest rental yield counties
        plt.figure(figsize=(8, 4))
        (county_avg_yield.tail(10) / 100).sort_values().plot(kind='barh', color='#81C784')
        plt.title('Top 10 Lowest Rental Yield Counties', fontsize=12)
        plt.xlabel('Average Rental Yield (%)', fontsize=10)
        plt.ylabel('County', fontsize=10)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_low_rental.png'), bbox_inches='tight')
        plt.close()


        ML_all_risk_rental_yield_df = df_Rental.dropna(subset=['all_risk_yield_plus'])
        county_avg_mlyield = ML_all_risk_rental_yield_df.groupby('county')['all_risk_yield_plus'].mean().sort_values(ascending=False)
        # Highest Ml_ARRY counties
        plt.figure(figsize=(8, 4))
        (county_avg_mlyield.head(10) / 100).sort_values().plot(kind='barh', color='#FFA726')
        plt.title('Top 10 High All Risk Rental Yield (ML) Counties', fontsize=12)
        plt.xlabel('Average Rental Yield (%)', fontsize=10)
        plt.ylabel('County', fontsize=10)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_high_mlrental.png'), bbox_inches='tight')
        plt.close()

        # Lowest  Ml_ARRY counties
        plt.figure(figsize=(8, 4))
        (county_avg_mlyield.tail(10) / 100).sort_values().plot(kind='barh', color='#81C784')
        plt.title('Top 10 Lowest All Risk Rental Yield (ML) Counties', fontsize=12)
        plt.xlabel('Average Rental Yield (%)', fontsize=10)
        plt.ylabel('County', fontsize=10)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_low_mlrental.png'), bbox_inches='tight')
        plt.close()

        # Top 10 counties by number of properties sold
        df = pd.DataFrame(list(Propertysale.objects.all().values(
            'price', 'bedrooms', 'area', 'publish_date'
        )))
        df['year_month'] = df['publish_date'].dt.to_period('M')
        recent_12_months = pd.date_range(end=pd.Timestamp.today(), periods=12, freq='M').to_period('M')
        df_recent = df[df['year_month'].isin(recent_12_months)]
        df_nonnull_county = df_recent[df_recent['area'].notna() & (df_recent['area'].str.strip() != '')&(df_recent['area'].str.strip() != 'Unknown')]
        property_count_by_county = df_nonnull_county['area'].value_counts().sort_values(ascending=False)

        plt.figure(figsize=(8, 5))
        property_count_by_county.head(10).plot(kind='bar', color='#64B5F6') 
        plt.title('Top 10 Counties by Number of Properties Sold In the Past Year', fontsize=12)
        plt.xlabel('County', fontsize=10)
        plt.ylabel('Number of Properties', fontsize=10)
        plt.xticks(rotation=45, fontsize=8) 
        plt.yticks(fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_top10_property_sold.png'), bbox_inches='tight')
        plt.close()


        self.stdout.write(self.style.SUCCESS("Dashboard charts saved to static/dashboard_charts."))
