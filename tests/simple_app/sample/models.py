from django.db import models
from common_app.model_helpers import cached_model_property


class Team(models.Model):
    name = models.CharField(max_length=100)
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
