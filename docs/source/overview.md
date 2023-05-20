# Overview

In addition to fixed-format data files that have been available for many years,
the [Particle Data Group (PDG)](https://pdg.lbl.gov) is developing a new API (Application Programming Interface)
to access the data published in the _Review of Particle Physics_. 

**PLEASE NOTE: THIS API IS STILL UNDER DEVELOPMENT AND CURRENTLY ONLY AVAILABLE AS A BETA RELEASE FOR TESTING.**

The new API provides three
options for accessing PDG data in machine-readable format. These three options are aimed at different use cases.
They are:

* a REST API,
* a Python API, and
* downloadable PDG database files.

The [REST API](restapi.md) allows retrieving
the data presented by [pdgLive](https://pdglive.lbl.gov)
in [JSON format](https://www.json.org/)
without installing any PDG-specific software.
Buttons labeled `JSON (beta)` are present on pdgLive pages where data can be downloaded. An example of
such a page is the
[pdgLive summary page of the charged pion](https://pdglive.lbl.gov/Particle.action?init=0&node=S008&home=MXXX005).

The [Python API](pythonapi.md), implemented in Python package [`pdg`](https://pypi.org/project/pdg/),
provides a high-level API for programmatically accessing PDG data. 
For most users, this will be the easiest and most versatile method for programmatically accessing PDG data.

The [PDG database file](schema.md) allows downloading the PDG data as a single file
in [SQLite](https://sqlite.org/index.html) format
that can be queried with [SQL](https://en.wikipedia.org/wiki/SQL) using any of the SQLite
libraries that  are available for many programming languages.
This option is intended for users who wish to incorporate PDG data into their own software for
an application, where the Python API is not suitable (e.g. because their software is written in a different
programming language such as C++), and who have the necessary technical expertise to correctly query the data.

All three of these options use digital object identifiers termed [PDG Identifiers](pdgidentifiers) in order
to reference specific items of PDG data.

The following chapters provide details on PDG Identifiers and on how to use the different options for
programmatic access to PDG data.

The PDG API is still under development and is currently only available as a beta release.
See [Development status](status.md) for an overview of what features are already available and what is still
being developed.