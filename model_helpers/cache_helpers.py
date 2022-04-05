import typing
import functools
import json
import types
import inspect
from hashlib import sha256
from django.db import models
from django.core.cache import cache


class CachedFunction:
    def __init__(self, cache_timeout: int, key_parameters: typing.Iterable, key_class_attrs: typing.Iterable):
        """
        cache_timeout: number of seconds to store the cached value. default is determined by Django's `CACHE` settings.
        key_parameters: List of parameter names that need to match for the cache to be considered valid.
        key_class_attrs: List of attributes on the class that needs to match for the cache to be considered valid.
                         Useful only for instance methods or class methods otherwise it doesn't do anything.

        Example1:
            @CachedFunction(key_parameters=["a", "b"])
            def sum(a, b, log_output):
                return a + b

        >> sum(1, b=2, log_output=True)
        3  # sum function is called
        >> sum(1, b=2, log_output=False)  # log_output is not in key_parameters list so it won't be considered
        3  # sum function is NOT called. Cached version is returned instead.
        >> sum(2, b=2)
        4  # sum function is called.

        Example2:
            class A:
                b = 7
                @CachedFunction(key_parameters=["a"], key_class_attrs=["b"])
                def sum(self, a, log_output):
                    return a + self.b

        cache would remain valid so long as `self.b` and `a` variables are unchanged.
        """
        self.cache_timeout = cache_timeout
        self.key_parameters = key_parameters
        self.key_class_attrs = key_class_attrs

    def __call__(self, original_func):
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            cache_key = self.get_cache_key(original_func, *args, **kwargs)
            returned_value = cache.get(cache_key)
            if returned_value is None:
                returned_value = original_func(*args, **kwargs)
                self.cache_value(cache_key, returned_value)
            return returned_value
        return wrapper

    def cache_value(self, cache_key: str, value) -> None:
        """
        Set the cache value of that property
        """
        # Save that key in the cache
        if self.cache_timeout is None:
            cache.set(cache_key, value)
        else:
            cache.set(cache_key, value, self.cache_timeout)

    def get_cache_key(self, function: types.FunctionType, *args, **kwargs) -> str:
        func_arguments: dict = inspect.getcallargs(function, *args, **kwargs)
        if self.key_parameters:
            key_parameters = set(self.key_parameters)
        else:
            key_parameters = set(func_arguments.keys())

        args = {
            param: repr(param_value)
            for param, param_value in func_arguments.items()
            if param in key_parameters
        }

        if "self" in func_arguments or "cls" in func_arguments:
            assert self.key_class_attrs is not None, (
                "Your method is part of a class so, you need to specify which class attributes affect the output. "
                "If output is not affected by class attributes, consider using @staticmethod decorator"
            )
            try:
                class_obj = func_arguments["self"]
            except KeyError:
                class_obj = func_arguments["cls"]
            for class_attr in self.key_class_attrs:
                args["class.{0}".format(class_attr)] = repr(getattr(class_obj, class_attr))

            args.pop("cls", None)
            args.pop("self", None)

        func_signature = {
            "name": function.__qualname__,
            "module": function.__module__,
            "args": args,
        }
        return sha256(json.dumps(func_signature).encode("ascii")).hexdigest()


def cached_function(
    original_func=None, *, cache_timeout=None, key_parameters=None, key_class_attrs=None,
):
    cached_func_instance = CachedFunction(cache_timeout, key_parameters, key_class_attrs)
    if original_func:
        return cached_func_instance(original_func)
    return cached_func_instance


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
        cached_func_instance = CachedFunction(cache_timeout, key_class_attrs=["pk"], key_parameters=None)

        def get_x(obj: "models.Model"):
            return cached_func_instance(original_func)(obj)

        def del_x(obj: "models.Model") -> None:
            """
            Remove that property from the cache
            """
            cache_key = cached_func_instance.get_cache_key(original_func, obj)
            # Remove that key from the cache
            cache.delete(cache_key)

        def set_x(obj: "models.Model", value) -> None:
            """
            Set the cache value of that property
            """
            cache_key = cached_func_instance.get_cache_key(original_func, obj)
            cached_func_instance.cache_value(cache_key, value)

        if readonly:
            return property(fget=get_x, fdel=del_x)
        return property(fget=get_x, fset=set_x, fdel=del_x)

    # model_method is passed when using @cached_model_property
    if model_method:
        return func(model_method)
    # model_method is not passed when using @cached_model_property(readonly=True) or even @cached_model_property()
    return func
