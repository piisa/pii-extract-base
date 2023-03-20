# Pii Extract Base

[![version](https://img.shields.io/pypi/v/pii-extract-base)](https://pypi.org/project/pii-extract-base)
[![changelog](https://img.shields.io/badge/change-log-blue)](CHANGES.md)
[![license](https://img.shields.io/pypi/l/pii-extract-base)](LICENSE)
[![build status](https://github.com/piisa/pii-extract-base/actions/workflows/pii-extract-base-pr.yml/badge.svg)](https://github.com/piisa/pii-extract-base/actions)

This repository builds a Python package providing a base library for PII 
detection for Source Documents i.e. extraction of PII (Personally Identifiable
Information aka [Personal Data]) items existing in the document.

The package itself does **not** implement any PII Detection tasks, it only
provides the base infrastructure for the process. Detection tasks must be
supplied [externally].


## Requirements

The package needs
 * at least Python 3.8
 * the [pii-data] base package
 * one or more pii-extract plugins (to actually do real detection work)

## Usage

The package can be used:
 * As an API, in two flavors: function-based API and object-based API
 * As a command-line tool

For details, see the [usage document].


## Building

The provided [Makefile] can be used to process the package:
 * `make pkg` will build the Python package, creating a file that can be
   installed with `pip`
 * `make unit` will launch all unit tests (using [pytest], so pytest must be
   available)
 * `make install` will install the package in a Python virtualenv. The
   virtualenv will be chosen as, in this order:
     - the one defined in the `VENV` environment variable, if it is defined
     - if there is a virtualenv activated in the shell, it will be used
     - otherwise, a default is chosen as `/opt/venv/pii` (it will be
       created if it does not exist)


[pii-data]: https://github.com/piisa/pii-data
[python-stdnum]: https://github.com/arthurdejong/python-stdnum
[Makefile]: Makefile
[usage document]: doc/usage.md

[pytest]: https://docs.pytest.org
[Personal Data]: https://en.wikipedia.org/wiki/Personal_data
[externally]: doc/adding-tasks.md
