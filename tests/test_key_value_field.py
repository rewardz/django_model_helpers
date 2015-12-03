from nose import tools as test
from sample.models import Team
from django.core.exceptions import ValidationError


def test_key_value_field():
    from model_helpers import KeyValueContainer

    team = Team(name="Team1")
    team.full_clean()
    team.save()
    test.assert_equal(team.options, {})
    team.options = "name = Ramast"
    team.full_clean()
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
    # but since dictionary doesn't maintain order, I can't predict which oe of the two lines will show first
    test.assert_in("Age = 30", str(team.options))
    test.assert_in("Name = Ramast", str(team.options))
    # Test invalid string
    team.options = "Name ?? Ramast"
    test.assert_raises(ValidationError, team.full_clean)


def test_custom_key_value_separator():
    team = Team(name="Team2")
    team.full_clean()
    team.save()
    # Modify option field's separator pragmatically for this test case
    # Of course you should just define it in the model
    # options = KeyValueField(sep=":")
    options_field = filter(lambda field: field.name == "options", team._meta.fields)[0]
    options_field.separator = ":"
    # Test invalid string
    team.options = "Name = Ramast"
    test.assert_raises(ValidationError, team.full_clean)
    # Now use the new separator
    team.options = "Name : Ramast"
    team.full_clean()
    test.assert_equal(team.options, {"Name": "Ramast"})
