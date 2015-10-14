## Model Helpers

Model helpers are small collection of django functions that make working with models easier. This doc describe each of these helpers 

### __model\_helpers.upload_to__
 pass `model_helpers.upload_to` as `upload_to` parameter for any FileField or ImageField.
This will generates random file name and return it while keeping the original file extension. each model get its own storage folder named after model's name.

__Sample usage:__
	
    import model_helpers
    
    class Profile(models.model):
        name = CharField(max_length=100)
        picture = ImageField(upload_to=model_helpers.upload_to)

uploaded images for this model will be stored in: `media/Profile/<random_name>`

### get\_current\_datetime
Normally calling this function is same as calling `timezone.now()`
However when writing test cases for your model/api you might need to assume certain datetime to be current datetime and that's when this function comes handy.

	In [2]: get_current_datetime()
	Out[2]: datetime.datetime(2015, 10, 13, 4, 53, 55, 443135, tzinfo=<UTC>)
	
	In [3]: from django.conf import settings
	In [4]: from django.utils.dateparse import parse_datetime
	In [5]: settings.CURRENT_DATETIME = parse_datetime("2014-01-01T01:01:01Z")
	In [6]: get_current_datetime()
	Out[6]: datetime.datetime(2014, 1, 1, 1, 1, 1, tzinfo=<UTC>)

The idea is using this function exclusively in your code to get current date/time in order to facilitate writing test cases.

### cached\_model\_property decorator

`cached_model_property` is a decorator for model functions that takes no arguments
 The decorator convert the function into a property that support caching out of the box
  
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

Now try

    team = Team.objects.first()

* `team.points`  <-- complex DB queries will happen, result will be returned
* `team.points`  <-- this time result is returned from cache (points function is not called
* `del team.points` <-- points value has been removed from cache
* `team.points`  <-- complex DB queries will happen, result will be returned

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
      })


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
* You can define extra keys to use in your code for example:

        AVAILABLE_SETTINGS = Choices({
            "max_page_width": {"id": 0, "display": "Maximum page width in pixels", "default": 100})

then in your code you can do

    settings = Settings.objects.filter(name=AVAILABLE_SETTINGS.max_page_width).first()
    if settings:
        return settings.value
    return AVAILABLE_SETTINGS[settings.name]["default"]
  
