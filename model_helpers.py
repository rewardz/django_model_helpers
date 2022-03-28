import types
import typing
from os import path as fs_path
from time import strftime
from collections import OrderedDict
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.conf import settings
from django.db import models

from django.utils.deconstruct import deconstructible

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


def cached_model_property(  # noqa: WPS212
    model_method=None, readonly=True, cache_timeout=None
):
    """
    cached_model_property is a decorator for model functions that takes no arguments
    The function is converted into a property that support caching out of the box

    :param readonly: set readonly parameter False to make the property writeable
    :type readonly: bool
    :param cache_timeout: number of seconds before cache expires
    :type cache_timeout: int

    Sample usage:

    class Team(models.Model):

        @cached_model_property
        def points(self):
            # Do complex DB queries
            return result

        @cached_model_property(readonly=False)
        def editable_points(self):
            # get result
            return result

    Now try
    team = Team.objects.first()
    team.points  <-- complex DB queries will happen, result will be returned
    team.points  <-- this time result is returned from cache (points function is not called at all!
    del team.points <-- points value has been removed from cache
    team.points  <-- complex DB queries will happen, result will be returned

    set readonly parameter False to make the property writeable
    team.editable_points = 88
    in this case the assigned value will replace the value stored in the cache
    team.editable_points
    returns 88
    """

    def func(original_func):
        def _get_cache_key(obj: "models.Model") -> str:
            model_name = obj._meta.db_table  # noqa: WPS437
            method_name = original_func.__name__
            return "{0}.{1}.{2}".format(model_name, obj.pk, method_name)

        def get_x(obj: "models.Model"):
            # Try to get the cache key for that method
            cache_key = _get_cache_key(obj)
            result = cache.get(cache_key)
            # If not cached, call the actual method and cache the result
            if result is None:
                result = original_func(obj)
                set_x(obj, result)
            return result

        def del_x(obj: "models.Model") -> None:
            """
            Remove that property from the cache
            """
            cache_key = _get_cache_key(obj)
            # Remove that key from the cache
            cache.delete(cache_key)

        def set_x(obj: "models.Model", value) -> None:
            """
            Set the cache value of that property
            """
            cache_key = _get_cache_key(obj)
            # Save that key in the cache
            if cache_timeout is None:
                cache.set(cache_key, value)
            else:
                cache.set(cache_key, value, cache_timeout)

        if readonly:
            return property(fget=get_x, fdel=del_x)
        return property(fget=get_x, fset=set_x, fdel=del_x)

    # model_method is passed when using @cached_model_property
    if model_method:
        return func(model_method)
    # model_method is not passed when using @cached_model_property(readonly=True) or even @cached_model_property()
    return func


