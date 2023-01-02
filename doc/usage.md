# Usage

## API Usage

There are two types of API usage: the object-based API (lower-level, based on
object instantiation) and the file-based API (higher-level, based on function
calls).


### File-based API

The file-based API uses the `process_file` function to read an SrdDocument
from a file and write the result as a PII Collection to an output file. It is
executed as:

```Python

from pii_extract import PiiEnum
from pii_extract.api import process_file

# Define language, country(ies) and PII tasks
lang = 'en'
country = ['US', 'GB']
tasklist = (PiiEnum.CREDIT_CARD, PiiEnum.GOVID, PiiEnum.MEDICAL)

# Process the file
process_file(infilename, outfilename, lang,
             country=country, pii=tasklist)
```


### Object API

The object-based API is centered on the `PiiProcessor` object. Its usage goes
like this:

```Python

from pii_extract import PiiEnum
from pii_extract.api import PiiProcessor

# Define language, country(ies) and PII tasks to instantiate
lang = 'en'
country = ['US', 'GB']
tasklist = (PiiEnum.CREDIT_CARD, PiiEnum.GOVID, PiiEnum.DISEASE)

# Instantiate object
proc = PiiProcessor()

# Build the task objects
proc.build_tasks(lang, country=country, pii=tasklist)

# Process a SourceDocument
piic = proc(doc)

for pii in piic:
  print(pii.asdict())
```

... this will load and execute PII extraction tasks for English that will
anonymize credit card numbers, disease information, and Government IDs for US
and UK (assuming all these tasks are implemented and available to the package),
and produce a `PiiCollection` object with the results.


It is also possible to load **all** possible tasks for a language, by not 
specifying a country list nor a `tasks` argument.

```Python

from pii_extract import PiiEnum
from pii_extract.api import PiiProcessor

proc = PiiProcesor()

proc.build_tasks('en')

piic = proc(doc)

```

...this will load all anonymization tasks available for English, including:
 * language-independent tasks
 * language-dependent but country-independent tasks
 * country-dependent tasks for *all* countries implemented under the `en`
   language


### Raw text API

It is also possible to use the object API to process a raw text buffer. For
that we can define a `DocumentChunk` on the fly:

```Python

from pii_data.types.doc import DocumentChunk
from pii_extract.api import PiiProcessor, PiiCollectionBuilder

chunk = DocumentChunk(id=0, data="...a text buffer...")

proc = PiiProcesor()
proc.build_tasks(lang="en")

piic = PiiCollectionBuilder(lang="en")
proc.detect_chunk(chunk, piic)

for pii in piic:
  print(pii.asdict())
```


## Command-line usage

Installing the package provides also a command-line script, `pii-detect`,
that can be used to process files through PII tasks:

    pii-detect <infile> <outfile> --lang es --country es ar mx \
       --tasks CREDIT_CARD BLOCKCHAIN_ADDRESS BANK_ACCOUNT

or, to add all possible tasks for a given language:

    pii-detect <infile> <outfile> --lang es

If no language is specified, then the document to process must define a
language in its metadata.

There is an additional command-line script, `pii-task-info`, that does not
process documents; it is only used to show the available tasks for a given
language.


## Gathering tasks

The tasks that the package can [collect and make available] to the API are:
 * Tasks provided in a pii-extract plugin, such as [pii-extract-plg-regex]
 * Tasks defined in a JSON task file added as configuration


[collect and made available]: task-collection.md
[pii-extract-plg-regex]: http://github.com/piisa/pii-extract-plg-regex
