import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Cleans up the project by deleting the SQLite database, migration files, and __pycache__ directories."

    def handle(self, *args, **kwargs):
        # Path to the cleanup script
        cleanup_script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../../utils/lib/cleanup.py'
        )

        # Execute the cleanup script
        self.stdout.write("Running cleanup script...")
        exit_code = os.system(f"python {cleanup_script_path}")
        if exit_code == 0:
            self.stdout.write(self.style.SUCCESS("Cleanup completed successfully."))
        else:
            self.stdout.write(self.style.ERROR("Cleanup script failed."))