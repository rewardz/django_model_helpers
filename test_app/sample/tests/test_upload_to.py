import pytest
from datetime import date
import model_helpers
from django.conf import settings

# Specify a filename template that make use of all capabilities of upload_to template
settings.UPLOAD_TO_OPTIONS = {
    "file_name_template": "{model_name}/%Y/{filename}-{instance.pk}.{extension}"
}


class FakeModel(object):
    pk = 1


def test_upload_to():

    fake_instance = FakeModel()
    upload_to = model_helpers.UploadTo(
        max_filename_length=10
    )  # get upload_to function with short filename
    year = date.today().year

    assert (
        upload_to(fake_instance, "/tmp/filezx/myfile.png")
        == f"FakeModel/{year}/myfile-1.png"
    )
    assert (
        upload_to(fake_instance, "/tmp/filezx/1234567890123456.png")
        == f"FakeModel/{year}/1234567890-1.png"
    )
    with pytest.raises(ValueError):
        upload_to(fake_instance, "/tmp/filezx/1234567890123456.php")
    with pytest.raises(ValueError):
        upload_to(fake_instance, "/tmp/filezx/1234567890123456.pHp")
    with pytest.raises(ValueError):
        upload_to(fake_instance, "/tmp/filezx/.pHp")
    # Validate model_helper's upload_to function (Shortcut for using UploadTo class)
    assert (
        model_helpers.upload_to(fake_instance, "/tmp/filezx/myfile.png")
        == f"FakeModel/{year}/myfile-1.png"
    )
