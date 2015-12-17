from nose import tools
from datetime import date
import model_helpers

# Make the limit small for testing
model_helpers.UPLOAD_TO_MAX_FILENAME_LEN = 10


class FakeModel(object):
    pass


def test_upload_to():

    fake_instance = FakeModel()
    year = date.today().year
    tools.assert_equal(
        model_helpers.upload_to(fake_instance, "/tmp/filezx/myfile.png"),
        "FakeModel/%d/myfile.png" % year )
    tools.assert_equal(
        model_helpers.upload_to(fake_instance, "/tmp/filezx/1234567890123456.png"),
        "FakeModel/%d/1234567890.png" % year)
    tools.assert_raises(ValueError, model_helpers.upload_to, fake_instance, "/tmp/filezx/1234567890123456.php")
    tools.assert_raises(ValueError, model_helpers.upload_to, fake_instance, "/tmp/filezx/1234567890123456.pHp")
    tools.assert_raises(ValueError, model_helpers.upload_to, fake_instance, "/tmp/filezx/.pHp")