# noinspection PyOldStyleClasses
class Choices(OrderedDict):
    """
    Offer a cleaner way for django choices field

    Usage:

    ** define a constant **
    ANIMAL_TYPES = Choices(
    [
        {"insect": 1,
        {"mammal": {"id": 2}, # same as {"mammal": 2}
        {"none": {"id": None, "display": "Not Animal"},
    ])

    ** Inside your model class **

    animal_type = models.IntegerField(choices=ANIMAL_TYPES(), null=True)

    output of ANIMAL_TYPES() is django choice list ordered by display name:
    [(1, 'Insect'), (2, 'Mammal'), (None, 'Not Animal')]

    ** Using the new model **
    animal = Animals.objects.first()
    if animal.animal_type == ANIMAL_TYPES.insect:
        # do the insect related code

    """

    # always True except during the execution of__init__() and update() methods
    _read_only = True
    # cache for mapping between choice id and choice dictionary (populated on demand)
    _choices_id = None

    def __init__(self, choices: typing.Iterable, order_by="display"):
        """

        :param choices: dictionary of dictionary . ex: {'choice1': {'id':1, 'display': 'Code One'}, ...}
        display key is optional. if not provided its assumed to be dict_key.replace("_", " ").capitalize()
        :type choices: Choices | OrderedDict | dict | tuple | list
        :param order_by: Whether generated Django choice list should be ordered (valid options "id", "display", None)
        :type  order_by: str | None
        """
        self._read_only = False

        # Initialize parent dict with the choices provided by the user
        super().__init__(choices)
        choices_list = []
        self._choices = choices_list
        self._order_by = order_by

        if not choices:
            return
        # choice_ids are used to validate an id is not used more than once
        choice_ids = set()

        for choice_code, choice_options in self.items():
            if not issubclass(choice_options.__class__, dict):
                # in case passing {"insect": 1} assume 1 is the id
                choice_options = {"id": choice_options}
                self[choice_code] = choice_options

            choice_id = choice_options["id"]
            choice_ids.add(choice_id)
            # End of validation
            if "display" not in choice_options:
                choice_options["display"] = choice_code.replace("_", " ").capitalize()
            display = choice_options["display"]
            choices_list.append((choice_id, _(display)))
        # Sort by display name
        if order_by == "display":
            choices_list.sort(key=lambda choice: choice[1])
        elif order_by == "id":
            choices_list.sort(key=lambda choice: choice[0])

        self._read_only = True

    def __call__(self):
        """
        :return: list of choices
        :rtype: list
        """
        return self._choices

    def get_display_name(self, choice_id):
        """
        Return translated display name of certain choice.
        same same model's get_<field_name>_display()
        :param choice_id: choice id
        :rtype: str
        """
        return self.get_value(choice_id, "display")

    def get_value(self, choice_id, choice_key, raise_exception=True):
        """
        Finds a choice with id <choice_id> and return value of key <key>

        :param choice_id: the db value of the choice in question
        :param choice_key: the key inside choice dictionary in which you want to get value of
        :param raise_exception: if True, KeyError exception will be raised if the key wasn't found
        :return: whatever stored in that choice key is returned,
                 if key not found and raise_exception=False then None is returned
        """
        if self._choices_id is None:
            self._choices_id = {item["id"]: (key, item) for key, item in self.items()}

        choice_name, choice = self._choices_id[choice_id]
        if choice_key is None:
            return choice_name
        if raise_exception:
            return choice[choice_key]
        return choice.get(choice_key)

    def get_code_name(self, choice_id):
        """
        Return code name of certain choice
        :param choice_id: choice id
        :rtype: str
        """
        return self.get_value(choice_id, choice_key=None)

    def copy(self):
        new_self = Choices({}, order_by=self._order_by)
        new_self.update(self)
        return new_self

    def update(self, new_data=None, **kwargs):
        """
        :type new_data: Choices | OrderedDict | dict | tuple | list
        """
        if self._read_only:
            raise TypeError("Choices are constants and can't be modified")

        if not new_data:
            new_data = kwargs

        if not isinstance(new_data, Choices):
            new_data = Choices(new_data)
        assert isinstance(new_data, Choices)

        common_keys = set(new_data.keys()) & set(self.keys())
        if common_keys:
            raise ValueError(
                "The following keys exist in both instances {keys}".format(
                    keys=", ".join(common_keys)
                )
            )

        self._choices += new_data()
        self._choices_id = None

        super().update(new_data)

    def __getattr__(self, attr_name):
        if attr_name in self:
            return self[attr_name]["id"]
        raise AttributeError(
            "Attribute {attr_name} is not part of {class_name} class".format(
                attr_name=attr_name, class_name=self.__class__.__name__
            )
        )

    def __setattr__(self, attr, *args):
        if self._read_only and attr in self:
            raise TypeError("Choices are constants and can't be modified")
        super().__setattr__(attr, *args)

    def __setitem__(self, *args):
        if self._read_only:
            raise TypeError("Choices are constants and can't be modified")
        super().__setitem__(*args)

    def __dir__(self):
        return list(self.keys()) + dir(self.__class__)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._read_only = True

    def __add__(self, other):
        self._read_only = False
        with self.copy() as result:
            result.update(other)
            self._read_only = True
            return result


class KeyValueContainer(dict):
    def __init__(self, seq=None, separator="=", **kwargs):
        super().__init__()
        self.sep = separator
        if isinstance(seq, str):
            seq = self._parse_string(seq)
        if seq is not None:
            seq = dict(seq)
            kwargs.update(seq)

        for key, value in kwargs.items():
            self.__setitem__(key, value)

    def __str__(self):
        result = []
        for key, val in self.items():
            result.append(" ".join((key, self.sep, val)))
        return "{0}\n".format("\n".join(result))

    def __setitem__(self, key, item):
        if item is None:
            item = ""
        else:
            item = str(item)
        super().__setitem__(key, item)

    def _parse_string(self, value):
        result = {}
        if not value:
            return result

        for line in value.split("\n"):
            line = line.strip()
            if not line:
                continue
            if self.sep not in line:
                raise ValueError(
                    _("Invalid syntax in line {0}\nExpected: key {1} value").format(
                        repr(line), self.sep
                    )
                )
            key, value = [val.strip() for val in line.split(self.sep, 1)]
            result[key] = value

        return result


class KeyValueField(models.TextField):
    """
    Basically a way to store configuration in DB and have it returned as dictionary.
    Simple key/value store
    data stored as
    key = value
    default separator is "=" but it can be customized

    sample usage

    class MyModel(models.Model):
         options = KeyValueField(separator=":")

    >> my_model.options = "key1 : val1 \n key2 : val2"
    >> my_model.clean_fields()
    >> my_model.options
    {"key1": "val1", "key2": "val2"}
    """

    description = _("Key/Value dictionary field")
    empty_values = (None,)

    def __init__(self, separator="=", *args, **kwargs):
        self.separator = separator
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):  # noqa: WPS117
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, name, property(fget=self.get_value, fset=self.set_value))

    def set_value(self, obj, value):
        if isinstance(value, str):
            value = self.from_db_value(value)
        elif not isinstance(value, KeyValueContainer):
            value = KeyValueContainer(value)
        obj.__dict__[self.name] = value

    def get_value(self, obj):
        return obj.__dict__[self.name]

    def from_db_value(self, value, *args, **kwargs):
        try:
            return KeyValueContainer(value, separator=self.separator)
        except ValueError as excp:
            raise ValidationError(excp)

    def get_prep_value(self, value):
        if value is None:
            return ""
        return str(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.separator != "=":
            kwargs["separator"] = self.separator
        return name, path, args, kwargs
