import re
from daftlistings import Daft, SearchType
from django.core.management.base import BaseCommand
from polls.models import Propertysale, Propertyrent
from geopy.geocoders import Nominatim
#Dictionary of the first three digits of the postal code and the city it corresponds to
eircode_to_city = {
    "D01": "Dublin", "D02": "Dublin", "D03": "Dublin", "D04": "Dublin",
    "D05": "Dublin", "D06": "Dublin", "D07": "Dublin", "D08": "Dublin",
    "D09": "Dublin", "D10": "Dublin", "D11": "Dublin", "D12": "Dublin",
    "D13": "Dublin", "D14": "Dublin", "D15": "Dublin", "D16": "Dublin",
    "D17": "Dublin", "D18": "Dublin", "D20": "Dublin", "D22": "Dublin",
    "D24": "Dublin", "D6W": "Dublin",
    "A94": "Dublin", "A96": "Dublin", "A98": "Dublin",
    "A41": "Greater Dublin Area", "A42": "Greater Dublin Area",
    "A45": "Greater Dublin Area", "A84": "Greater Dublin Area",
    "A85": "Greater Dublin Area", "A86": "Greater Dublin Area",
    "K32": "Greater Dublin Area", "K34": "Greater Dublin Area",
    "K36": "Greater Dublin Area", "K45": "Greater Dublin Area",
    "K56": "Greater Dublin Area", "K67": "Greater Dublin Area",
    "K78": "Greater Dublin Area",
    "A63": "Wicklow", "A67": "Wicklow", "A75": "Monaghan",
    "A81": "Monaghan", "A82": "Meath", "A83": "Meath",
    "A91": "Louth", "A92": "Louth", "C15": "Meath",
    "E21": "Tipperary", "E25": "Tipperary", "E32": "Tipperary",
    "E34": "Tipperary", "E41": "Tipperary", "E45": "Tipperary",
    "E53": "Tipperary", "E91": "Tipperary", "F12": "Mayo",
    "F23": "Mayo", "F26": "Mayo", "F28": "Mayo", "F31": "Mayo",
    "F35": "Mayo", "F42": "Roscommon", "F45": "Roscommon",
    "F52": "Roscommon", "F56": "Sligo", "F91": "Sligo",
    "F92": "Donegal", "F93": "Donegal", "F94": "Donegal",
    "H12": "Cavan", "H14": "Cavan", "H16": "Cavan",
    "H18": "Monaghan", "H23": "Monaghan", "H53": "Galway",
    "H54": "Galway", "H62": "Galway", "H65": "Galway",
    "H71": "Galway", "H91": "Galway", "N37": "Westmeath/Roscommon",
    "N39": "Longford", "N41": "Leitrim", "N91": "Westmeath",
    "P12": "Cork", "P14": "Cork", "P17": "Cork", "P24": "Cork",
    "P25": "Cork", "P31": "Cork", "P32": "Cork", "P36": "Cork",
    "P43": "Cork", "P47": "Cork", "P51": "Cork", "P56": "Cork",
    "P61": "Cork", "P67": "Cork", "P72": "Cork", "P75": "Cork",
    "P81": "Cork", "P85": "Cork", "R14": "Kildare", "R21": "Carlow",
    "R32": "Laois", "R35": "Offaly", "R42": "Offaly", "R45": "Offaly",
    "R51": "Kildare", "R56": "Kildare", "R93": "Carlow", "R95": "Kilkenny",
    "T12": "Cork", "T23": "Cork", "T34": "Cork", "T45": "Cork",
    "T56": "Cork", "V14": "Clare", "V15": "Clare", "V23": "Kerry",
    "V31": "Kerry", "V35": "Limerick", "V42": "Limerick", "V92": "Kerry",
    "V93": "Kerry", "V94": "Limerick", "V95": "Clare", "W12": "Kildare",
    "W23": "Kildare", "W34": "Kildare", "W91": "Kildare", "X35": "Waterford",
    "X42": "Waterford", "X91": "Waterford", "Y14": "Wicklow", "Y21": "Wexford",
    "Y25": "Wexford", "Y34": "Wexford", "Y35": "Wexford"
}


