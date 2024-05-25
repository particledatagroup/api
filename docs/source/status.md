# Development status

The PDG API tools supporting programmatic access to PDG data are still **under development** and are currently only
available for testing as a **beta software release with limited functionality**.

You are invited to try out these new tools, but please be aware that this is software under development and that
there will be bugs. At this stage there is no guarantee that the data returned by any of the API tools is correct,
so please do not use data provided by the present version for any scientific work or publication without carefully
checking each data item you retrieve.

While we will try to minimize changes in the JSON file structure, schema changes of the SQLite database file,
and interface changes in the Python API package, such changes may still happen if deemed necessary to support
future development. As a result, **future releases may or may not be compatible with the present beta versions**.

## Features supported by the current version
* Beta versions of
  * REST API with pdgLive JSON download links
  * Python API package
  * SQLite files
* Access to the data published in the Summary Tables (excluding footnotes), with access both via individual PDG
  Identifiers and navigation via particles to particle properties, **branching fractions**, and the corresponding
  Summary Table values

## Features under development (not yet available in this beta version)
* Improvement to contents of underlying data tables, especially in the area of modelling decay products.
* Processing of aliases such as \ell in branching fractions
* Access to data published in the Particle Listings
* Searching of PDG Identifiers and associated data (other than by low-level SQL querying of the data in the SQLite file)
* Improved documentation, especially on using the SQLite database file
* General improvements of and extensions to existing features.
* ...

