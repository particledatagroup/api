# Development status

Development of the PDG API is continuing in order to add additional features. See below for what is currently available
and what features are still under development and will become available in the future.

Release notes for different versions of the Python API can be found in the
[CHANGELOG file](https://github.com/particledatagroup/api/blob/main/CHANGELOG.md). 

To provide feedback on the PDG API or to report any bugs, please contact [api@pdg.lbl.gov](mailto:api@pdg.lbl.gov).
For the Python API, you may also submit an [Issue on github](https://github.com/particledatagroup/api/issues).

## Features supported by the current version
* [REST API](restapi.md) with pdgLive JSON download links 
* [Python API](pythonapi.md) API package [pdg](https://pypi.org/project/pdg/)
* [PDG database files](schema.md) - see [API page on the PDG website](https://pdg.lbl.gov/api) for available files
* All of the above tools support access to the data published in the Summary Tables (excluding footnotes),
  with access both via individual PDG Identifiers and navigation via particles to particle properties,
  **branching fractions**, and the corresponding Summary Table values.

## Features under development
* Processing of aliases such as \ell and generic decay products in branching fractions
* Improved handling of "indented" decay modes
* Access to data published in the Particle Listings
* Searching of PDG Identifiers and associated data (other than by low-level SQL querying of the data in the SQLite file)
* General improvements of and extensions to existing features
* ...

