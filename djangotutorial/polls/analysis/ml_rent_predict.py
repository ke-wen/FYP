# ml_rent_predict.py - 用于训练租金预测模型和预测未来租金

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
import xgboost as xgb

def train_rent_model(df_rent_raw):
    df = df_rent_raw.copy()
    df['publish_date'] = pd.to_datetime(df['publish_date'])
    df = df[df['publish_date'] >= '2024-09-01']
    q_low, q_high = df['price'].quantile([0.01, 0.99])
    df = df[(df['price'] >= q_low) & (df['price'] <= q_high)]


    for col in ['bathrooms', 'bedrooms', 'Property_Type']:
        if col in df.columns and df[col].isnull().any():
            df[col].fillna(df[col].mode()[0], inplace=True)

    if 'ecode' in df.columns and 'county' in df.columns:
        df['ecode'] = df.groupby('county')['ecode'].transform(
            lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "Unknown")
        )

    df['price'] = df.groupby(['county', 'bedrooms'])['price'].transform(lambda x: x.fillna(x.mean()))
    df['price'] = df.groupby('county')['price'].transform(lambda x: x.fillna(x.mean()))
    df['price'].fillna(df['price'].median(), inplace=True)

    df['log_price'] = np.log1p(df['price'])
    df['days_since_min'] = (df['publish_date'] - df['publish_date'].min()).dt.days


    categorical_cols = ['Property_Type', 'county', 'ecode']
    encoders = {}
    for col in categorical_cols:
        df[col] = df[col].astype(str)
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col])
        encoders[col] = enc

    features = ['bedrooms', 'bathrooms', 'Property_Type', 'county', 'ecode', 'days_since_min']
    target = 'log_price'
    num_cols = ['bedrooms', 'bathrooms', 'days_since_min']

    df = df.sort_values('publish_date')
    split_idx = int(len(df) * 0.8)
    X = df[features]
    y = df[target]
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
    X_test[num_cols] = scaler.transform(X_test[num_cols])

    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    daily_trend = df.groupby(df['publish_date'].dt.date)['log_price'].mean().reset_index()
    daily_trend['publish_date'] = pd.to_datetime(daily_trend['publish_date'])
    daily_trend['days_since_start'] = (daily_trend['publish_date'] - df['publish_date'].min()).dt.days
    trend_model = LinearRegression()
    trend_model.fit(daily_trend[['days_since_start']], daily_trend['log_price'])

    return model, scaler, trend_model, df['publish_date'].min(), split_idx, encoders, X_train, y_train


def calculate_predicted_rents_for_property(
    property_features,
    model,
    scaler,
    trend_model,
    min_date,
    split_idx,
    maintenance_percentage=0.34
):
    num_cols = ['bedrooms', 'bathrooms', 'days_since_min']
    future_dates = [datetime.now() + timedelta(days=365 * i) for i in range(1, 6)]
    annual_rents = []

    for future_date in future_dates:
        days_since_min_val = (future_date - min_date).days
        X_future = pd.DataFrame([{**property_features, 'days_since_min': days_since_min_val}])
        X_future[num_cols] = scaler.transform(X_future[num_cols])

        log_rent_base = model.predict(X_future)[0]
        max_train_date = min_date + timedelta(days=365 * 4)
        days_beyond_training = max(0, (future_date - max_train_date).days)
        daily_coef = trend_model.coef_[0]
        adjusted_log_rent = log_rent_base + days_beyond_training * daily_coef

        monthly_rent = np.expm1(adjusted_log_rent)
        annual_rent = monthly_rent * 12
        annual_rents.append(annual_rent)

    return annual_rents
