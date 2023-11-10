**Model helpers** are small collection of django functions and classes that make working with models easier.
All functions here are compliant with pylint and has test cases with over 95% code coverage.
This doc describe each of these helpers.

upload_to_
  Pass this function to your `FileField` as `upload_to` argument

cached_model_property_
  Decorate a model function with that decorator to turn it into a property that caches the result.

cached_function_
  Decorate any function or class method with that decorator to enable out of the box caching.

Choices_
  A feature rich solution for implementing choice field

KeyValueField_
  A field that can store multiple key/value entries in a human readable form

.. _upload_to:

**model\_helpers.upload\_to**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass ``model_helpers.upload_to`` as ``upload_to`` parameter for any FileField or ImageField. This will - by default - generate slugified version of the file name. By default each model get its own storage folder named after model's name.

``upload_to`` function also block files with certain harmful extensions like "php" or "py" from being uploaded.

**Sample usage:**

::

    import model_helpers

    class Profile(models.model):
        name = CharField(max_length=100)
        picture = ImageField(upload_to=model_helpers.upload_to)

uploaded images for this model will be stored in: ``media/Profile/<current_year>/<slugified_original_filename>``.

**settings**

settings for ``upload_to`` function should be placed in ``UPLOAD_TO_OPTIONS`` inside your *settings.py* file These are the default settings

::

    settings.UPLOAD_TO_OPTIONS = {
        "black_listed_extensions": ["php", "html", "htm", "js", "vbs", "py", "pyc", "asp", "aspx", "pl"],
        "max_filename_length": 40,
        "file_name_template": "{model_name}/%Y/{filename}.{extension}"
    }

-  ``black_listed_extensions`` prevent any file with any of these extensions from being saved.
-  ``max_filename_length`` trim filename if it exceeds certain length to mitigate DB errors when user upload long filename
-  ``file_name_template`` controls where the file should be saved.

**specifying ``file_name_template``**

``file_name_template`` pass your string to strftime() function; ``'%Y'`` in the example above is the four-digit year. other accepted variables are:

-  ``model_name``: name of the model which the file is being uploaded for.
-  ``filename``: name of the file - without extension - after it has been processed by ``upload_to`` (trimmed and slugified)
-  ``extension``: file's extension
-  ``instance``: the model instance passed to ``upload_to`` function

For example to save uploaded files to a directory like this

::

      model name/current year/current month/instance's name(dot)file's extension

you do

::

      UPLOAD_TO_OPTIONS = {"file_name_template": "{model_name}/%Y/%m/{instance.name}.{extension}" }

**customizing ``upload_to`` per model**

If you want to have different ``upload_to`` options for different models, use ``UploadTo`` class instead. For example to have ``ImageField`` that allow all file extensions, You can do this:

