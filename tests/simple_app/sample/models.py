from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from model_helpers import cached_model_property, KeyValueField, SimpleGenericForeignKey


class Team(models.Model):
    name = models.CharField(max_length=100)
    options = KeyValueField(default="", blank=True,
                            help_text="Set options using key=value format. i.e. password=123")
    counter = 0

    def get_counter(self):
        self.counter += 1
        return self.counter

    @cached_model_property
    def cached_counter(self):
        return self.get_counter()

    @cached_model_property(readonly=False)
    def writable_cached_counter(self):
        return self.get_counter()

    @cached_model_property(cache_timeout=1)
    def one_sec_cache(self):
        self.counter += 1
        return self.counter


class ModelX(models.Model):
    link = SimpleGenericForeignKey(null=True)


@SimpleGenericForeignKey.register_generic_model(index=1)
@python_2_unicode_compatible
class ModelA(models.Model):

    name_a = models.CharField(max_length=20)

    def __str__(self):
        return self.name_a


@SimpleGenericForeignKey.register_generic_model(index=2)
@python_2_unicode_compatible
class ModelB(models.Model):

    name_b = models.CharField(max_length=20)

    def __str__(self):
        return self.name_b
