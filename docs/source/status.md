# Development status

Development of the PDG API is continuing in order to add additional features. See below for what is currently available
and what features are still under development and will become available in the future.

Release notes for different versions of the Python API can be found in the
[CHANGELOG file](https://github.com/particledatagroup/api/blob/main/CHANGELOG.md). 

## Bug reports and feedback
To provide feedback on the PDG API or to report any bugs:
- For general comments as well as feedback or bugs specific to REST API or database files, please
  contact [api@pdg.lbl.gov](mailto:api@pdg.lbl.gov).
- For anything related to the Python API, either submit an [Issue on github](https://github.com/particledatagroup/api/issues)
  or contact [api@pdg.lbl.gov](mailto:api@pdg.lbl.gov).

## Features supported by the current version
* [REST API](restapi.md) with pdgLive JSON download links 
* [Python API](pythonapi.md) API package [pdg](https://pypi.org/project/pdg/)
* [PDG database files](schema.md) - see [API page on the PDG website](https://pdg.lbl.gov/api) for available files
* All the above tools support access to the data published in the Summary Tables (excluding footnotes),
  with access both via individual PDG Identifiers and navigation via particles to particle properties,
  **branching fractions**, and the corresponding Summary Table values.
* Starting with the 2025 update of the _Review of Particle Physics_, **experimental access to
  the data from the Particle Listings** is available.

## Limitations and known bugs of the current API version
- Fit information and correlation matrices are not yet accessible
- Conservation law data is not yet accessible
- Some header text/notes of Listing sections are not yet accessible
- Some text representations of values in the Listings lack parentheses, for example the API might return "2.60361+-0.00052E-8" instead of "(2.60361+-0.00052)E-8"
- Numerical values are missing for some limits (only text representation is available)

## Features under development
* Implement access to the parts of the Listings data currently not yet accessible (see above)
* Improved processing of aliases such as \ell and generic decay products in branching fractions
* Improved handling of "indented" decay modes
* Searching of PDG Identifiers and associated data (other than by low-level SQL querying of the data in the SQLite file)
* General improvements of and extensions to existing features
* ...