::

    my_image = models.ImageField(upload_to=models_helper.UploadTo(black_listed_extensions=[])

``UploadTo`` class accepts all ``upload_to`` settings documented above. You can also inherit from this class if you want to have very custom file naming schema (like if you want file name be based on its md5sum)

.. _cached_model_property:

cached_model_property decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``cached_model_property`` is a decorator for model functions that takes no arguments. The decorator convert the function into a property that support caching out of the box

**Note**: ``cached_model_property`` is totally different from django's ``cached_property`` the later is not true caching but rather memorizing function's return value.
``cache_timeout``: number of seconds before cache expires.

**Sample usage:**

::

    class Team(models.Model):
        @cached_model_property
        def points(self):
            # Do complex DB queries
            return result

        @cached_model_property(readonly=False)
        def editable_points(self):
            # get result
            return result

        @cached_model_property(cache_timeout=1)
        def one_second_cache(self):
            # get result
            return result

Now try

::

    team = Team.objects.first()

-  ``team.points`` <-- complex DB queries will happen, result will be returned
-  ``team.points`` <-- this time result is returned from cache (points function is not called
-  ``del team.points`` <-- points value has been removed from cache
-  ``team.points`` <-- complex DB queries will happen, result will be returned

**How does it work?**: first time the decorator store the function output in the cache with ``key = "<model_class>_<instance.pk>_<function_name>"`` so if you have two models with same name, or have model that provide no primary key you can't use this decorator.

set ``readonly`` parameter to ``False`` to make the property writeable

``team.editable_points = 88``

In this case the assigned value will replace the value stored in the cache

``team.editable_points`` returns 88

I personally don't use the writable cached property option but might be useful to someone else

.. _cached_function:

cached_function decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``cached_function`` is a decorator for any functions.
The decorator automatically cache function's result for a defined amount of time.
The caching takes into account function arguments and *- for class methods -* class properties.

``cache_timeout``: number of seconds before cache expires.
``key_parameters``: Function parameters which the cached value depends on
``key_class_attrs``: Class attributes which the cached value depends on

**Sample Usage:**

::

    class ExampleClass:

        example_field = 0

        @cached_function(cache_timeout=1, key_parameters=["arg_a", "arg_b"], key_class_attrs=["example_field"])
        def example_function(self, arg_a, arg_b, print_result=False):
            if print_result:
                print("Result is ", arg_a + arg_b)
            return arg_a + arg_b

This output from ``example_function`` will be cached for exactly `1` second.
The cache would depend on value of function's ``arg_a`` and ``arg_b`` parameters and class's ``example_field`` value.

.. _Choices:

Choices class (version 2.0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dealing with Django's ``choices`` attribute is a pain. Here is a proper way of implementing choice field in Django

::

    class Student(models.Model):
        FRESHMAN = 'FR'
        SOPHOMORE = 'SO'
        JUNIOR = 'JR'
        SENIOR = 'SR'
        YEAR_IN_SCHOOL_CHOICES = (
            (FRESHMAN, 'Freshman'),
            (SOPHOMORE, 'Sophomore'),
            (JUNIOR, 'Junior'),
            (SENIOR, 'Senior'),
        )
        year_in_school = models.CharField(
                            max_length=2,
                            choices=YEAR_IN_SCHOOL_CHOICES,
                            default=FRESHMAN)

Then you can do

::

    student = Student.objects.first()
    if student.year_in_school == Student.SENIOR:
          # do some senior stuff

With Choices class this becomes

::

    class SchoolYearChoices(Choices):
        # attributes must be uppercase or it will be ignoredS
        FRESHMAN = 'FR'
        SOPHOMORE = 'SO'
        JUNIOR = 'JR'
        SENIOR = 'SR'

    YEAR_IN_SCHOOL_CHOICES = SchoolYearChoices()


    class Student(models.Model):
        year_in_school = models.CharField(
                            max_length=2,
                            choices=YEAR_IN_SCHOOL_CHOICES(),
                            default=YEAR_IN_SCHOOL_CHOICES.FRESHMAN)

Then you can do

::

    student = Student.objects.first()
    if student.year_in_school == YEAR_IN_SCHOOL_CHOICES.SENIOR:
          # do some senior stuff


``Choices`` class is more flexible because it allow you to specify 3 values (or more!).
The standard ones are:

- choice attribute name (must be uppercase)
- choice db value (aka choice_id)
- choice display name.

The example above can be better written like that

::

    class SchoolYearChoices(Choices):
         FRESHMAN: {"id": 0, "display": "New comer"},
         SOPHOMORE: 1,
         JUNIOR: 2,
         SENIOR: 3

     YEAR_IN_SCHOOL_CHOICES = SchoolYearChoices()


    class Student(models.Model):
        year_in_school = models.SmalllIntegerField(
            choices=YEAR_IN_SCHOOL_CHOICES(),
            default=YEAR_IN_SCHOOL_CHOICES.FRESHMAN
        )

Then you can do something like this

::

    Student.objects.filter(
        year_in_school__gt=YEAR_IN_SCHOOL_CHOICES.SOPHOMORE)

To return all students in grades higher than Sophomore

-  A choice can be defined as attribute/value ``SOPHOMORE = 1`` in which case display name will be code name capitalized ``"Sophomore"`` and will be saved in DB as number ``1``
-  A choice value can be fully defined as a dict ``FRESHMAN = {"id": 0, "display": "New comer"}`` in which case display name will be ``"New comer"`` and id will be ``0``
- **NOTE:** attribute name must be in uppercase or it will be ignored (i.e FRESHMEN not freshman)

Defining extra keys to use in your code.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``Choices`` attributes are dictionaries so they can hold additional keys.
Those keys can be used in your code to define some settings or constants associated with that choice.
For example:

::

        class SettingsChoices(Choices):
            MAX_PAGE_WIDTH = {"id": 0, "display": "Maximum page width in pixels", "default": 100}

            def get_default_value(self, choice_id):
                try:
                   return self.get_choice(choice_id)["default"]
                except KeyError:
                   return None

        AVAILABLE_SETTINGS = SettingsChoices()

then in your code you can do

::

    try:
        return Settings.objects.get(name=AVAILABLE_SETTINGS.MAX_PAGE_WIDTH).value
    except Settings.DoesNotExist:
        return AVAILABLE_SETTINGS.get_default_value(AVAILABLE_SETTINGS.MAX_PAGE_WIDTH)

Inheriting ``Choices``
^^^^^^^^^^^^^^^^^^^^^^^^^
One choice class can inherit from another choice class.
**Example:**

::

        class SchoolYearChoices(Choices):
            FRESHMAN = {"id": 0, "display": "New comer"},
            SOPHOMORE = 1,
            JUNIOR = 2,
            SENIOR = 3

        class SchoolYearChoicesWithGraduate(SchoolYearChoices):
            GRADUATE = 4

        YEAR_IN_SCHOOL = SchoolYearChoicesWithGraduate()
        YEAR_IN_SCHOOL() == [
            {"id": 0, "display": "New comer"},
            {"id": 1, "display": "Sophomore"},
            {"id": 2, "display": "Junior"},
            {"id": 3, "display": "Senior"},
            {"id": 4, "display": "Graduate"},
        ]


Useful functions of ``Choices`` class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  ``get_display_name``: given choice id (value), return the display name of that id. same as model's ``get_<field_name>_display()``
-  ``get_choice_name``: Given choice id same as ``get_display_name`` but return code name
-  ``get_choice``: Given choice id, return a dictionary of all choice attributes

**Example:**

::

    class ExampleChoice(Choices):
        MY_KEY = {"id": 0, "display": "Display Of My Key", "additional_key": 1234}

    CHOICES_EXAMPLE = ExampleChoice()


    >>> CHOICES_EXAMPLE.get_display_name(CHOICES_EXAMPLE.MY_KEY)
    "Display Of My Key"
    >>> CHOICES_EXAMPLE.get_choice_name(CHOICES_EXAMPLE.MY_KEY)
    "my_key"
    >>> CHOICES_EXAMPLE.get_choice(CHOICES_EXAMPLE.MY_KEY)
    {"id": 0, "display": "Display Of My Key", "additional_key": 1234}

.. _KeyValueField:

**model\_helpers.KeyValueField**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need to have a simple key/value field. most developers would rely on ``JsonField`` which is good for some use cases but people using django admin may not like to modify json object that look like this

::

    {"key1": "value of some sort", "key2": "value containing \" character"}

``KeyValueField`` serialize objects in a more readable way. the dictionary above would be stored and displayed like this.

::

    key1 = value of some sort
    key2 = value containing " character

That's it. For you as a developer you will access your ``KeyValueField`` as a dictionary.

**Example**:

::

    class MyModel(models.Model):
         options = KeyValueField(separator=":")

    >> my_model.options = "key1 : val1 \n key2 : val2"
    >> my_model.options
    {"key1": "val1", "key2": "val2"}
    >>> str(my_model.options)
    "key1 : val1 \n key2 : val2"

You can find more examples in the test file ``tests/test_key_value_field.py``

**``KeyValueField`` is NOT good for:**

-  Maintain original value's datatype. all values are converted to unicode strings
-  Store a multiline value
