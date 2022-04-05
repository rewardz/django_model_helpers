import typing
from django.utils.translation import gettext as _
from collections import OrderedDict


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
