from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Run all update and chart generation commands in order"

    def handle(self, *args, **kwargs):
        self.stdout.write("Running update_properties...")
        call_command("update_properties")

        self.stdout.write("Running update_yields...")
        call_command("update_yields")

        self.stdout.write("Running update_yields_plus...")
        call_command("update_yields_plus_new")

        self.stdout.write("Generating dashboard charts...")
        call_command("generate_dashboard_charts")

        self.stdout.write(self.style.SUCCESS("All update tasks completed successfully."))
