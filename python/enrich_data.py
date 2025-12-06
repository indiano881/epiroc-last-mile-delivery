"""
Epiroc Last-Mile Data Enrichment Pipeline
==========================================
This script enriches the raw shipment data with:
1. US Holidays
2. Weather data (Open-Meteo)
3. Economic indicators (FRED)
4. Traffic proxy features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import holidays
from tqdm import tqdm
import json
import time
import os
from typing import Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Paths
RAW_DATA_PATH = "../../last-mile-data.csv"
ENRICHED_DATA_PATH = "./enriched_shipments.csv"
ZIP_MAPPING_PATH = "./zip3_coordinates.json"

# API Keys (get your free FRED key at https://fred.stlouisfed.org/docs/api/api_key.html)
# Try to load from .env file first
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

load_env_file()
FRED_API_KEY = os.getenv("FRED_API_KEY", "YOUR_FRED_API_KEY_HERE")

# Open-Meteo Historical API (FREE, no key needed)
OPEN_METEO_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# ═══════════════════════════════════════════════════════════════
# ZIP CODE TO LAT/LON MAPPING
# ═══════════════════════════════════════════════════════════════

# Common US 3-digit ZIP code centroids (approximate)
# In production, use a complete database from simplemaps.com
ZIP3_COORDINATES = {
    # Northeast
    "010": (42.1, -72.6),   # MA
    "027": (42.4, -71.1),   # MA Boston area
    "049": (44.3, -69.0),   # ME
    "075": (40.9, -74.2),   # NJ
    "088": (40.2, -74.0),   # NJ
    "100": (40.7, -74.0),   # NY NYC
    "121": (42.7, -73.8),   # NY Albany
    "124": (41.5, -74.0),   # NY
    "136": (43.0, -76.1),   # NY Syracuse
    "153": (40.4, -80.0),   # PA Pittsburgh
    "155": (40.3, -78.9),   # PA
    "157": (40.3, -79.5),   # PA
    "160": (41.4, -79.7),   # PA
    "165": (41.0, -80.3),   # PA
    "171": (40.3, -76.9),   # PA
    "172": (40.0, -76.3),   # PA Lancaster/Harrisburg area
    "175": (40.3, -75.1),   # PA
    "184": (41.4, -75.6),   # PA Scranton
    "186": (41.2, -75.9),   # PA
    "201": (38.9, -77.0),   # DC/VA
    "212": (39.3, -76.6),   # MD Baltimore
    "215": (39.0, -76.5),   # MD
    "217": (39.4, -77.4),   # MD
    "226": (38.8, -77.1),   # VA
    "234": (37.5, -77.4),   # VA Richmond
    "240": (39.5, -77.8),   # MD/WV
    "241": (39.3, -76.6),   # MD
    "243": (37.3, -79.9),   # VA
    "253": (37.8, -79.4),   # VA
    "258": (37.3, -80.0),   # VA

    # Southeast
    "280": (35.2, -80.8),   # NC Charlotte
    "282": (35.8, -78.6),   # NC Raleigh
    "290": (34.0, -81.0),   # SC Columbia
    "293": (34.8, -82.4),   # SC
    "296": (34.0, -80.9),   # SC
    "300": (33.7, -84.4),   # GA Atlanta
    "301": (33.4, -84.2),   # GA
    "302": (33.9, -83.4),   # GA
    "305": (31.6, -84.2),   # GA
    "307": (32.5, -84.9),   # GA
    "318": (32.5, -93.7),   # LA
    "331": (25.8, -80.2),   # FL Miami
    "339": (28.5, -81.4),   # FL Orlando
    "370": (36.2, -86.8),   # TN Nashville
    "372": (35.0, -85.3),   # TN
    "377": (35.9, -83.9),   # TN Knoxville
    "379": (36.3, -82.4),   # TN
    "396": (32.3, -90.2),   # MS

    # Midwest
    "405": (41.7, -83.5),   # OH Toledo
    "416": (41.1, -81.5),   # OH Akron
    "437": (40.0, -82.9),   # OH Columbus
    "440": (41.5, -81.7),   # OH Cleveland
    "441": (41.1, -81.5),   # OH
    "442": (41.0, -80.8),   # OH Youngstown
    "443": (41.4, -82.1),   # OH
    "473": (39.8, -86.2),   # IN Indianapolis
    "479": (41.1, -85.1),   # IN Fort Wayne
    "492": (42.9, -85.7),   # MI Grand Rapids
    "498": (43.0, -83.7),   # MI Flint
    "513": (42.3, -83.0),   # MI/ON border
    "521": (41.6, -93.6),   # IA Des Moines
    "524": (42.5, -92.3),   # IA
    "528": (44.0, -92.5),   # MN
    "531": (43.0, -89.4),   # WI Madison
    "532": (43.0, -87.9),   # WI Milwaukee
    "540": (44.5, -88.0),   # WI Green Bay
    "543": (44.8, -89.6),   # WI
    "544": (44.9, -89.6),   # WI
    "557": (45.0, -93.3),   # MN Minneapolis
    "570": (43.5, -96.7),   # SD Sioux Falls
    "577": (46.9, -96.8),   # ND Fargo
    "590": (45.8, -108.5),  # MT Billings
    "591": (47.5, -111.3),  # MT Great Falls
    "601": (41.8, -88.1),   # IL
    "605": (41.9, -87.8),   # IL Chicago suburbs
    "610": (41.5, -90.6),   # IL
    "617": (40.7, -89.6),   # IL Peoria
    "622": (39.8, -89.6),   # IL Springfield
    "630": (38.6, -90.2),   # MO St. Louis
    "633": (39.1, -94.6),   # MO Kansas City
    "635": (39.1, -94.6),   # MO/KS
    "641": (38.9, -92.3),   # MO Columbia
    "667": (38.0, -97.3),   # KS

    # South Central
    "706": (30.2, -92.0),   # LA Lafayette
    "720": (34.7, -92.3),   # AR Little Rock
    "727": (33.4, -94.0),   # TX Texarkana
    "731": (35.4, -94.4),   # AR/OK
    "744": (36.2, -95.9),   # OK Tulsa
    "750": (32.8, -96.8),   # TX Dallas
    "752": (32.7, -97.3),   # TX Fort Worth
    "756": (31.8, -97.1),   # TX Waco
    "765": (33.2, -97.1),   # TX Denton
    "770": (29.8, -95.4),   # TX Houston
    "773": (29.4, -95.0),   # TX Houston area
    "780": (29.4, -98.5),   # TX San Antonio
    "786": (27.8, -97.4),   # TX Corpus Christi
    "787": (30.3, -97.7),   # TX Austin
    "794": (33.6, -101.8),  # TX Lubbock
    "799": (31.8, -106.4),  # TX El Paso

    # Mountain West
    "800": (39.7, -105.0),  # CO Denver
    "812": (38.3, -104.6),  # CO Colorado Springs
    "814": (40.4, -105.1),  # CO Fort Collins
    "827": (41.1, -104.8),  # WY Cheyenne
    "829": (42.9, -106.3),  # WY Casper
    "840": (40.8, -111.9),  # UT Salt Lake City
    "841": (40.7, -111.9),  # UT
    "850": (33.4, -112.0),  # AZ Phoenix
    "851": (33.4, -111.9),  # AZ Mesa
    "857": (32.2, -110.9),  # AZ Tucson
    "863": (34.5, -114.4),  # AZ
    "870": (35.1, -106.6),  # NM Albuquerque
    "874": (36.7, -108.2),  # NM Farmington
    "890": (36.2, -115.1),  # NV Las Vegas
    "893": (39.5, -119.8),  # NV Reno
    "894": (39.5, -119.8),  # NV
    "898": (36.1, -115.2),  # NV Las Vegas

    # Pacific West
    "906": (34.0, -118.2),  # CA Los Angeles
    "908": (33.8, -117.9),  # CA LA area
    "919": (33.8, -117.9),  # CA Orange County
    "920": (32.7, -117.2),  # CA San Diego
    "921": (32.8, -117.1),  # CA San Diego
    "923": (33.9, -117.4),  # CA Riverside
    "925": (33.8, -118.2),  # CA LA South Bay
    "932": (34.2, -119.2),  # CA Ventura
    "935": (35.4, -119.0),  # CA Bakersfield
    "945": (37.8, -122.4),  # CA San Francisco
    "956": (38.6, -121.5),  # CA Sacramento
    "958": (38.4, -121.4),  # CA Sacramento area
    "974": (45.5, -122.7),  # OR Portland
    "980": (47.6, -122.3),  # WA Seattle
    "982": (47.2, -122.5),  # WA Tacoma
    "984": (47.7, -122.2),  # WA Seattle area
}

def get_zip3_coordinates(zip3: str) -> tuple:
    """Get coordinates for a 3-digit ZIP code."""
    # Clean the zip code
    zip3_clean = zip3.replace("xx", "").strip()

    # Handle state codes
    state_to_coords = {
        "PA": (40.3, -76.3),
        "OH": (40.4, -82.9),
        "TX": (31.0, -100.0),
        "CA": (36.8, -119.4),
        "AZ": (34.0, -111.0),
        "FL": (28.0, -82.0),
        "GA": (33.0, -84.0),
        "NC": (35.5, -79.0),
        "SC": (34.0, -81.0),
        "TN": (36.0, -86.0),
        "VA": (37.5, -79.0),
        "WI": (44.0, -90.0),
        "MN": (46.0, -94.0),
        "MI": (44.0, -85.0),
        "IL": (40.0, -89.0),
        "MO": (38.5, -92.5),
        "CO": (39.0, -105.5),
        "NV": (39.0, -117.0),
        "OR": (44.0, -120.5),
        "WA": (47.5, -120.5),
        "NE": (41.5, -100.0),
        "MW": (42.0, -93.0),  # Midwest region
        "SO": (33.0, -90.0),  # South region
        "WE": (40.0, -115.0), # West region
        "NJ": (40.2, -74.5),
        "NY": (43.0, -75.0),
        "MD": (39.0, -76.7),
        "AR": (35.0, -92.5),
        "OK": (35.5, -97.5),
        "KS": (38.5, -98.0),
        "IA": (42.0, -93.5),
        "IN": (40.0, -86.0),
        "KY": (38.0, -85.5),
        "LA": (31.0, -92.0),
        "MS": (33.0, -90.0),
        "AL": (33.0, -87.0),
        "UT": (39.5, -111.5),
        "NM": (34.5, -106.0),
        "MT": (47.0, -110.0),
        "ND": (47.5, -100.5),
        "SD": (44.5, -100.0),
        "WY": (43.0, -107.5),
        "ID": (44.0, -114.5),
        "ME": (45.0, -69.0),
        "VT": (44.0, -72.7),
        "NH": (43.5, -71.5),
        "MA": (42.3, -72.0),
        "CT": (41.6, -72.7),
        "RI": (41.7, -71.5),
        "DE": (39.0, -75.5),
        "WV": (38.9, -80.5),
    }

    # Check if it's a state code
    if zip3_clean in state_to_coords:
        return state_to_coords[zip3_clean]

    # Check ZIP3 mapping
    if zip3_clean in ZIP3_COORDINATES:
        return ZIP3_COORDINATES[zip3_clean]

    # Try with leading zeros
    for i in range(3 - len(zip3_clean)):
        padded = "0" * (i + 1) + zip3_clean
        if padded in ZIP3_COORDINATES:
            return ZIP3_COORDINATES[padded]

    # Default to US center
    return (39.8, -98.6)


# ═══════════════════════════════════════════════════════════════
# HOLIDAY ENRICHMENT
# ═══════════════════════════════════════════════════════════════

def enrich_holidays(df: pd.DataFrame) -> pd.DataFrame:
    """Add holiday-related features to the dataframe."""
    print("Enriching with US holidays...")

    # Get US holidays for all years in the data
    years = df['ship_year'].unique()
    us_holidays = {}
    for year in years:
        us_holidays.update(holidays.US(years=year))

    holiday_dates = set(us_holidays.keys())

    def is_holiday(date):
        return date.date() in holiday_dates

    def get_holiday_name(date):
        return us_holidays.get(date.date(), None)

    def days_to_nearest_holiday(date, max_days=30):
        """Find days to nearest holiday (past or future)."""
        min_diff = max_days
        for hol_date in holiday_dates:
            diff = abs((hol_date - date.date()).days)
            if diff < min_diff:
                min_diff = diff
        return min_diff

    def is_holiday_week(date):
        """Check if date is within 3 days of a holiday."""
        return days_to_nearest_holiday(date, max_days=4) <= 3

    # Apply functions
    tqdm.pandas(desc="Checking ship holidays")
    df['is_ship_holiday'] = df['actual_ship'].progress_apply(is_holiday)

    tqdm.pandas(desc="Checking delivery holidays")
    df['is_delivery_holiday'] = df['actual_delivery'].progress_apply(
        lambda x: is_holiday(x) if pd.notna(x) else False
    )

    tqdm.pandas(desc="Getting holiday names")
    df['holiday_name'] = df['actual_ship'].progress_apply(get_holiday_name)

    tqdm.pandas(desc="Calculating days to holiday")
    df['days_to_holiday'] = df['actual_ship'].progress_apply(days_to_nearest_holiday)

    tqdm.pandas(desc="Checking holiday week")
    df['is_holiday_week'] = df['actual_ship'].progress_apply(is_holiday_week)

    return df


# ═══════════════════════════════════════════════════════════════
# WEATHER ENRICHMENT (Open-Meteo)
# ═══════════════════════════════════════════════════════════════

def fetch_weather_batch(lat: float, lon: float, start_date: str, end_date: str) -> Optional[Dict]:
    """Fetch weather data from Open-Meteo Historical API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                  "snowfall_sum", "wind_speed_10m_max", "weather_code"],
        "timezone": "America/New_York"
    }

    try:
        response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Weather API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None


