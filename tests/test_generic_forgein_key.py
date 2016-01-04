import django
from nose import tools
from django.core.exceptions import ValidationError
from sample.models import ModelX, ModelA, ModelB
from model_helpers import SimpleGenericForeignKey


def test_generic_foreign_key():
    DJANGO_VERSION = (django.VERSION[0] * 10 + django.VERSION[1]) / 10.0

    instance_a = ModelA.objects.create(name_a="I am model A", id=1)
    instance_b = ModelB.objects.create(name_b="I am model B", id=1)
    ModelX.objects.create(link=instance_a)
    ModelX.objects.create(link=instance_b)
    ModelX.objects.create(link=None)
    ModelX.objects.create(link=None)
    instance_x = ModelX.objects.all()[0]

    # Accepted forms of assignment
    ModelX(link=instance_a)
    ModelX(link=(ModelA, 1))
    ModelX(link=("ModelA", "1"))
    ModelX(link=257)  # <-- for internal use only
    # Validation error when putting invalid data
    with tools.assert_raises(ValidationError):
        ModelX(link="None Sense")
    with tools.assert_raises(SimpleGenericForeignKey.NotRegistered):
        ModelX(link=("None Sense", 1))
    with tools.assert_raises(SimpleGenericForeignKey.NotRegistered):
        ModelX(link=(ModelX, 1))
    with tools.assert_raises(SimpleGenericForeignKey.NotRegistered):
        ModelX(link=instance_x)

    items = [str(obj.link__obj) for obj in ModelX.objects.order_by("pk").all()]
    tools.assert_list_equal(["I am model A", "I am model B", "None", "None"], items)

    # the reason I call full_clean is convert instance b's id to int, otherwise assert_equal will fail
    instance_b.full_clean()
    # Filter by instance
    tools.assert_equal(ModelX.objects.get(link=instance_b).link__obj, instance_b)
    tools.assert_equal(ModelX.objects.get(link=instance_a).link__obj, instance_a)
    # Filter by Model/instance id tuple without getting actual instance
    tools.assert_equal(ModelX.objects.get(link=(ModelA, 1)).link__obj, instance_a)
    tools.assert_equal(ModelX.objects.get(link=(ModelB, 1)).link__obj, instance_b)
    # Filter by Model name/ instance id tuple
    tools.assert_equal(ModelX.objects.get(link=("ModelA", 1)).link__obj, instance_a)
    tools.assert_equal(ModelX.objects.get(link=("ModelB", "1")).link__obj, instance_b)
    # Filter by String
    tools.assert_equal(ModelX.objects.get(link="ModelA+1").link__obj, instance_a)
    tools.assert_equal(ModelX.objects.get(link="ModelB+1").link__obj, instance_b)
    # Filter by null should behave normally
    tools.assert_equal(ModelX.objects.filter(link__isnull=True)[0].link__obj, None)
    tools.assert_equal(ModelX.objects.filter(link__isnull=True).count(), 2)
    # Validation error when using unregistered model
    with tools.assert_raises(SimpleGenericForeignKey.NotRegistered):
        ModelX.objects.get(link=instance_x)

    if DJANGO_VERSION >= 1.7:
        # Filter by class (Warning: DB index is not used)
        tools.assert_equal(ModelX.objects.get(link__class=ModelA).link__obj, instance_a)
        tools.assert_equal(ModelX.objects.get(link__class="ModelA").link__obj, instance_a)
        # Filter by class's defined index
        tools.assert_equal(ModelX.objects.get(link__class=1).link__obj, instance_a)

        with tools.assert_raises(SimpleGenericForeignKey.NotRegistered):
            ModelX.objects.get(link__class=ModelX)

    # get info about certain foreign key
    inst_x = ModelX.objects.get(link=instance_a)
    assert isinstance(inst_x.link, int), "ForeignKey value must be int"
    tools.assert_equal(inst_x.link__obj, instance_a)
    tools.assert_equal(inst_x.link__class, ModelA)
    # Null should be properly handled
    inst_x = ModelX.objects.filter(link=None)[0]
    tools.assert_is_none(inst_x.link)
    tools.assert_is_none(inst_x.link__obj)
    tools.assert_is_none(inst_x.link__class)

    # Can't register two classes with same index
    with tools.assert_raises(AssertionError):
        SimpleGenericForeignKey.register_generic_model(1)(ModelX)

    # Don't retrieve related object from DB until its accessed
    dead_inst = ModelA.objects.create(name_a="Dead object")
    dead_rel = ModelX.objects.create(link=dead_inst)
    ModelA.objects.filter(pk=dead_inst.pk).delete()

    # Don't try to retrieve the instance again if nothing has changed
    tools.assert_equal(dead_rel.link__obj, dead_inst)
    # These lines shouldn't crash because it shouldn't do DB queries
    dead_rel.full_clean()
    dead_rel.save()
    dead_rel = ModelX.objects.get(link=dead_inst)
    dead_rel.full_clean()
    dead_rel.save()
    if DJANGO_VERSION >= 1.7:
        ModelX.objects.filter(link__class=ModelA).order_by("pk").last()
    dead_rel.link = (ModelA, dead_inst.pk)
    dead_rel.save()

    tools.assert_equal(dead_rel.link__class, ModelA)
    # Only this should fail
    with tools.assert_raises(ModelA.DoesNotExist):
        bool(dead_rel.link__obj)
