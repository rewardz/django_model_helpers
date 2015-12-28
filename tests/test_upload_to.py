from nose import tools
from datetime import date
import model_helpers
from django.conf import settings

# Specify a filename template that make use of all capabilities of upload_to template
settings.UPLOAD_TO_OPTIONS = {"file_name_template": "{model_name}/%Y/{filename}-{instance.pk}.{extension}"}


class FakeModel(object):
    pk = 1


def test_upload_to():

    fake_instance = FakeModel()
    upload_to = model_helpers.UploadTo(max_filename_length=10)  # get upload_to function with short filename
    year = date.today().year

    tools.assert_equal(
        upload_to(fake_instance, "/tmp/filezx/myfile.png"),
        "FakeModel/%d/myfile-1.png" % year)
    tools.assert_equal(
        upload_to(fake_instance, "/tmp/filezx/1234567890123456.png"),
        "FakeModel/%d/1234567890-1.png" % year)
    tools.assert_raises(ValueError, upload_to, fake_instance, "/tmp/filezx/1234567890123456.php")
    tools.assert_raises(ValueError, upload_to, fake_instance, "/tmp/filezx/1234567890123456.pHp")
    tools.assert_raises(ValueError, upload_to, fake_instance, "/tmp/filezx/.pHp")
    # Validate model_helper's upload_to function (Shortcut for using UploadTo class)
    tools.assert_equal(
        model_helpers.upload_to(fake_instance, "/tmp/filezx/myfile.png"),
        "FakeModel/%d/myfile-1.png" % year)
