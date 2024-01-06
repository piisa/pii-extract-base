# Guidelines for PII regex implementation

## Rules

* Implement it as a regular expression _string_, **not** as a compiled regular
  expression (it will be compiled when loaded by the module)
* The pattern **will be compiled with the [regex] package**, instead of the
  `re` package in the standard Python library, so you can use the extended
  features (such as unicode categories) in `regex`. Compilation will be done
  in backwards-compatible mode (i.e. using the `VERSION0` flag), so it should
  be fully compatible with `re`
* Do **not** anchor the regex to either beginning or end (it should be able to
  match anywhere in the passed string, which itself can be any portion of
  a document)
* It is usually convenient to try to define regex boundaries, e.g. by framing
  it with `\b` (when appropriate) or by using lookahead or lookbehind 
  assertions, positive or negative (e.g. `(?=...)`, `(?<=...)`, etc)
* The regex must either produce no capturing groups (then the whole match will
  be considered as the PII value) or a single one (which will be the PII value)
* The pattern will be compiled with the [re.VERBOSE] (aka `re.X`) flag, so
  take that into account (in particular, **whitespace is ignored**, so if it is
  part of the regular expression needs to included as a category i.e. `\s`, or
  escaped as `\ `)
  

## Method qualification

Assuming that a regex has been created so as not to miss any valid matches
(i.e. no false negatives), its quality will be determined by the amount of
false positives (matches that do not actually correspond to a valid PII
instance) it generates. In this scenario we could classify the regex as
belonging to one of these four groups:

1. `weak-regex`: a regex that can cause a considerable number of false
   positives. E.g. _any list of 8 digits_
2. `soft-regex`: a regex that has enough structure to avoid a great portion
   of false positives, but still not very distinctive. E.g. _a list of 8 digits
   that starts with 0, 1 or 2_
3. `regex`: a regex that should mostly limit to actual matches, plus some
   occasional false positives. E.g. _a list of 8 digits followed by a dash and
   a single ASCII letter_
4. `strong regex`: a regex that is very unlikely to match anything other
   than true positives. E.g. _a list of 3 groups of 3 digits separated by
   dashes, in which the first group contains only 1, 2, or 3 and the last
   only 5, 6 or 7_ or _a full email address, containing a valid domain_
  
Of course this classification is inherently subjective, since it is difficult
to perfectly foresee the exact number of false positives that a regex will
generate, so it is intended only as a hint. Adding it as the `method` field
in the [task descriptor] may help downwards when taking decisions about PII
detection results.

Note that this classification is independent of any other validation methods
that a task may incorporate over the regex match, such as checksum or
context. Those can be added as additional elements to the `method` field
(which is a comma-separated list of methods).

[regex]: https://github.com/mrabarnett/mrab-regex
[re.VERBOSE]: https://docs.python.org/3/library/re.html#re.X
[task descriptor]: task-descriptor.md

