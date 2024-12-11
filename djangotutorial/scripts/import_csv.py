import csv
from polls.models import Propertysale

def import_sale(file_path):
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:

            if not Propertysale.objects.filter(id=row['id']).exists():
                Propertysale.objects.create(
                    id=row['id'],
                    title=row['title'],
                    ecode=row['ecode'],
                    country=row['country'],
                    Property_Type=row['Property_Type'],
                    price=row['price'] or None,
                    publish_date=row['publish_date'] or None,
                    bedrooms=int(float(row['bedrooms'])) if row['bedrooms'] else None,  
                    bathrooms=int(float(row['bathrooms'])) if row['bathrooms'] else None,
                    propertySize = row['propertySize'] or None,
                    link=row['link'] or None,
                )
    print("Data import completed")


def import_rent(file_path):
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:

            if not Propertysale.objects.filter(id=row['id']).exists():
                Propertysale.objects.create(
                    id=row['id'],
                    title=row['title'],
                    ecode=row['ecode'],
                    country=row['country'],
                    Property_Type=row['Property_Type'],
                    price=row['price'] or None,
                    publish_date=row['publish_date'] or None,
                    bedrooms=int(float(row['bedrooms'])) if row['bedrooms'] else None,  
                    bathrooms=int(float(row['bathrooms'])) if row['bathrooms'] else None,
                    link=row['link'] or None,
                )
    print("Data import completed")

