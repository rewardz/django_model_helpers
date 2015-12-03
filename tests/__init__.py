import os
import sys
import django
from django.core.management import call_command


app_path = os.path.join(
    os.path.dirname(__file__),
    "simple_app"
)

sys.path.insert(0, app_path)
os.environ["DJANGO_SETTINGS_MODULE"] = "simple_app.settings"

django.setup()

call_command("migrate")
call_command("createcachetable")
