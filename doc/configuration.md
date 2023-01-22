# Package configuration

The package follows the standard [configuration model] and format for a PIISA
module. There are two local configuration sections recognized:
 * a _plugin_ configuration
 * a _tasks_ configuration
 
 
## Plugin configuration

The plugin configuration has as format tag 
`piisa:config:extract:plugins:v1`. If present, it will contain a
dictionary, indexed by plugin name (the name of the plugin entry point).

A configuration for one specific plugin can contain up to two keys:
 * `load`: a boolean indicating if the plugin is to be loaded. Defaults to
   `True`, i.e. all installed plugins are normally loaded, but this option
   can be used to prevent loading of certain plugins
 * `options`: a dictionary with keyword arguments to be handed over the
   plugin loader class constructors, to customize plugin instatiation
   
Note that the plugin loader class constructor will also be given the general
configuration object, so if this object contains a configuration section
specific for a plugin, it will be fetched from there. The `options` keys is
intended for speciall parameters beyond this plugin configuration.


## Tasks configuration

The tasks configuration has as format tag `piisa:config:extract:tasks:v1`.
It should contain a list of [task descriptors] and can be used to [collect
arbitrary detection tasks] implemented elsewhere.


[configuration model]: https://github.com/piisa/docs/configuration.md
[task descriptors]: task-descriptor.md
[collect arbitrary detection tasks]: task-collection.md#json
