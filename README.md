## Model Helpers

Model helpers are small collection of django functions that make working with models easier.
All functions here are compliant with pylint and has test cases with 100% code coverage.
This doc describe each of these helpers.

### __model\_helpers.upload_to__
Pass `model_helpers.upload_to` as `upload_to` parameter for any FileField or ImageField.
This will generates random file name and return it while keeping the original file extension.
each model get its own storage folder named after model's name.

`upload_to` function also block files with certain harmful extentions like "php" or "py" from being uploaded.

__Sample usage:__
	
    import model_helpers
    
    class Profile(models.model):
        name = CharField(max_length=100)
        picture = ImageField(upload_to=model_helpers.upload_to)

uploaded images for this model will be stored in: `media/Profile/<current_year>/<slugified_original_filename>`.

__Note:__f filename exceeds 40 character, it will be trimmedl.


### cached\_model\_property decorator

`cached_model_property` is a decorator for model functions that takes no arguments.
 The decorator convert the function into a property that support caching out of the box

 __Note__: `cached_model_property` is totally different from django's `model_property` the later is not true caching but rather memorizing function's return value.
  
  __Sample usage:__
  
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

    team = Team.objects.first()

* `team.points`  <-- complex DB queries will happen, result will be returned
* `team.points`  <-- this time result is returned from cache (points function is not called
* `del team.points` <-- points value has been removed from cache
* `team.points`  <-- complex DB queries will happen, result will be returned

__How does it work?__: first time the decorator store the function output in the cache with `key = "<model_class>_<instance.pk>_<function_name>"` so if you have two models with same name, or have model that provide no primary key you can't use this decorator.

set `readonly` parameter to `False` to make the property writeable

`team.editable_points = 88`

In this case the assigned value will replace the value stored in the cache

`team.editable_points` returns 88

I personally don't use the writable cached property option but might be useful to someone else

### Choices class _inspired by [Django Choices](https://pypi.python.org/pypi/django-choices/)._

Dealing with Django's `choices` attribute is a pain.
Here is a proper way of implementing choice field in Django

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

    student = Student.objects.first()
    if student.year_in_school == Student.SENIOR:
          # do some senior stuff
  
With Choices class this becomes

    YEAR_IN_SCHOOL_CHOICES = Choices({
        "freshman": "FR",
        "sophomore": "SO",
        "junior": "JR",
        "Senior": "SR"
    })


    class Student(models.Model):
        year_in_school = models.CharField(
                            max_length=2,
                            choices=YEAR_IN_SCHOOL_CHOICES(),
                            default=YEAR_IN_SCHOOL_CHOICES.freshman)

Then you can do

    student = Student.objects.first()
    if student.year_in_school == YEAR_IN_SCHOOL_CHOICES.senior:
          # do some senior stuff
 
`YEAR_IN_SCHOOL_CHOICES` is a readonly OrderedDict and you can treat it as such. for example:
`YEAR_IN_SCHOOL_CHOICES.keys()` or `YEAR_IN_SCHOOL_CHOICES.iteritems()`

`Choices` class is more flexible because it allow you to specify 3 values. choice name, choice db value, choice display name.
The example above can be better written like that

     YEAR_IN_SCHOOL_CHOICES = Choices({
         "freshman": {"id": 0, "display": "New comer"},
         "sophomore": 1,
         "junior": 2,
         "Senior": 3
      }, order_by="id")


    class Student(models.Model):
        year_in_school = models.SmalllIntegerField(
                            choices=YEAR_IN_SCHOOL_CHOICES(),
                            default=YEAR_IN_SCHOOL_CHOICES.freshman)

Then you can do something like this

    Student.objects.filter(
        year_in_school__gt=YEAR_IN_SCHOOL_CHOICES.sophomore)

To return all students in grades higher than Sophomore
 
* A choice can be defined as key/value `"sophomore": 1` in which case display name will be code name capitalized `"Sophomore"` and will be saved in DB as number `1`
* A choice can be fully defined as key/dict `"freshman": {"id": 0, "display": "New comer"}` in which case display name will be `"New comer"` and id will be `0`

#### Defining extra keys to use in your code.

As mentioned before `Choices` can be treated as an OrderedDictionary and so you should feel free to use the free functionality, for example adding extra keys

        AVAILABLE_SETTINGS = Choices({
            "max_page_width": {"id": 0, "display": "Maximum page width in pixels", "default": 100})

then in your code you can do

    settings = Settings.objects.filter(name=AVAILABLE_SETTINGS.max_page_width).first()
    if settings:
        return settings.value
    return AVAILABLE_SETTINGS["max_page_width"]["default"]
  

#### Ordering your `Choices`

Assuming you have a big list of choices you might prefer to ask Choices class to order them for you.

__Example:__

    Choices({
         "usa": {"display": "United States", "id": 0},
         "egypt": 1,
         "uk": {"display": "United Kingdom", "id": 2},
         "ua": {"display": "Ukraine", "id": 3}
        }, order_by="display")

The fields will be in the order "Egypt", "Ukraine", "United Kingdom", "United States".

`order_by="id"` will order the list by id
 
If you don't want any sort of ordering then set `order_by=None` and in this case its better that you pass your choices as tuple of dictionaries to maintain order

    Choices((
         ("uk", {"display": "United Kingdom", "id": 2),
         ("usa", {"display": "United States", "id": 0),
         ("egypt", 1),
         ("ua": {"display": "Ukraine", "id": 3})
        ), order_by=None)

__Note:__ By default choices are ordered by display name

#### Useful functions of `Choices` class

* `get_display_name`: given choice id, return the display name of that id. same as model's `get_<field_name>_display()`
* `get_code_name`: Given choice id same as `get_display_name` but return code name
* `get_value`: Given choice id, return value of any key defined inside choice entry

__Example:__

    CHOICES_EXAMPLE = Choices({"my_key": {"id": 0, "display": "Display Of My Key", "additional_key": 1234})
    >>> CHOICES_EXAMPLE.get_display_name(0)
    "Display Of My Key"
    >>> CHOICES_EXAMPLE.get_code_name(0)
    "my_key"
    >>> CHOICES_EXAMPLE.get_value(0, "additional_key")
    1234


### __model\_helpers.KeyValueField__

Sometimes you need to have a simple key/value field. most developers would rely on `JsonField` which is good for some use cases but people using django admin may not like to modify json object that look like this  

    {"key1": "value of some sort", "key2": "value containing \" character"}
      
`KeyValueField` serialize objects in a more readable way. the dictionary above would be stored and displayed like this.

    key1 = value of some sort
    key2 = value containing " character

That's it.
For you as a developer you will access your `KeyValueField` as a dictionary.  
  
__Example__:

    class MyModel(models.Model):
         options = KeyValueField(separator=":")

    >> my_model.options = "key1 : val1 \n key2 : val2"
    >> my_model.clean_fields()
    >> my_model.options
    {"key1": "val1", "key2": "val2"}
    >>> str(my_model.options)
    "key1 : val1 \n key2 : val2"

You can find more examples in the test file `tests/test_key_value_field.py`

__`KeyValueField` is NOT good for:__

* Maintain original value's datatype. all values are converted to unicode strings
* Store a multiline value
