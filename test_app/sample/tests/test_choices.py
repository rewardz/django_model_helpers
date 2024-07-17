import pytest
import model_helpers

# Disable translation, We don't offer testing for translation functionality
model_helpers.ugettext_lazy = lambda text: text
model_helpers._ = lambda text: text


class FruitChoices(model_helpers.Choices):
    BERRY = {"display": "strawberry", "id": 1, "extra_key": "extra_value"}
    BANANA = 2
    WATER_MELON = {"id": 3}


FRUITS = FruitChoices()


def test_choices_output():
    assert FRUITS() == [
        (1, "BERRY"),
        (2, "BANANA"),
        (3, "WATER_MELON"),
    ]


def test_choices_functions():
    assert FRUITS.BERRY == 1
    assert FRUITS.get_choice(1) == {
        "display": "strawberry", "id": 1, "extra_key": "extra_value", 'name': 'BERRY'
    }
    assert FRUITS.get_choice(2) == {"display": "Banana", "id": 2, "name": "BANANA"}
    assert FRUITS.get_choice(3) == {"display": "Water melon", "id": 3, "name": "WATER_MELON"}

    assert FRUITS.get_display_name(3) == "Water melon"
    assert FRUITS.get_choice_name(3) == "WATER_MELON"


class FoodChoices(FruitChoices):
    Nothing = None
    RICE = 4
    BREAD = 5


FOOD = FoodChoices()


def test_concat_choices():
    assert FOOD() == [
        (1, "BERRY"),
        (2, "BANANA"),
        (3, "WATER_MELON"),
        (None, "Nothing"),
        (4, "RICE"),
        (5, "BREAD"),
    ]


class DuplicateFood(FoodChoices):
    CHEESE = 3


def test_errors():
    with pytest.raises(ValueError):
        # error because id 3 is used by both CHEESE and WATER_MELON from parent class
        DuplicateFood()
    with pytest.raises(NotImplementedError):
        # old implementation is not supported anymore
        model_helpers.Choices([{"display": "strawberry", "id": 1, "extra_key": "extra_value"}])
