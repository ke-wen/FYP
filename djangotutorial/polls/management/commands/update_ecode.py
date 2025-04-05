from django.core.management.base import BaseCommand
from polls.models import Propertysale, Propertyrent


class Command(BaseCommand):
    help = "Fix ecode fields to ensure only first 3 characters are stored."

    def handle(self, *args, **options):
        def fix_ecode(model):
            updated = 0
            for obj in model.objects.all():
                if obj.ecode and len(obj.ecode) > 3:
                    new_ecode = obj.ecode[:3].upper().strip()
                    if new_ecode != obj.ecode:
                        obj.ecode = new_ecode
                        obj.save(update_fields=['ecode'])
                        updated += 1
            return updated

        updated_sales = fix_ecode(Propertysale)
        updated_rents = fix_ecode(Propertyrent)

        self.stdout.write(self.style.SUCCESS(f"✅ Updated {updated_sales} Propertysale records."))
        self.stdout.write(self.style.SUCCESS(f"✅ Updated {updated_rents} Propertyrent records."))