def calculate_weather_severity(row: Dict) -> float:
    """Calculate weather severity score (0-10)."""
    score = 0

    # Precipitation (rain)
    precip = row.get('precipitation', 0) or 0
    if precip > 50:
        score += 4
    elif precip > 25:
        score += 3
    elif precip > 10:
        score += 2
    elif precip > 5:
        score += 1

    # Snowfall
    snow = row.get('snowfall', 0) or 0
    if snow > 30:
        score += 4
    elif snow > 15:
        score += 3
    elif snow > 5:
        score += 2
    elif snow > 1:
        score += 1

    # Wind
    wind = row.get('wind_speed_max', 0) or 0
    if wind > 80:
        score += 2
    elif wind > 50:
        score += 1

    return min(score, 10)


def enrich_weather(df: pd.DataFrame, sample_size: Optional[int] = None) -> pd.DataFrame:
    """Add weather data for origin and destination."""
    print("Enriching with weather data...")

    # Get unique ZIP3 + date combinations
    origin_combos = df[['origin_zip_3d', 'actual_ship']].drop_duplicates()
    origin_combos['date_str'] = origin_combos['actual_ship'].dt.strftime('%Y-%m-%d')

    if sample_size:
        origin_combos = origin_combos.head(sample_size)

    # Cache for weather data
    weather_cache = {}

    # Fetch weather for unique combinations
    print(f"Fetching weather for {len(origin_combos)} unique origin/date combinations...")

    for _, row in tqdm(origin_combos.iterrows(), total=len(origin_combos)):
        zip3 = row['origin_zip_3d']
        date_str = row['date_str']
        cache_key = f"{zip3}_{date_str}"

        if cache_key not in weather_cache:
            lat, lon = get_zip3_coordinates(zip3)
            weather_data = fetch_weather_batch(lat, lon, date_str, date_str)

            if weather_data and 'daily' in weather_data:
                daily = weather_data['daily']
                weather_cache[cache_key] = {
                    'temp_max': daily.get('temperature_2m_max', [None])[0],
                    'temp_min': daily.get('temperature_2m_min', [None])[0],
                    'precipitation': daily.get('precipitation_sum', [None])[0],
                    'snowfall': daily.get('snowfall_sum', [None])[0],
                    'wind_speed_max': daily.get('wind_speed_10m_max', [None])[0],
                    'weather_code': daily.get('weather_code', [None])[0],
                }
            else:
                weather_cache[cache_key] = {}

            # Rate limiting
            time.sleep(0.1)

    # Apply weather data to dataframe
    def get_origin_weather(row, field):
        cache_key = f"{row['origin_zip_3d']}_{row['actual_ship'].strftime('%Y-%m-%d')}"
        return weather_cache.get(cache_key, {}).get(field)

    df['origin_temp_max'] = df.apply(lambda r: get_origin_weather(r, 'temp_max'), axis=1)
    df['origin_temp_min'] = df.apply(lambda r: get_origin_weather(r, 'temp_min'), axis=1)
    df['origin_precipitation'] = df.apply(lambda r: get_origin_weather(r, 'precipitation'), axis=1)
    df['origin_snowfall'] = df.apply(lambda r: get_origin_weather(r, 'snowfall'), axis=1)

    # Calculate severity scores
    df['origin_weather_severity'] = df.apply(
        lambda r: calculate_weather_severity({
            'precipitation': r['origin_precipitation'],
            'snowfall': r['origin_snowfall'],
            'wind_speed_max': get_origin_weather(r, 'wind_speed_max')
        }), axis=1
    )

    return df


