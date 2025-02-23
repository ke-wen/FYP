from django.core.management.base import BaseCommand
from polls.models import Propertysale, Propertyrent

# 更新后的 Dublin & Greater Dublin Area 对应字典
eircode_to_city = {
    "A41": "Ballyboughal", "A42": "Garristown", "A45": "Oldtown",
    "A63": "Greystones", "A67": "Wicklow", "A75": "Castleblaney",
    "A81": "Carrickmacross", "A82": "Kells", "A83": "Enfield",
    "A84": "Ashbourne", "A85": "Dunshaughlin", "A86": "Dunboyne",
    "A91": "Dundalk", "A92": "Drogheda", "A94": "Blackrock",
    "A96": "Glenageary", "A98": "Bray", "C15": "Navan",
    "D01": "Dublin 1", "D02": "Dublin 2", "D03": "Dublin 3",
    "D04": "Dublin 4", "D05": "Dublin 5", "D06": "Dublin 6",
    "D07": "Dublin 7", "D08": "Dublin 8", "D09": "Dublin 9",
    "D10": "Dublin 10", "D11": "Dublin 11", "D12": "Dublin 12",
    "D13": "Dublin 13", "D14": "Dublin 14", "D15": "Dublin 15",
    "D16": "Dublin 16", "D17": "Dublin 17", "D18": "Dublin 18",
    "D20": "Dublin 20", "D22": "Dublin 22", "D24": "Dublin 24",
    "D6W": "Dublin 6W",
    "E21": "Cahir", "E25": "Cashel", "E32": "Carrick-on-Suir",
    "E34": "Tipperary", "E41": "Thurles", "E45": "Nenagh",
    "E53": "Roscrea", "E91": "Clonmel",
    "F12": "Claremorris", "F23": "Castlebar", "F26": "Ballina",
    "F28": "Westport", "F31": "Ballinrobe", "F35": "Ballyhaunis",
    "F42": "Roscommon", "F45": "Castlerea", "F52": "Boyle",
    "F56": "Ballymote", "F91": "Sligo", "F92": "Letterkenny",
    "F93": "Lifford", "F94": "Donegal",
    "H12": "Cavan", "H14": "Belturbet", "H16": "Cootehill",
    "H18": "Monaghan", "H23": "Clones", "H53": "Ballinasloe",
    "H54": "Tuam", "H62": "Loughrea", "H65": "Athenry",
    "H71": "Clifden", "H91": "Galway",
    "K32": "Balbriggan", "K34": "Skerries", "K36": "Malahide",
    "K45": "Lusk", "K56": "Rush", "K67": "Swords",
    "K78": "Lucan",
    "N37": "Athlone", "N39": "Longford", "N41": "Carrick-on-Shannon",
    "N91": "Mullingar",
    "P12": "Macroom", "P14": "Crookstown", "P17": "Kinsale",
    "P24": "Cobh", "P25": "Midleton", "P31": "Ballincollig",
    "P32": "Rylane", "P36": "Youghal", "P43": "Carrigaline",
    "P47": "Dunmanway", "P51": "Mallow", "P56": "Charleville",
    "P61": "Fermoy", "P67": "Mitchelstown", "P72": "Bandon",
    "P75": "Bantry", "P81": "Skibbereen", "P85": "Clonakilty",
    "R14": "Athy", "R21": "Mhuine Bheag", "R32": "Portlaoise",
    "R35": "Tullamore", "R42": "Birr", "R45": "Edenderry",
    "R51": "Kildare", "R56": "Curragh", "R93": "Carlow",
    "R95": "Kilkenny",
    "T12": "Cork Southside", "T23": "Cork Northside",
    "T34": "Carrignavar", "T45": "Glanmire",
    "T56": "Watergrasshill",
    "V14": "Shannon", "V15": "Kilrush", "V23": "Caherciveen",
    "V31": "Listowel", "V35": "Kilmallock", "V42": "Newcastle West",
    "V92": "Tralee", "V93": "Killarney", "V94": "Limerick",
    "V95": "Ennis",
    "W12": "Newbridge", "W23": "Celbridge", "W34": "Monasterevin",
    "W91": "Naas",
    "X35": "Dungarvan", "X42": "Kilmacthomas", "X91": "Waterford",
    "Y14": "Arklow", "Y21": "Enniscorthy", "Y25": "Gorey",
    "Y34": "New Ross", "Y35": "Wexford"
}
class Command(BaseCommand):
    help = "Force update area names in Propertysale and Propertyrent tables based on first 3 characters of ecode."

    def update_table(self, model):
        updated_count = 0
        for property in model.objects.all():
            if property.ecode and len(property.ecode) >= 3:  # 确保 ecode 存在且长度足够
                ecode_prefix = property.ecode[:3]  # 取前三位
            else:
                ecode_prefix = None  # 如果 ecode 不存在或长度不足 3

            # 确保 area 始终有值
            new_area = eircode_to_city.get(ecode_prefix, "Unknown") if ecode_prefix else "Unknown"

            if property.area != new_area:  # 只有在需要更新时才修改数据库，减少数据库写入
                property.area = new_area
                property.save()
                updated_count += 1

        return updated_count

    def handle(self, *args, **kwargs):
        updated_sale = self.update_table(Propertysale)
        updated_rent = self.update_table(Propertyrent)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_sale} Propertysale records."))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_rent} Propertyrent records."))
