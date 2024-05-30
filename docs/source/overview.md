# Overview

The new API of the [Particle Data Group (PDG)](https://pdg.lbl.gov) provides programmatic access to the
data published in the _Review of Particle Physics_.
It provides three tools for accessing PDG data in machine-readable format that
are aimed at different use cases. The three tools are:

* a REST API,
* a Python API, and
* downloadable PDG database files.

The [REST API](restapi.md) allows retrieving
the data presented by [pdgLive](https://pdglive.lbl.gov)
in [JSON format](https://www.json.org/)
without installing any PDG-specific software.
Buttons labeled `JSON` are present on pdgLive pages where data can be downloaded. An example of
such a page is the
[pdgLive summary page of the charged pion](https://pdglive.lbl.gov/Particle.action?init=0&node=S008&home=MXXX005).

The [Python API](pythonapi.md), implemented in Python package [pdg](https://pypi.org/project/pdg/),
provides a high-level API for programmatically accessing PDG data. 
For most users, this will be the easiest and most versatile method for programmatically accessing PDG data.

The [PDG database file](schema.md) allows downloading the PDG data as a single file
in [SQLite](https://sqlite.org/index.html) format
that can be queried with [SQL](https://en.wikipedia.org/wiki/SQL) using any of the SQLite
libraries that  are available for many programming languages.
This option is intended for users who wish to incorporate PDG data into their own software for
an application, where the Python API is not suitable (e.g. because their software is written in a different
programming language such as C++), and who have the necessary technical expertise to correctly query the data.

Internally, these tools use digital object identifiers termed [PDG Identifiers](pdgidentifiers) in order
to reference specific items of PDG data. In most cases, the user does not need to know specific PDG Identifiers
and can instead either navigate to the quantity of interest in pdgLive (where the corresponding PDG Identifier is displayed)
or start with customary references such as Monte Carlo particle numbers or ASCII particle names.

The following chapters provide details on PDG Identifiers and on how to use the different tools for
programmatic access to PDG data.

Development of the PDG API is continuing in order to add additional features.
See [Development status](status.md) for an overview of what is available and what features are still
being developed.
