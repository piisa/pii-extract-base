# ChangeLog

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
 
 
