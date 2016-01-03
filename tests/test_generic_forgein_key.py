import django
from nose import tools
from django.core.exceptions import ValidationError
from sample.models import ModelX, ModelA, ModelB


def test_generic_foreign_key():
    DJANGO_VERSION = (django.VERSION[0] * 10 + django.VERSION[1]) / 10

    instance_a = ModelA.objects.create(name_a="I am model A", id=1)
    instance_b = ModelB.objects.create(name_b="I am model B", id=1)
    ModelX.objects.create(link=instance_a)
    ModelX.objects.create(link=instance_b)
    ModelX.objects.create(link=None)
    ModelX.objects.create(link=None)

    items = [str(obj.link) for obj in ModelX.objects.order_by("pk").all()]
    tools.assert_list_equal(["I am model A", "I am model B", "None", "None"], items)

    # Filter by instance
    tools.assert_equal(ModelX.objects.get(link=instance_b).link, instance_b)
    tools.assert_equal(ModelX.objects.get(link=instance_a).link, instance_a)
    # Filter by Model/instance id tuple without getting actual instance
    tools.assert_equal(ModelX.objects.get(link=(ModelA, 1)).link, instance_a)
    tools.assert_equal(ModelX.objects.get(link=(ModelB, 1)).link, instance_b)
    # Filter by Model name/ instance id tuple
    tools.assert_equal(ModelX.objects.get(link=("ModelA", 1)).link, instance_a)
    tools.assert_equal(ModelX.objects.get(link=("modelb", 1)).link, instance_b)
    # Filter by null should behave normally
    tools.assert_equal(ModelX.objects.filter(link__isnull=True)[0].link, None)
    tools.assert_equal(ModelX.objects.filter(link__isnull=True).count(), 2)
    # Validation error when using unregistered model
    with tools.assert_raises(ValidationError):
        ModelX.objects.get(link=ModelX.objects.all()[0])

    if DJANGO_VERSION >= 1.7:
        # Filter by class (Warning: DB index is not used)
        tools.assert_equal(ModelX.objects.get(link__class=ModelA).link, instance_a)
        tools.assert_equal(ModelX.objects.get(link__class="ModelA").link, instance_a)

        with tools.assert_raises(ValidationError):
            ModelX.objects.get(link__class=ModelX)
