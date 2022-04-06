import pytest
from model_helpers.cache_helpers import cached_function


class ExampleClass:

    func1_call_counter = 0
    func2_call_counter = 0
    func3_call_counter = 0
    example_field = "a"

    @staticmethod
    @cached_function
    def cached_func1(arg_a, arg_b):
        ExampleClass.func1_call_counter += 1
        return arg_a + arg_b

    @cached_function(cache_timeout=1, key_parameters=["arg_a", "arg_b"], key_class_attrs=["example_field"])
    def cached_func2(self, arg_a, arg_b, print_status=True):
        self.func2_call_counter += 1
        if print_status:
            print("Function is executed")
        return arg_a + arg_b

    @classmethod
    @cached_function(key_class_attrs=["example_field"])
    def cached_func3(cls, arg_a, arg_b):
        cls.func3_call_counter += 1
        return arg_a + arg_b


@pytest.mark.django_db(transaction=True)
def test_cached_function():
    example_instance = ExampleClass()

    # ### Test class static method ####
    assert example_instance.func1_call_counter == 0
    # First call, not cached and function is executed
    assert example_instance.cached_func1(1, 1) == 2
    assert example_instance.func1_call_counter == 1
    # Second call, cached and call_counter doesn't increase
    assert example_instance.cached_func1(1, 1) == 2
    assert example_instance.func1_call_counter == 1
    # 3ed call with different parameters isn't cached
    assert example_instance.cached_func1(2, 1) == 3
    assert example_instance.func1_call_counter == 2
    # Calling with original parameters (1, 1) should still be cached
    assert example_instance.cached_func1(1, 1) == 2
    assert example_instance.func1_call_counter == 2

    # ### Test class instance method ####
    assert example_instance.func2_call_counter == 0
    # First call, not cached and function is executed
    assert example_instance.cached_func2(1, 1) == 2
    assert example_instance.func2_call_counter == 1
    # Second call cached and call_counter doesn't increase
    assert example_instance.cached_func2(1, 1) == 2
    assert example_instance.func2_call_counter == 1
    # 3ed call not cached because parameters changed
    assert example_instance.cached_func2(1, 2) == 3
    assert example_instance.func2_call_counter == 2
    # Changing class attribute invalidates the cache
    example_instance.example_field = "test"
    assert example_instance.cached_func2(1, 1) == 2
    assert example_instance.func2_call_counter == 3

    # ### Test class method ####
    assert ExampleClass.func3_call_counter == 0
    # First call, not cached and function is executed
    assert ExampleClass.cached_func3(1, 1) == 2
    assert ExampleClass.func3_call_counter == 1
    # Second call, cached and call_counter doesn't increase
    assert ExampleClass.cached_func3(1, 1) == 2
    assert ExampleClass.func3_call_counter == 1
    # 3ed call with different parameters isn't cached
    assert ExampleClass.cached_func3(2, 1) == 3
    assert ExampleClass.func3_call_counter == 2
    # Calling with original parameters (1, 1) should still be cached
    assert ExampleClass.cached_func3(1, 1) == 2
    assert ExampleClass.func3_call_counter == 2

    # #### Test with different data types cases ####
    example_instance.func2_call_counter = 0
    assert example_instance.cached_func2((1, 2), (3, 4)) == (1, 2, 3, 4)
    assert example_instance.func2_call_counter == 1
    assert example_instance.cached_func2((1, 2), (3, 4)) == (1, 2, 3, 4)
    assert example_instance.func2_call_counter == 1