# ═══════════════════════════════════════════════════════════════
# ECONOMIC INDICATORS (FRED)
# ═══════════════════════════════════════════════════════════════

def fetch_fred_series(series_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch data from FRED API."""
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            df = pd.DataFrame(observations)
            if len(df) > 0:
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                return df[['date', 'value']]
        return pd.DataFrame()
    except Exception as e:
        print(f"FRED fetch error for {series_id}: {e}")
        return pd.DataFrame()


def enrich_economic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add economic indicators from FRED."""
    print("Enriching with economic indicators...")

    if FRED_API_KEY == "YOUR_FRED_API_KEY_HERE":
        print("WARNING: FRED API key not set. Skipping economic indicators.")
        df['freight_index'] = None
        df['fuel_price'] = None
        df['consumer_sentiment'] = None
        return df

    # Date range
    start_date = df['actual_ship'].min().strftime('%Y-%m-%d')
    end_date = df['actual_ship'].max().strftime('%Y-%m-%d')

    # Fetch Cass Freight Index
    print("Fetching Cass Freight Index...")
    freight_df = fetch_fred_series('FRGSHPUSM649NCIS', start_date, end_date)
    if len(freight_df) > 0:
        freight_df = freight_df.rename(columns={'value': 'freight_index'})
        freight_df['year_month'] = freight_df['date'].dt.to_period('M')

    # Fetch Oil Prices (proxy for fuel)
    print("Fetching Oil Prices...")
    oil_df = fetch_fred_series('DCOILWTICO', start_date, end_date)
    if len(oil_df) > 0:
        # Aggregate to monthly
        oil_df['year_month'] = oil_df['date'].dt.to_period('M')
        oil_monthly = oil_df.groupby('year_month')['value'].mean().reset_index()
        oil_monthly = oil_monthly.rename(columns={'value': 'fuel_price'})

    # Fetch Consumer Sentiment
    print("Fetching Consumer Sentiment...")
    sentiment_df = fetch_fred_series('UMCSENT', start_date, end_date)
    if len(sentiment_df) > 0:
        sentiment_df = sentiment_df.rename(columns={'value': 'consumer_sentiment'})
        sentiment_df['year_month'] = sentiment_df['date'].dt.to_period('M')

    # Merge with main dataframe
    df['year_month'] = df['actual_ship'].dt.to_period('M')

    if len(freight_df) > 0:
        df = df.merge(freight_df[['year_month', 'freight_index']], on='year_month', how='left')
    else:
        df['freight_index'] = None

    if len(oil_df) > 0:
        df = df.merge(oil_monthly[['year_month', 'fuel_price']], on='year_month', how='left')
    else:
        df['fuel_price'] = None

    if len(sentiment_df) > 0:
        df = df.merge(sentiment_df[['year_month', 'consumer_sentiment']], on='year_month', how='left')
    else:
        df['consumer_sentiment'] = None

    df = df.drop(columns=['year_month'])

    return df


# ═══════════════════════════════════════════════════════════════
# TRAFFIC PROXY FEATURES
# ═══════════════════════════════════════════════════════════════

def enrich_traffic_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """Add traffic proxy features derived from temporal data."""
    print("Enriching with traffic proxy features...")

    # Rush hour (shipping time between 7-9am or 4-7pm)
    df['ship_hour'] = df['actual_ship'].dt.hour
    df['is_rush_hour'] = df['ship_hour'].apply(
        lambda h: (7 <= h <= 9) or (16 <= h <= 19)
    )

    # Weekend
    df['is_weekend'] = df['ship_dow'].isin([5, 6])

    # Month end (last 3 days)
    df['day_of_month'] = df['actual_ship'].dt.day
    df['days_in_month'] = df['actual_ship'].dt.daysinmonth
    df['is_month_end'] = (df['days_in_month'] - df['day_of_month']) <= 3

    # Quarter end (last week of quarter)
    df['is_quarter_end'] = df['ship_month'].isin([3, 6, 9, 12]) & df['is_month_end']

    # Congestion score (composite)
    df['congestion_score'] = (
        df['is_rush_hour'].astype(int) * 2 +
        df['is_month_end'].astype(int) * 1 +
        df['is_quarter_end'].astype(int) * 2 +
        df['is_holiday_week'].astype(int) * 3 +
        df['origin_weather_severity'].fillna(0) * 0.5
    )

    # Clean up temp columns
    df = df.drop(columns=['ship_hour', 'day_of_month', 'days_in_month'])

    return df


# ═══════════════════════════════════════════════════════════════
# CARRIER & LANE PERFORMANCE
# ═══════════════════════════════════════════════════════════════

def calculate_historical_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate historical OTD rates for carriers and lanes."""
    print("Calculating historical performance metrics...")

    # Carrier performance
    carrier_stats = df.groupby('carrier_pseudo').agg({
        'otd_designation': [
            ('total', 'count'),
            ('on_time', lambda x: (x == 'On Time').sum()),
            ('early', lambda x: (x == 'Delivered Early').sum()),
            ('late', lambda x: (x == 'Late').sum()),
        ],
        'actual_transit_days': 'mean',
    }).reset_index()

    carrier_stats.columns = ['carrier_pseudo', 'total_shipments', 'on_time_count',
                             'early_count', 'late_count', 'avg_transit_days']
    carrier_stats['carrier_otd_rate'] = (
        (carrier_stats['on_time_count'] + carrier_stats['early_count']) /
        carrier_stats['total_shipments'] * 100
    )

    # Lane performance
    lane_stats = df.groupby('lane_id').agg({
        'otd_designation': [
            ('total', 'count'),
            ('on_time', lambda x: (x == 'On Time').sum()),
            ('early', lambda x: (x == 'Delivered Early').sum()),
            ('late', lambda x: (x == 'Late').sum()),
        ],
        'actual_transit_days': 'mean',
    }).reset_index()

    lane_stats.columns = ['lane_id', 'lane_total_shipments', 'lane_on_time_count',
                          'lane_early_count', 'lane_late_count', 'lane_avg_transit_days']
    lane_stats['lane_otd_rate'] = (
        (lane_stats['lane_on_time_count'] + lane_stats['lane_early_count']) /
        lane_stats['lane_total_shipments'] * 100
    )

    # Merge back
    df = df.merge(
        carrier_stats[['carrier_pseudo', 'carrier_otd_rate']],
        on='carrier_pseudo',
        how='left'
    )
    df = df.merge(
        lane_stats[['lane_id', 'lane_otd_rate', 'lane_avg_transit_days']],
        on='lane_id',
        how='left'
    )

    return df


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def main(skip_weather: bool = False, sample_size: Optional[int] = None):
    """Run the full enrichment pipeline."""
    print("=" * 60)
    print("EPIROC LAST-MILE DATA ENRICHMENT PIPELINE")
    print("=" * 60)

    # Load raw data
    print(f"\nLoading data from {RAW_DATA_PATH}...")
    df = pd.read_csv(RAW_DATA_PATH)
    print(f"Loaded {len(df):,} shipments")

    # Sample if requested
    if sample_size:
        print(f"Sampling {sample_size:,} rows for testing...")
        df = df.head(sample_size)

    # Parse dates
    print("\nParsing dates...")
    df['actual_ship'] = pd.to_datetime(df['actual_ship'])
    df['actual_delivery'] = pd.to_datetime(df['actual_delivery'])

    # Calculate delay (target variable)
    df['delay_days'] = df['actual_transit_days'] - df['all_modes_goal_transit_days']

    # Enrichment steps
    df = enrich_holidays(df)

    if not skip_weather:
        df = enrich_weather(df, sample_size=1000)  # Limit weather API calls
    else:
        print("Skipping weather enrichment...")
        df['origin_temp_max'] = None
        df['origin_temp_min'] = None
        df['origin_precipitation'] = None
        df['origin_snowfall'] = None
        df['origin_weather_severity'] = 0

    df = enrich_economic_indicators(df)
    df = enrich_traffic_proxy(df)
    df = calculate_historical_performance(df)

    # Save enriched data
    print(f"\nSaving enriched data to {ENRICHED_DATA_PATH}...")
    df.to_csv(ENRICHED_DATA_PATH, index=False)
    print(f"Saved {len(df):,} enriched shipments")

    # Print summary
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"Total shipments: {len(df):,}")
    print(f"Date range: {df['actual_ship'].min()} to {df['actual_ship'].max()}")
    print(f"\nOTD Distribution:")
    print(df['otd_designation'].value_counts())
    print(f"\nOverall OTD Rate: {(df['otd_designation'] != 'Late').mean() * 100:.1f}%")
    print(f"Holiday shipments: {df['is_ship_holiday'].sum():,}")
    print(f"Holiday week shipments: {df['is_holiday_week'].sum():,}")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich shipment data")
    parser.add_argument("--skip-weather", action="store_true", help="Skip weather API calls")
    parser.add_argument("--sample", type=int, help="Sample size for testing")

    args = parser.parse_args()

    df = main(skip_weather=args.skip_weather, sample_size=args.sample)
