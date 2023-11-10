import typing
from django.utils.translation import gettext as _
from collections import OrderedDict


class Choices:
    """
    Offer a cleaner way for django choices field
    Requires python 3.6 or higher
    Improvement over old Choices class:
    1. code completion in IDEs
    2. simpler syntax
    3. supports class inheritance

    Example usage:

    class FruitChoices(model_helpers.Choices2):
        BERRY = {"display": "strawberry", "value": 1, "extra_key": "extra_value"}
        BANANA = 2
        WATER_MELON = 3
        x = "unrelated attr" # this will be ignored because its not in upper case


    FRUITS = FruitChoices()

    # In Django models:
        fruit = models.IntegerField(choices=FRUITS()) # produces [(1, "BERRY"), (2, "BANANA"), (3, "WATER_MELON")]
    """
    _choices = None
    _choices_by_id = None

    def __getattribute__(self, item):
        attr_value = super().__getattribute__(item)
        if item.startswith("_"):
            return attr_value

        if item in self._choices:
            return attr_value["value"]
        return attr_value

    @classmethod
    def _get_all_attrs(cls, class_obj):
        if not class_obj:
            return tuple()

        return cls._get_all_attrs(class_obj.__base__) + tuple(class_obj.__dict__.items())

    def __init__(self, *args):
        if args:
            raise NotImplementedError("Choices class has been updated, please use the new syntax")
        self._choices = {}
        self._choices_by_id = {}
        for attr_name, attr_value in self._get_all_attrs(self.__class__):
            if not attr_name.isupper():
                continue
            attr_name: str
            if not isinstance(attr_value, dict):
                attr_value =  {"value": attr_value, "display": attr_name.replace("_", " ").capitalize()}

            attr_value["name"] = attr_name
            choice_value = attr_value["value"]
            self._choices[attr_name] = attr_value
            if choice_value in self._choices_by_id:
                raise ValueError(
                    "Duplicate choice value {choice_value} for {choice_name} and {choice_name2}".format(
                        choice_value=choice_value,
                        choice_name=attr_name,
                        choice_name2=self._choices_by_id[choice_value]["name"],
                    )
                )
            self._choices_by_id[choice_value] = attr_value

    def __call__(self):
        return [
            (choice_value["value"], choice_name)
            for choice_name, choice_value in self._choices.items()
        ]

    def get_choice(self, choice_id) -> dict:
        """
        Return translated display name of certain choice.
        same as model's get_<field_name>_display()
        :param choice_id: choice value as stored in Database
        """
        return self._choices_by_id[choice_id]

    def get_display_name(self, choice_id):
        """
        Return translated display name of certain choice.
        same as model's get_<field_name>_display()
        :param choice_id: choice value as stored in Database
        """
        return self.get_choice(choice_id)["display"]

    def get_choice_name(self, choice_id):
        """
        Returns name of certain choice given its database value.
        :param choice_id: choice value as stored in Database
        """
        return self.get_choice(choice_id)["name"]
