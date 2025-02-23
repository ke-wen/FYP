from django.core.management.base import BaseCommand
from polls.models import Propertysale, Propertyrent

# 更新后的 Dublin & Greater Dublin Area 对应字典
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
class Command(BaseCommand):
    help = "Force update county names in Propertysale and Propertyrent tables based on first 3 characters of ecode."

    def update_table(self, model):
        updated_count = 0
        for property in model.objects.all():
            if property.ecode and len(property.ecode) >= 3:  # 确保 ecode 存在且长度足够
                ecode_prefix = property.ecode[:3]  # 取前三位
                new_county = eircode_to_city.get(ecode_prefix, "Unknown")
                if new_county:  # 只要找到新值就直接更新
                    property.county = new_county
                    property.save()
                    updated_count += 1
        return updated_count

    def handle(self, *args, **kwargs):
        updated_sale = self.update_table(Propertysale)
        updated_rent = self.update_table(Propertyrent)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_sale} Propertysale records."))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_rent} Propertyrent records."))
