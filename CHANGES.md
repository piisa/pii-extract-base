# ChangeLog

## 0.7.0
 * when building tasks, pass along the config to the task constructor
 * can deactivate context filter via task config
 * improved error reporting on regex compile exceptions
 * improved debug messages
 * use add_process_stage() from pii-data 0.5.0
 * fix: ensure process stage is not duplicated
 * fix in task_info script
 * fix: filter out tasks by language, also for multiclass descriptors

## 0.6.1
 * fix: corrected debug output for context

## 0.6.0
 * fix: must export class in pii_extract.api
 * added debug output when executing tasks

## 0.5.0
 * Added `languages` argument to PiiProcessor, to restrict the pre-collection
   of tasks
 * Ensure a task is not built twice in the same PiiTaskCollection, if it's for
   the same language
 * fixed task_info api call & script

## 0.4.0
 * PiiCollectionBuilder modified, adding methods add_detector_fields() &
   add_collection()
 * PiiBaseTask: add task-level method if pii-level method is not available
 * updated for pii-data v. 0.4.0
 * refactor a number of modules (**note: breaking changes**)

## 0.3.1
 * removed cache of built tasks: now they are rebuilt again if included
   in lists (each task decides if it caches something)
 * fixed regex group detection (when there are initial unmatched groups)
 * fix: do not expand the language list in BaseTaskCollector.gather_tasks()
   (would cause to execute the gather process twice)
 * added more logging lines

## 0.3.0
 * TaskCollection can build several task lists, for different languages
    - tasks already built for other languages are reused
 * PiiProcessor refactored to allow multilingual operation
    - build_tasks() can be called several times on the same object
    - on detection, the object uses the task list for the document/chunk lang
 * Sort detected PII instances by position inside the chunk

## 0.2.1
 * improvements in debug output
 * fix: country filter should not act if the task does not have a country

## 0.2.0
 * another refactor, enabling task plugins
 * split it into `pii-extract-base` and `pii-extract-plg-regex` plugin
 * manage configurations
 * multi-tasks are now available

## 0.1.0
 * full refactor, new package is `pii-manager`
 * there are now three modes for task implementation
 * three processing modes (replace, tag, extract)
 * a file-based API and an object-based API
 * manage configuration files
    - task configurations
    - plugin configurations
 * added "status" to PiiInstance objects
 * when building tasks, use "multi_type" task info to allow mult-type tasks
 
 
