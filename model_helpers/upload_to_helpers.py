import types
from os import path as fs_path
from time import strftime
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.conf import settings


UPLOAD_TO_OPTIONS = types.MappingProxyType(
    {
        "black_listed_extensions": [
            "php",
            "html",
            "htm",
            "js",
            "vbs",
            "py",
            "pyc",
            "asp",
            "aspx",
            "pl",
        ],
        "max_filename_length": 40,
        "file_name_template": "{model_name}/%Y/{filename}.{extension}",
    }
)


@deconstructible
class UploadTo:
    """
    An instance of this class is passed as "upload_to" parameter for any FileField or ImageField
    It ensures file name is less than "max_filename_length" char also slugify the filename and finally provide simple
    protection against uploading some harmful files like (php or python files)

    File is saved in a folder called <model_name>/<current_year>/file_name.ext
    example: User/2015/profile_pic.jpg
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: You can override any of the default options by passing it as keyword argument to this function
        :return:
        """
        self.options = UPLOAD_TO_OPTIONS.copy()
        if hasattr(settings, "UPLOAD_TO_OPTIONS"):
            self.options.update(settings.UPLOAD_TO_OPTIONS)
        self.options.update(kwargs)

    def __call__(self, instance, full_filename):
        """
        :param instance: model instance which the file is uploaded for
        :param full_filename: filename including its path
        :return: string
        """
        file_info = self.get_file_info(full_filename)
        self.validate_file_info(file_info)
        return self.generate_file_name(instance, file_info)

    @staticmethod
    def get_file_info(full_filename):
        filename = fs_path.basename(full_filename).lower()
        filename, file_ext = filename.rsplit(".", 1)
        return {
            "filename": filename,
            "extension": file_ext,
            "full_filename": full_filename,
        }

    def validate_file_info(self, file_info):
        file_ext = file_info["extension"]
        if file_ext in self.options["black_listed_extensions"]:
            raise ValueError("File extension '{0}' is not allowed".format(file_ext))

    def generate_file_name(self, instance, file_info):
        model_name = instance.__class__.__name__
        filename = file_info["filename"]
        max_len = self.options["max_filename_length"]
        file_info["filename"] = slugify(filename)[:max_len]

        return strftime(self.options["file_name_template"]).format(
            model_name=model_name,
            instance=instance,
            **file_info,
        )


# Shortcut for UploadTo class
def upload_to(instance, full_filename):
    upload_to_obj = UploadTo()
    return upload_to_obj(instance, full_filename)
