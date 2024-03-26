from django.db import models
from model_helpers import cached_model_property, KeyValueField


class Team(models.Model):
    name = models.CharField(max_length=100)
    options = KeyValueField(
        default="",
        blank=True,
        help_text="Set options using key=value format. i.e. password=123",
    )
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
