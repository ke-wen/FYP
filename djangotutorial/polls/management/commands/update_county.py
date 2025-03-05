from django.core.management.base import BaseCommand
from polls.models import Propertysale, Propertyrent

# 更新后的 Dublin & Greater Dublin Area 对应字典
eircode_to_city = {
    "D01": "Dublin 1", "D02": "Dublin 2", "D03": "Dublin 3", "D04": "Dublin 4",
    "D05": "Dublin 5", "D06": "Dublin 6", "D07": "Dublin 7", "D08": "Dublin 8",
    "D09": "Dublin 9", "D10": "Dublin 10", "D11": "Dublin 11", "D12": "Dublin 12",
    "D13": "Dublin 13", "D14": "Dublin 14", "D15": "Dublin 15", "D16": "Dublin 16",
    "D17": "Dublin 17", "D18": "Dublin 18", "D20": "Dublin 20", "D22": "Dublin 22",
    "D24": "Dublin 24", "D6W": "Dublin 6W",
    "A94": "Blackrock", "A96": "Glenageary", "A98": "Bray",
    "A41": "Ballyboughal", "A42": "Garristown", "A45": "Oldtown",
    "A84": "Ashbourne", "A85": "Dunshaughlin", "A86": "Dunboyne",
    "K32": "Balbriggan", "K34": "Skerries", "K36": "Malahide",
    "K45": "Lusk", "K56": "Rush", "K67": "Swords", "K78": "Lucan",
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
class Command(BaseCommand):
    help = "Force update county names in Propertysale and Propertyrent tables based on first 3 characters of ecode."

    def update_table(self, model):
        updated_count = 0
        for property in model.objects.all():
            if property.ecode and len(property.ecode) >= 3: 
                ecode_prefix = property.ecode[:3] 
                new_county = eircode_to_city.get(ecode_prefix, "Unknown")
                if new_county:  
                    property.county = new_county
                    property.save()
                    updated_count += 1
        return updated_count

    def handle(self, *args, **kwargs):
        updated_sale = self.update_table(Propertysale)
        updated_rent = self.update_table(Propertyrent)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_sale} Propertysale records."))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_rent} Propertyrent records."))
