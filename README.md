PDG Python API
==============

The Python package `pdg` provides programmatic access to the data
published by the  Particle Data Group (PDG) in the
*Review of Particle Physics*.

This repository uses Git LFS to manage Sqlite database file. You need to have Git LFS installed
before checking out the repository. Please see the instructions at https://github.com/git-lfs/git-lfs.

**PLEASE NOTE: This software is a beta release for testing and is still under active development.
The data provided by the present version should not be used in any scientific publications
without careful checking of every single data item retrieved from the PDG API.**

For documentation of the PDG API see https://pdgapi.lbl.gov/doc. 

The source code for this package can be found at
https://github.com/particledatagroup/api.

The *Review of Particle Physics* is available online from the PDG website at https://pdg.lbl.gov.

General information about PDG and the *Review of Particle Physics*
can be found at https://pdg.lbl.gov/about.

To provide feedback or report bugs, please contact api@pdg.lbl.gov.

## Release history (latest release first)

### Version 0.0.7 (May 24, 2024)

- Revised database schema (version 0.2) with new `pdgitem`, `pdgitem_map` and `pdgdecay`
- Support for decays
- Bug fixes (especially also in metadata)
- Final beta version for 2023 _Review of Particle Physics_

### Version 0.0.6 (Dec 14, 2023)

- Support for widths and lifetimes
- Bug fixes (especially also in metadata)

### Version 0.0.5 (May 31, 2023)

- First public beta version
- Data from 2023 partial update of _Review of Particle Physics_

