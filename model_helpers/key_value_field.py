from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db import models


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
