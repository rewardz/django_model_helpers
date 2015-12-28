import os
import sys
import django
from django.core.management import call_command, CommandError

app_path = os.path.join(
    os.path.dirname(__file__),
    "simple_app"
)

sys.path.insert(0, app_path)
os.environ["DJANGO_SETTINGS_MODULE"] = "simple_app.settings"

django.setup()

try:
    call_command("syncdb", "--noinput")
except CommandError:
    # Django >= 1.9
    call_command("migrate", "--run-syncdb")

call_command("createcachetable")
