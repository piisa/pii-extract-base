# Adding tasks to pii-extract

The `pii-extract-base` package does **not** contain any implementation of PII
tasks. Tasks must then be [implemented] externally and added to the framework.

There are three ways to attach external tasks:
 * via a pii-extract plugin
 * via a JSON definition
 * via folder traversal


## Plugin

A pii-extract plugin is a Python package that must have:
  * an entry point for the group `pii-extract.plugins` (this is done in the
    `setup.py` packaging file)
  * the entry point must be a class with:
     - a constructor (with optional arguments, see below)
     - a `get_tasks()` method delivering an iterable of task descriptors, with
       an optional "lang" argument to restrict to a specific language
     - optional attributes `source`, `version` and `description`

Plugin instantiation can be customized by a
`piisa:config:extract:plugins:v1` configuration. This is a dict indexed
by plugin entry point. Each plugin configuration can contain:
 * `load`: a boolean parameter indicating whether to load the plugin (default
   is `True`)
 * `options`: a dict of keyword arguments to pass to the plugin constructor
 
 
A plugin constructor will have as arguments:
 * `config`: a PIISA configuration object, from which it can take its own
   section, if present
 * `debug`: a boolean to activate debug output
 * `**options`: additional arguments, as defined in the extract config
 
One example of a plugin is [pii-extract-plg-regex].

Installed plugins are automatically discovered by `pii-extract-base`, so if
the task is inside a plugin, no further action is needed. 

## JSON

Tasks can also be added by using a package configuration, with tag 
`piisa:config:extract:tasks:v1`. This configuration will have:
  * the `format` field
  * a `header` field, that can contain a dictionary of default task descriptor
    fields
  * a `tasklist` field, which will contain a list of task descriptors.
  
There is an [example available]
  

## Folder

A folder collector class can be instantiated to traverse a folder and its
subfolders, and collect all tasks defined there. The folder structure has two
levels:
 * first level is task language
 * second level is task country

All files within a subfolder will be inspected searching for `PII_TASKS`
variables, which must contain [task descriptors].

There is a [small example of a folder] available.


[example available]: ../test/data/tasklist-example.json
[implemented]: task-implementation.md
[task descriptors]: task-descriptor.md
[small example of a folder]: ../test/taux/modules
[pii-extract-plg-regex]: https:/github.com/piisa/pii-extract-plg-regex
