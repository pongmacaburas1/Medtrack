import os
from django.core.management.base import BaseCommand
from importlib.util import spec_from_file_location, module_from_spec
from django.db import connection

class Command(BaseCommand):
    help = "Run all initialization scripts in the utils/initialization folder"

    def handle(self, *args, **kwargs):
        initialization_folder = os.path.join(
            os.path.dirname(__file__), "../../../utils/initialization"
        )
        initialization_folder = os.path.abspath(initialization_folder)

        if not os.path.exists(initialization_folder):
            self.stdout.write(self.style.ERROR("Initialization folder not found."))
            return

        scripts = [
            f for f in os.listdir(initialization_folder)
            if f.endswith(".py") and not f.startswith("__")
        ]
        
        # Order scripts by filename to ensure consistent execution order
        scripts.sort()

        if not scripts:
            self.stdout.write(self.style.WARNING("No initialization scripts found."))
            return

        for script in scripts:
            script_path = os.path.join(initialization_folder, script)
            self.stdout.write(self.style.NOTICE(f"Running script: {script}"))

            try:
                spec = spec_from_file_location("module.name", script_path)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                connection.commit()
                self.stdout.write(self.style.SUCCESS(f"Successfully ran: {script}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error running {script}: {e}"))

        self.stdout.write(self.style.SUCCESS("All initialization scripts have been executed."))