def get_postal_code(lat, lon):
    """Convert latitude and longitude to ecode using Nominatim's library"""
    geolocator = Nominatim(user_agent="kefyp_django_geopy", timeout=10)
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location and 'address' in location.raw:
        return location.raw['address'].get('postcode')
    return None

def to_num(price_string):
    """Convert a string to a number"""
    try:
        euro_match = re.search(r"€\s?\d+(?:,\d{3})*(?:\.\d+)?", price_string)
        if euro_match:
            numeric_price = re.sub(r"[^\d.]", "", euro_match.group(0))
            return float(numeric_price)

        match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", price_string)
        if match:
            numeric_price = match.group(0).replace(',', '')
            return float(numeric_price)
    except:
        return None
    return None

def to_county_and_ecode(latitude, longitude):
    """Get ecode and city"""
    postal_code = get_postal_code(latitude, longitude)
    if postal_code:
        ecode = postal_code[:3]
        city = eircode_to_city.get(ecode, "Unknown")
        return postal_code, city
    return None, "Unknown"

class Command(BaseCommand):
    help = "Crawl real propertys data and update the database (only insert new data"

    def fetch_existing_ids(self, model):
        """Get all existing ids"""
        return set(model.objects.values_list('id', flat=True))

    def bulk_insert_new(self, listings, model, is_sale=False):
        existing_ids = self.fetch_existing_ids(model)  
        seen_ids = set()
        updated_entries = set()
        new_entries = []


        for listing in listings:
            if listing.id in existing_ids:
                # The data already exists, and the update status is active
                updated_entries.add(listing.id)
                model.objects.filter(id=listing.id).update(is_active=True)
            elif listing.id in seen_ids:
                # Recording duplicate IDs
                self.stdout.write(f"Duplicate ID found in new data: {listing.id}")
            else:
                # If the data does not exist, insert a new record
                seen_ids.add(listing.id)
                updated_entries.add(listing.id)
                ecode, county = to_county_and_ecode(listing.latitude, listing.longitude)
                entry_data = {
                    'id': listing.id,
                    'title': listing._result.get('title') or listing._result.get('seoTitle', 'N/A'),
                    'ecode': ecode,
                    'county': county,
                    'Property_Type': listing._result.get('propertyType'),
                    'price': to_num(listing.price),
                    'publish_date': listing.publish_date,
                    'bedrooms': int(float(to_num(listing._result.get("numBedrooms", "0")))) if listing._result.get("numBedrooms") else None,
                    'bathrooms': int(float(to_num(listing._result.get("numBathrooms", "0")))) if listing._result.get("numBathrooms") else None,
                    'link': listing.daft_link,
                    'is_active': True  # New records are active by default
                }
                if is_sale:
                    entry_data['propertySize'] = listing._result.get("propertySize", "N/A")
                new_entries.append(model(**entry_data))

        # Inserting New Data
        if new_entries:
            model.objects.bulk_create(new_entries)
            self.stdout.write(f"Added {len(new_entries)} new records.")

        # Mark data not in the crawl results as inactive
        inactive_ids = existing_ids - updated_entries
        model.objects.filter(id__in=inactive_ids).update(is_active=False)
        self.stdout.write(f"Marked {len(inactive_ids)} records as inactive.")

        



    def handle(self, *args, **kwargs):
        daft = Daft()

        # Get data on properties for sale
        daft.set_search_type(SearchType.RESIDENTIAL_SALE)
        sale_listings = daft.search()
        self.stdout.write(f"find {len(sale_listings)} properties for sale")
        self.bulk_insert_new(sale_listings, Propertysale, is_sale=True)

        # Get data on properties for rent
        daft.set_search_type(SearchType.RESIDENTIAL_RENT)
        rent_listings = daft.search()
        self.stdout.write(f"find {len(rent_listings)} properties for rent")
        self.bulk_insert_new(rent_listings, Propertyrent, is_sale=False)

        self.stdout.write("Database update completed")

#python manage.py update_properties
