from nose import tools as test
from sample.models import Team
from django.core.exceptions import ValidationError
from django.utils import six


def test_key_value_field():
    from model_helpers import KeyValueContainer

    team = Team(name="Team1")
    test.assert_equal(team.options, {})
    team.options = "name = Ramast"
    test.assert_equal(team.options, {"name": "Ramast"})
    test.assert_equal(str(team.options), "name = Ramast\n")
    team.options = KeyValueContainer(Age=30)
    test.assert_equal(str(team.options), "Age = 30\n")
    # Notice int has been converted to string since we don't store value data type
    test.assert_equal(team.options, {"Age": "30"})
    team.options.update({"Name": "Ramast"})
    # Output should be
    #     Name = Ramast
    #     Age = 30
    # but since dictionary doesn't maintain order, I can't predict which one of the two lines will show first
    test.assert_in("Age = 30", str(team.options))
    test.assert_in("Name = Ramast", str(team.options))
    # Test invalid string
    try:
        team.options = "Name ?? Ramast"
        assert False, "Assigning invalid string should raise ValidationError"
    except ValidationError:
        pass


def test_custom_key_value_separator():
    team = Team(name="Team2")
    # Modify option field's separator pragmatically for this test case
    # Of course you should just define it in the model's field definition
    # options = KeyValueField(sep=":")
    options_field = filter(lambda field: field.name == "options", team._meta.fields)
    if six.PY3:
        options_field = next(options_field)
    else:
        options_field = options_field[0]
    options_field.separator = ":"
    # Test invalid string
    try:
        team.options = "Name = Ramast"
        assert False, "Assigning invalid string should raise ValidationError"
    except ValidationError:
        pass
    # Now use the new separator
    team.options = "Name : Ramast"
    test.assert_equal(team.options, {"Name": "Ramast"})
