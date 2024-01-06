# PII Task Implementation

A PII task is a module that provides detection of a given PII (possible for a
given language and country). The `pii-extract-base` package accepts three
types of implementations for a PII task. They are commented in the following
sections.

Once defined, a task is made available to the framework via a [task
descriptor], which defines all the fields needed to use the task.


## 1. Regex implementation

In its simplest form, a PII Task can be just a regular expression pattern.
This pattern should match string fragments that correspond to the PII entity 
to be detected. See the [guidelines for creating PII regexes].

An example can be seen in the [international phone number] detector.


## 2. Callable implementation

The next implementation type is via a function. The signature for the function
is:

```Python

   RETURN_TYPE = Union[str, Tuple[str, int]]

   def my_pii_detector(src: str) -> Iterable[RETURN_TYPE]:
```

The function can have any name, but it may be good to have an illustrative name,
since if the task descriptor does not contain a task name, the function name
will be used as the `name` attribute for the task (after converting underscores
into spaces).

The function should:

 * accept a string: the document chunk to analyze
 * return an iterable that produces detection results. It can produce two types
   of results:
     * a tuple `(<string>, <position>)`, indicating a detected PII text and
       its position in the text chunk
     * a single string: this is a detected PII text. The framework will find
       its position in the text chunk (if it appears more than once, it will
       report it for each occurrence)

An example can be seen in the [australian business number] detector.

**Note**: the second return option (single-string results) could produce
ambiguity. If a given string in the document is a PII some of the time but
it also appears in a non-PII role in the same document, the wrapper that uses
the result of a callable implementation type will not be able to differentiate
among them, and the package will label *all* ocurrences of the string as PII.
If this is likely to happen, and there is code that *can* separate both uses,
use the first return option (tuple), or the class implementation type below.

Additionally, in case the same entity appears more than once in the passed
document and the callable produces multiple reports for them, the second return
form might produce PII duplicates.


## 3. Class implementation

In this case the task is implemented as a full Python class. The class *must*:

 * inherit from `pii_extract.build.task.BasePiiTask` (or if it can detect
   more than one PII type, `pii_extract.build.task.MultiPiiTask`)
 * implement a `find` method with the following signature:

        def find(self, text: str) -> Iterable[PiiEntity]:

   i.e. a method returning an iterable of identified [PiiEntity] objects

 * the default task name will be taken from the class-level attribute
   `pii_name`, if it exists, or else from the class name.

The class can also, optionally, include a constructor. In this case, the
constructor must
 * accept an arbitrary number of keyword arguments
 * call the parent class constructor with those arguments

In other words, a constructor must follow the following form:

```Python

   def __init__(self, **kwargs):
     super().__init__(**kwargs)
     ... any code specific to the implementation here ...
```


An example can be seen in the [credit card] detector.


## Context-based PII validation

If the task descriptor contains a [context definition], then all detected PII
instances will be further validated by searching for context text around them.

The base class for a task already implements a `find_context()` method that
uses the context specification for the task (if it is defined) to assess
detected candidates. This method is inherited by all subclasses, so if the
task contains a context definition (as detailed above) all regex, callable or 
class implementations of a task use it automatically to confirm or reject the
candidates detected by their `find()` methods. Hence, no further action is
needed apart from the context definition.

If we need a more specific variant of context assessment, then a class
implementation of the task can override the base class `find_context()` 
method and provide its own implementation. The signature is the same as for
the `find()` method, i.e.

    def find_context(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:

... and it must carry out the *whole* PII detection process:
  1. Detect PII candidates (maybe by calling the regular `find()` method)
  2. Validate them by checking their contexts



[task descriptor]: task-descriptor.md
[context definition]: task-descriptor.md#context-validation
[guidelines for creating PII regexes]: regex.md

[PiiEntity]: https://github.com/piisa/pii-data/tree/main/doc/piientity.md

[international phone number]: ../test/taux/modules/en/any/international_phone_number.py
[credit card]: ../test/taux/modules/any/credit_card_mock.py
[Australian business number]: ../test/taux/modules/en/au/abn_ex.py
