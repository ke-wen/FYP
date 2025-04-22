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
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class Command(BaseCommand):
    help = 'Generate static dashboard charts for Propertysale model'

    def handle(self, *args, **kwargs):
        output_dir = os.path.join(settings.BASE_DIR, "polls", "static", "dashboard_charts")
        os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(list(Propertysale.objects.all().values(
            'price', 'bedrooms', 'bathrooms', 'propertySize', 'Property_Type', 'county', 'ecode', 'publish_date'
        )))

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
        filtered_price_df = df[(df['price'] > 10000) & (df['price'] < 4000000)]

        # Property Type Price Distributi Box plot
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='Property_Type', y='price', data=filtered_price_df)
        plt.title("Price Distribution by Property Type")
        plt.xticks(rotation=45)
        plt.ylabel("Price (€)")
        plt.savefig(os.path.join(output_dir, 'chart_boxplot.png'), bbox_inches='tight')
        plt.close()

        # Correlation heat map
        for col in ['Property_Type', 'county', 'ecode']:
            df_full[col] = LabelEncoder().fit_transform(df_full[col].astype(str))

        corr_features = ['price', 'bedrooms', 'bathrooms', 'propertySize', 'Property_Type', 'county', 'ecode']
        corr_matrix = df_full[corr_features].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Feature Correlation Heatmap")
        plt.savefig(os.path.join(output_dir, 'chart_heatmap.png'), bbox_inches='tight')
        plt.close()

        # Random Forest Feature Importance Bar Chart
        df_rf = df_full.copy()
        features = ['bedrooms', 'bathrooms', 'propertySize', 'Property_Type', 'county', 'ecode']
        X = df_rf[features]
        y = df_rf['price']
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        importances = model.feature_importances_
        importance_df = pd.DataFrame({
            'Feature': features,
            'Importance': importances
        }).sort_values(by='Importance', ascending=True)

        plt.figure(figsize=(8, 5))
        plt.barh(importance_df['Feature'], importance_df['Importance'])
        plt.title("Feature Importance (Random Forest)")
        plt.xlabel("Importance")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_feature_importance.png'), bbox_inches='tight')
        plt.close()

        # Area vs Price Scatter plot (Less than or equal to 1000 Square meter)
        df_small = filtered_price_df[filtered_price_df['propertySize'] <= 1000]
        plt.figure(figsize=(6, 5))
        plt.scatter(df_small['propertySize'], df_small['price'], alpha=0.5)
        plt.title("Price vs Property Size (≤ 1000㎡)")
        plt.xlabel("Property Size (m²)")
        plt.ylabel("Price (€)")
        plt.savefig(os.path.join(output_dir, 'chart_scatter.png'), bbox_inches='tight')
        plt.close()

        # Price Histogram
        plt.figure(figsize=(8, 5))
        ax = sns.histplot(filtered_price_df['price'], bins=50, kde=True, color='blue')
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter('€{x:,.0f}'))
        plt.title('Filtered Property Price Distribution')
        plt.xlabel("Price (€)")
        plt.ylabel("Frequency")
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(output_dir, 'chart_price_hist.png'), bbox_inches='tight')
        plt.close()

        # Time trend chart
        monthly_avg = df_full.groupby('year_month')['price'].mean().sort_index()
        months = [pd.Period(m).to_timestamp() for m in monthly_avg.index]
        plt.figure(figsize=(8, 4))
        plt.plot(months, monthly_avg.values, marker='o')
        plt.title("Average Property Price by Month")
        plt.xlabel("Month")
        plt.ylabel("Average Price (€)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'chart_timeseries.png'), bbox_inches='tight')
        plt.close()


        self.stdout.write(self.style.SUCCESS("Dashboard charts saved to static/dashboard_charts."))
