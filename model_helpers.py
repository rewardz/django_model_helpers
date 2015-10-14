from uuid import uuid4
from django.core.exceptions import ValidationError
import pytz
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.cache import cache
from django.conf import settings
from collections import OrderedDict


def upload_to(instance, filename):
    """
    This function passed as "upload_to" parameter for any FileField or ImageField
    It generates random file name and return it while keeping the original file extention
    each model get its own storage folder named after model's name

    :param instance:
    :param filename:
    :return: string
    """
    model_name = instance.__class__.__name__
    file_ext = filename.split(".")[-1]
    new_filename = "%s.%s" % (uuid4(), file_ext)
    return "/".join([model_name, new_filename])


def get_current_datetime():
    """
    This is a central function that return today's datetime
    A CURRENT_DATETIME can be defined in settings which will cause the function to return that datetime instead
    this is mainly useful for code test cases when current date needs to be well defined
    :rtype: datetime.datetime
    """
    return getattr(settings, "CURRENT_DATETIME", None) or timezone.now()


def cached_model_property(model_method=None, **kwargs):
    """
    cached_model_property is a decorator for model functions that takes no arguments
    The function is converted into a property that support caching out of the box
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

    readonly = kwargs.get("readonly", True)

    def func(f):
        def _get_cache_key(obj):
            """
            :type obj: django.db.models.Model
            :rtype: basestring
            """
            # getattr(obj, "_meta") is same as obj._meta but avoid the warning about accessing protected property
            model_name = getattr(obj, "_meta").db_table
            method_name = f.__name__
            return "%s.%s.%s" % (model_name, obj.pk, method_name)

        def get_x(obj):
            # Try to get the cache key for that method
            cache_key = _get_cache_key(obj)
            result = cache.get(cache_key)
            # If not cached, call the actual method and cache the result
            if result is None:
                result = f(obj)
                cache.set(cache_key, result)
            return result

        def del_x(obj):
            """
            Remove that property from the cache
            :param obj:
            :return: None
            """
            cache_key = _get_cache_key(obj)
            # Remove that key from the cache
            cache.delete(cache_key)

        def set_x(obj, value):
            """
            Set the cache value of that property
            :param obj:
            :return: None
            """
            cache_key = _get_cache_key(obj)
            # Remove that key from the cache
            cache.set(cache_key, value)

        if readonly:
            return property(fget=get_x, fdel=del_x)
        else:
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

    def __init__(self, choices, order_by="display"):
        """

        :param choices: dictionary of dictionary . ex: {'choice1': {'id':1, 'display': 'Code One'}, ...}
        display key is optional. if not provided its assumed to be dict_key.replace("_", " ").capitalize()
        :type choices: Choices | OrderedDict | dict | tuple | list
        :param order_by: Whether generated Django choice list should be ordered (valid options "id", "display", None)
        :type  order_by: str | None
        """
        self._read_only = False

        # Initialize parent dict with the choices provided by the user
        super(Choices, self).__init__(choices)
        _choices = []
        self._choices = OrderedDict()
        self._order_by = order_by

        if not choices:
            return
        # choice_ids are used to validate an id is not used more than once
        choice_ids = set()

        for choice_code, choice_options in self.items():
            if not issubclass(choice_options.__class__, dict):
                # in case passing {"insect": 1} assume 1 is the id
                choice_options = {"id": choice_options}

            choice_id = choice_options["id"]
            # Validation block
            if choice_id in choice_ids:
                raise ValueError("id %s already used" % choice_id)
            choice_ids.add(choice_id)
            # End of validation
            if "display" in choice_options:
                display = choice_options["display"]
            else:
                display = choice_code.replace("_", " ").capitalize()
            _choices.append((choice_id, ugettext_lazy(display)))
        # Sort by display name
        if order_by == "display":
            _choices.sort(key=lambda x: x[1])
        elif order_by == "id":
            _choices.sort(key=lambda x: x[0])

        self._choices = OrderedDict(_choices)
        self._read_only = True

    def get_display_name(self, choice_id):
        """
        Return translated display name of certain choice.
        same same model's get_<field_name>_display()
        :param choice_id: choice id
        :rtype: str
        """
        return self._choices[choice_id]

    def get_value(self, choice_id, key, raise_exception=True):
        """
        Finds a choice with id <choice_id> and return value of key <key>

        :param choice_id: the db value of the choice in question
        :param key: the key inside choice dictionary in which you want to get value of
        :param raise_exception: if True, KeyError exception will be raised if the key wasn't found
        :return: whatever stored in that choice key is returned,
                 if key not found and raise_exception=False then None is returned
        """
        id_cache = getattr(self.get_value, "id_cache", {})
        if len(id_cache) != len(self):  # if cache is not up to date
            id_cache = self.get_value.cache = {item["id"]: (key, item) for key, item in self.iteritems()}

        choice_name, choice = id_cache[choice_id]
        if key is None:
            return choice_name
        elif raise_exception:
            return choice[key]
        else:
            return choice.get(key)

    def get_code_name(self, choice_id):
        """
        Return code name of certain choice
        :param choice_id: choice id
        :rtype: str
        """
        return self.get_value(choice_id, key=None)

    def __getattr__(self, attr_name):
        if attr_name in self:
            value = self[attr_name]
            if isinstance(value, dict):
                return self[attr_name]["id"]
            return self[attr_name]
        raise AttributeError("Attribute %s is not part of %s class" % (attr_name, self.__class__.__name__))

    def __call__(self):
        """
        :return: list of choices
        :rtype: list
        """
        return self._choices.items()

    def __setattr__(self, attr, *args):
        if self._read_only and attr in self:
            raise TypeError("Choices are constants and can't be modified")
        super(Choices, self).__setattr__(attr, *args)

    def __setitem__(self, *args):
        if self._read_only:
            raise TypeError("Choices are constants and can't be modified")
        super(Choices, self).__setitem__(*args)

    def __delitem__(self, attr, *args):
        if self._read_only and attr in self:
            raise TypeError("Choices are constants and can't be modified")
        super(Choices, self).__delitem__(*args)

    def copy(self):
        new_self = Choices({}, order_by=self._order_by)
        new_self.update(self)
        return new_self

    def update(self, new_data=None, **kwargs):
        """
        :type new_data: Choices | OrderedDict | dict | tuple | list
        """

        if not new_data:
            new_data = kwargs
        elif new_data and kwargs:
            kwargs.update(new_data)
            new_data = kwargs

        if not isinstance(new_data, Choices):
            new_data = Choices(new_data)
        assert isinstance(new_data, Choices)

        common_keys = set(new_data.keys()) & set(self.keys())
        if common_keys:
            raise ValueError("The following keys exist in both instances %s" % ", ".join(common_keys))

        self._choices.update(new_data())

        super(Choices, self).update(new_data)

    def __add__(self, other):
        self._read_only = False
        result = self.copy()
        result.update(other)
        self._read_only = True
        return result
