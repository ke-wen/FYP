# polls/management/commands/update_yields_plus.py
from django.core.management.base import BaseCommand
from django.db.models import Avg
from polls.models import Propertysale, Propertyrent
import numpy_financial as npf
from decimal import Decimal
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = "Update all_risk_yield_plus field for Propertysale using machine learning to predict property price after 5 years"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting process..."))
        
        # Prepare dataset
        self.prepare_data()
        
        # Train model
        self.train_model()
        
        # Get average rent information
        rent_map = self.get_rent_map()
        
        # Update all_risk_yield_plus field
        updated_count = self.update_yields_plus(rent_map)
        
        self.stdout.write(self.style.SUCCESS(f"Updated all_risk_yield_plus for {updated_count} properties."))

    def prepare_data(self):
        """Prepare dataset, process missing values and encode categorical variables"""
        self.stdout.write("Preparing data...")
        
        # Get all data from Propertysale model
        queryset = Propertysale.objects.filter(is_active=True)
        df = pd.DataFrame(list(queryset.values(
            'id', 'title', 'ecode', 'Property_Type', 'price', 'publish_date',
            'bedrooms', 'bathrooms', 'propertySize', 'county', 'area'
        )))
        
        # Convert Decimal to float to avoid type errors
        if 'price' in df.columns:
            df['price'] = df['price'].astype(float)
        
        # Process missing values
        self.process_missing_values(df)
        
        # Save processed dataframe
        self.df = df
        self.stdout.write(self.style.SUCCESS("Data preparation complete!"))
        
    def process_missing_values(self, df):
        """Process missing values, similar to the strategy in untitled.py"""
        # Convert propertySize
        df['propertySize'] = df['propertySize'].apply(self.convert_size)
        
        # Calculate average area for same bedrooms group
        bedroom_grouped_avg_size = df.groupby('bedrooms')['propertySize'].transform('mean')
        
        # Fill missing propertySize
        df['propertySize'].fillna(bedroom_grouped_avg_size, inplace=True)
        
        # If all propertySize in a bedrooms group are NaN, fill with overall median
        median_size = df['propertySize'].median()
        df['propertySize'].fillna(median_size, inplace=True)
        
        # Fill bathrooms, bedrooms and Property_Type with mode
        for col in ['bathrooms', 'bedrooms', 'Property_Type']:
            if col in df.columns and df[col].isnull().any():
                df[col].fillna(df[col].mode()[0], inplace=True)
        
        # Fill ecode with mode from same county
        if 'ecode' in df.columns and 'county' in df.columns:
            df['ecode'] = df.groupby('county')['ecode'].transform(
                lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown")
            )
        
        # Fill price with mean from same county and bedrooms 
        df['price'] = df.groupby(['county', 'bedrooms'])['price'].transform(lambda x: x.fillna(x.mean()))
        df['price'] = df.groupby('county')['price'].transform(lambda x: x.fillna(x.mean()))
        df['price'].fillna(df['price'].median(), inplace=True)
        
        # Fill missing title
        missing_title_mask = df['title'].isna()
        if missing_title_mask.any():
            df.loc[missing_title_mask, 'title'] = df[missing_title_mask][
                ['county', 'bedrooms', 'propertySize', 'Property_Type']
            ].astype(str).agg(' | '.join, axis=1)

    def convert_size(self, size):
        """Convert area units to square meters"""
        if pd.isna(size):
            return np.nan
            
        if isinstance(size, (int, float)):
            return float(size)
            
        size = str(size).strip()
        if 'm²' in size:
            return float(size.replace('m²', '').strip())
        elif 'ac' in size:
            return float(size.replace('ac', '').strip()) * 4046.86
        else:
            try:
                return float(size)
            except:
                return np.nan

    def train_model(self):
        """Train random forest model to predict property prices"""
        self.stdout.write("Training machine learning model...")
        
        df = self.df.copy()
        
        # Ensure publish_date is datetime type with timezone handling
        df['publish_date'] = pd.to_datetime(df['publish_date'])
        
        # Force timezone to be naive for consistent calculations
        if df['publish_date'].dt.tz is not None:
            df['publish_date'] = df['publish_date'].dt.tz_localize(None)
            
        min_date = df['publish_date'].min()
        
        # Calculate days feature
        df['days_since_min'] = (df['publish_date'] - min_date).dt.days
        
        # Prepare encoders for categorical features
        self.label_encoders = {}
        categorical_cols = ['Property_Type', 'county', 'ecode']
        
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        # Apply log transformation to price
        df['log_price'] = np.log1p(df['price'])
        
        # Calculate price trend
        yearly_avg_log_prices = df.groupby(
            df['publish_date'].dt.year
        )['log_price'].mean().reset_index()
        
        yearly_avg_log_prices['year_date'] = pd.to_datetime(
            yearly_avg_log_prices['publish_date'].astype(str) + '-01-01'
        )
        
        # Ensure year_date has same timezone properties as min_date
        if hasattr(min_date, 'tz') and min_date.tz is not None:
            yearly_avg_log_prices['year_date'] = yearly_avg_log_prices['year_date'].dt.tz_localize(min_date.tz)
        else:
            yearly_avg_log_prices['year_date'] = yearly_avg_log_prices['year_date'].dt.tz_localize(None)
        yearly_avg_log_prices = yearly_avg_log_prices.sort_values('year_date')
        
        # Calculate log price trend coefficient
        from sklearn.linear_model import LinearRegression
        days_array = (yearly_avg_log_prices['year_date'] - min_date).dt.days.values.reshape(-1, 1)
        log_price_array = yearly_avg_log_prices['log_price'].values
        log_trend_model = LinearRegression()
        log_trend_model.fit(days_array, log_price_array)
        self.log_price_trend_coef = log_trend_model.coef_[0]

        # Prepare features and target variables
        self.features = [
            'bedrooms', 'bathrooms', 'propertySize',
            'Property_Type', 'county', 'ecode',
            'days_since_min'
        ]
        
        # Only use rows with all features
        valid_rows = df[self.features + ['log_price']].dropna()
        
        if len(valid_rows) < 10:
            self.stdout.write(self.style.WARNING("Warning: Insufficient valid data, will use simplified model!"))
            # If too few data points, create a simple model
            self.model = None
            self.scaler = None
            self.min_date = min_date
            return
            
        X = valid_rows[self.features]
        y = valid_rows['log_price']
        
        # Split training and test sets chronologically
        df_sorted = valid_rows.sort_values('days_since_min')
        train_size = 0.8
        train_idx = int(len(df_sorted) * train_size)
        
        X_train = df_sorted[self.features].iloc[:train_idx]
        y_train = df_sorted['log_price'].iloc[:train_idx]
        
        # Standardize numerical features
        self.num_cols = ['bedrooms', 'bathrooms', 'propertySize', 'days_since_min']
        self.scaler = StandardScaler()
        
        X_train_scaled = X_train.copy()
        X_train_scaled[self.num_cols] = self.scaler.fit_transform(X_train[self.num_cols])
        
        # Train random forest model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train_scaled, y_train)
        
        self.min_date = min_date
        self.stdout.write(self.style.SUCCESS("Model training complete!"))

    def predict_future_price(self, property_features, years):
        """Predict future property price"""
        if self.model is None:
            # If model not available, use simple annual growth rate calculation
            current_price = property_features.get('price', 0)
            if current_price <= 0:
                return 0
            return current_price * (1 + 0.052) ** years
            
        # Create future date with consistent timezone handling
        future_date = datetime.now()
        
        # Ensure future_date has same timezone properties as min_date
        if hasattr(self.min_date, 'tz') and self.min_date.tz is not None:
            # Use timezone-aware datetime
            import pytz
            future_date = pytz.timezone('UTC').localize(future_date)
        else:
            # Use timezone-naive datetime
            future_date = future_date.replace(tzinfo=None)
            
        future_date = future_date + timedelta(days=365 * years)
        
        X_future = pd.DataFrame([property_features])
        
        # Encode categorical features
        for col, encoder in self.label_encoders.items():
            if col in X_future.columns:
                if X_future[col].iloc[0] in encoder.classes_:
                    X_future[col] = encoder.transform([X_future[col].iloc[0]])
                else:
                    # If value not in training set, use most common category
                    X_future[col] = 0
        
        # Add days feature
        X_future['days_since_min'] = (future_date - self.min_date).days
        
        # Keep only features needed for the model
        X_future = X_future[self.features]
        
        # Standardize numerical features
        X_future[self.num_cols] = self.scaler.transform(X_future[self.num_cols])
        
        # Predict log price
        log_prediction = self.model.predict(X_future)[0]
        
        # Convert back to original scale
        predicted_price = np.expm1(log_prediction)
        
        return predicted_price

    def get_rent_map(self):
        """Get average rent information"""
        self.stdout.write("Getting average rent information...")
        
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
                
        return rent_map

    def calculate_all_risk_yield_plus(self, initial_investment, monthly_rent, future_price):
        """Calculate all_risk_yield_plus, similar to all_risk_yield but using predicted future price"""
        maintenance_percentage = 0.34
        holding_period = 3
        income_growth_rate = 0.02
        rental_review_period = 12
        
        net_annual_income = monthly_rent 
        cash_flows = [-initial_investment]
        
        for year in range(holding_period):
            growth_cycles = year // rental_review_period
            adjusted_income = net_annual_income * (1 + income_growth_rate) ** growth_cycles
            maintenance_cost = adjusted_income * maintenance_percentage
            net_cash_flow = adjusted_income - maintenance_cost
            cash_flows.append(net_cash_flow)
            
        # Use predicted future price
        cash_flows[-1] += future_price
        
        try:
            irr_float = npf.irr(cash_flows)  # Calculate IRR
            if np.isnan(irr_float) or irr_float <= -1:
                return 0.0
            
            e = irr_float
            g = income_growth_rate
            t = rental_review_period
            k0 = e - e * (((1 + g) ** t - 1) / ((1 + e) ** t - 1))
            return k0 * 100
        except:
            return 0.0

    def update_yields_plus(self, rent_map):
        """Update all_risk_yield_plus for each property"""
        self.stdout.write("Updating all_risk_yield_plus...")
        
        updated_count = 0
        sales = Propertysale.objects.filter(is_active=True)
        
        for prop in sales:
            if prop.price is None or prop.county is None or prop.bedrooms is None:
                continue
                
            # Check if corresponding rent data exists
            if (prop.county, prop.bedrooms) not in rent_map:
                continue
                
            price_float = float(prop.price)
            rent_float = rent_map[(prop.county, prop.bedrooms)]
            
            if price_float <= 0 or rent_float <= 0:
                continue
                
            # Get property features for future price prediction
            property_features = {
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'propertySize': self.convert_size(prop.propertySize),
                'Property_Type': prop.Property_Type,
                'county': prop.county,
                'ecode': prop.ecode,
                'price': price_float  # For simplified model
            }
            
            # Predict price after 5 years
            future_price = self.predict_future_price(property_features, years=1)
            
            # Calculate all_risk_yield_plus
            all_risk_yield_plus_val = self.calculate_all_risk_yield_plus(
                price_float, rent_float, future_price
            )
            
            # Save calculated result

            prop.all_risk_yield_plus = Decimal(f"{all_risk_yield_plus_val:.2f}")
            prop.save(update_fields=['all_risk_yield_plus'])
            updated_count += 1
                
        return updated_count