# Release history (latest release first)

## Version 0.2.0 (May 30, 2025)
- Data from 2025 update of Summary Tables and Particle Listings
- Add experimental support for data from Particle Listings
- SQLite file schema update to version 0.3 with additional tables to support data from Particle Listings, 
  a new column PDGDATA.VALUE_TEXT, and redefinition of PDGDATA.DISPLAY_VALUE_TEXT. The text representation
  of Summary Table values with error(s) and including powers of ten previously provided in PDGDATA.DISPLAY_VALUE_TEXT
  is now PDGDATA.VALUE_TEXT for consistency with the JSON API and new Listings tables. PDGDATA.DISPLAY_VALUE_TEXT
  is redefined to no longer include the powers of ten indicated by PDGDATA.DISPLAY_POWERS_OF_TEN nor any percent signs.
- Support navigation between branching fractions and contributing branching fraction ratios
- Miscellaneous bug fixes

## Version 0.1.4 (April 18, 2025)
- Add tutorial for Python API
- Add usage example for SQLite files
- List conference presentations in About
- Update publication to PyPI using github actions
- Updated SQLite file with many small bug fixes

## Version 0.1.3 (October 4, 2024)
- SQLite bug fix: incorrect is_limit for some decays
- SQLite bug fix: incorrect unit for some lifetimes
- SQLite bug fix: remove superfluous arrows from PDGID descriptions
- Add additional unit tests
- Remove leftover inclusion of distutils

## Version 0.1.2 (July 5, 2024)
- Extend installation instructions
- Updated SQLite file with fix for is_limit bug and extended pdgdoc entry for PDGDATA.LIMIT_TYPE

## Version 0.1.1 (June 28, 2024)
- Bug fixes and minor improvements to code (no updates to SQLite file)

## Version 0.1.0 (May 31, 2024)

- Data from 2024 _Review of Particle Physics_
- First production version
- Minor bug fixes and documentation updates

## Version 0.0.7 (May 28, 2024)

- Revised database schema (version 0.2) with new `pdgitem`, `pdgitem_map` and `pdgdecay` tables
- Support for decays
- Bug fixes (especially also in metadata)
- Final beta version for 2023 _Review of Particle Physics_

## Version 0.0.6 (Dec 14, 2023)

- Support for widths and lifetimes
- Bug fixes (especially also in metadata)

## Version 0.0.5 (May 31, 2023)

- First public beta version
- Data from 2023 update of _Review of Particle Physics_
