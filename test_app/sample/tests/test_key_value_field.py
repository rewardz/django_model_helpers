import pytest
from sample.models import Team
from django.core.exceptions import ValidationError


def test_key_value_field():

    team = Team(name="Team1")
    assert team.options == {}
    team.options = "name = Ramast"
    assert team.options == {"name": "Ramast"}
    assert str(team.options) == "name = Ramast\n"
    team.options = {"Age": 30}
    assert str(team.options) == "Age = 30\n"
    # Notice int has been converted to string since we don't store value data type
    assert team.options == {"Age": "30"}
    team.options.update({"Name": "Ramast"})
    # Output should be
    #     Name = Ramast
    #     Age = 30
    # but since dictionary doesn't maintain order, I can't predict which one of the two lines will show first
    assert "Age = 30" in str(team.options)
    assert "Name = Ramast" in str(team.options)
    # Test invalid string
    with pytest.raises(ValidationError):
        team.options = "Name ?? Ramast"


def test_custom_key_value_separator():
    team = Team(name="Team2")
    # Modify option field's separator pragmatically for this test case
    # Of course you should just define it in the model's field definition
    # options = KeyValueField(sep=":")
    options_field = filter(lambda field: field.name == "options", team._meta.fields)
    options_field = next(options_field)
    options_field.separator = ":"
    # Test invalid string
    with pytest.raises(ValidationError):
        team.options = "Name = Ramast"
    # Now use the new separator
    team.options = "Name : Ramast"
    assert team.options == {"Name": "Ramast"}
