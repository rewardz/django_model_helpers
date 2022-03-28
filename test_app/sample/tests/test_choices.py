import pytest
import model_helpers

# Disable translation, We don't offer testing for translation functionality
model_helpers.ugettext_lazy = lambda x: x
model_helpers._ = lambda x: x


def test_choices_output():
    choices = model_helpers.Choices({
        "choice1": 1,
        "choice2": {"id": 2},
        "choice__xx": {"id": 3, "display": "Choice_XX"},
        "choice3": {"id": 3, "display": "Choice_3"}
    })
    assert choices() == [
        (1, "Choice1"),
        (2, "Choice2"),
        (3, "Choice_3"),
        (3, "Choice_XX")
    ]


def test_choices_order():
    # Order by "display"  (default)
    choices = model_helpers.Choices([
        ("choice1", 1),
        ("choice2", {"id": 2}),
        ("choice3", {"id": 3, "display": "A_Choice_3"}),
    ])
    assert choices() == [
        (3, "A_Choice_3"),
        (1, "Choice1"),
        (2, "Choice2")]
    # Order by "id"
    choices = model_helpers.Choices([
        ("choice1", 1),
        ("choice3", {"id": 3, "display": "A_Choice_3"}),
        ("choice2", {"id": 2}),
    ], order_by="id")
    assert choices() == [
        (1, "Choice1"),
        (2, "Choice2"),
        (3, "A_Choice_3")]
    # Disable ordering
    choices = model_helpers.Choices([
        ("choice1", 1),
        ("choice3", {"id": 3, "display": "A_Choice_3"}),
        ("choice2", {"id": 2}),
    ], order_by=None)
    assert choices() == [
        (1, "Choice1"),
        (3, "A_Choice_3"),
        (2, "Choice2")]


def test_choices_functions():
    # When an id is repeated, the last value is assumed
    choices = model_helpers.Choices([
        ("choice1", 1),
        ("choice_xx", {"id": 3, "display": "xxx"}),
        ("choice2", {"id": 2, "extra_key": "extra_value"}),
        ("choice3", {"id": 3, "display": "A_Choice_3"}),
    ], order_by=None)

    assert choices["choice1"] == {"id": 1, "display": "Choice1"}
    assert choices["choice2"] == {"id": 2, "display": "Choice2", "extra_key": "extra_value"}
    assert choices["choice3"] == {"id": 3, "display": "A_Choice_3"}

    assert choices.choice1 == 1
    assert choices.choice2 == 2
    assert choices.choice3 == 3

    assert choices.get_display_name(1) == "Choice1"
    assert choices.get_display_name(2) == "Choice2"
    assert choices.get_display_name(3) == "A_Choice_3"

    assert choices.get_code_name(1) == "choice1"
    assert choices.get_code_name(2) == "choice2"
    assert choices.get_code_name(3) == "choice3"

    assert choices.get_value(2, "extra_key") == "extra_value"
    with pytest.raises(KeyError):
        choices.get_value(choice_id=1, choice_key="extra_key")
    assert choices.get_value(1, "extra_key", raise_exception=False) is None


def test_concat_choices():

    choices1 = model_helpers.Choices({"X": 1, "Y": 2})
    choices2 = choices1 + model_helpers.Choices({}) + {"B": 4, "A": 5}
    # Items of each list are ordered by when concatenated they are not re-ordered
    # items of first list will appear first then items of second list
    assert choices2() == [
        (1, "X"),
        (2, "Y"),
        (5, "A"),
        (4, "B")
    ]

    # Duplicate key
    with pytest.raises(ValueError):
        choices1.__add__({"X": 7})


def test_errors():
    choices1 = model_helpers.Choices({"X": 1, "Y": 2})
    with pytest.raises(TypeError):
        choices1.X = 7
    with pytest.raises(TypeError):
        setattr(choices1, "X", 7)
    with pytest.raises(TypeError):
        assert choices1.update({"X": 7})


def test_dir_method():
    choices1 = model_helpers.Choices({"X": 1, "Y": 2})
    assert "X" in dir(choices1)
    assert "Y" in dir(choices1)
    # parent attributes should also be mentioned
    assert "items" in dir(choices1)
