# PDG Identifiers

Many quantities used in particle physics are difficult to reference unambiguously in a plain-text format as
is typically needed when writing programs or querying a database.
Therefore, each quantity evaluated by PDG, such as for example a given particle's mass or a specific branching fraction,
is assigned a unique digital object identifier termed *PDG Identifier*.
These identifiers can be used across all PDG tools and interfaces to reference and look up the information
on a desired quantity.

PDG Identifiers are case-insensitive, alphanumeric strings consisting
of either a single group of characters (e.g. "S126M")
or a group of alphanumeric characters and an integer number separated by a period (e.g. "S008.1").
(In the past the latter was written in the form "NODE:DESIG=NUMBER". That format is now obsolete and no longer supported.)
The complete list of PDG Identifiers is published on the
[PDG website](https://pdg.lbl.gov/) under "Downloads" in "Book, Booklet, Data Files"
and can also be generated using the Python API or from the SQLite database file.

The world averages provided by PDG generally change from one edition of the
*Review of Particle Physics* to the next one. If one wishes to reference the value of a quantity from a specific
edition, the year of the edition can be appended to the base PDG Identifier. For example, "S126M" corresponds to the
current value of the Higgs mass as provided by the edition of the *Review of Particle Physics* being used,
while "S126M/2022" denotes the specific value published in the 2022 edition. Not all PDG resources support
PDG Identifiers referencing a specific edition of the *Review of Particle Physics*.

In most cases, users should not need to know or enter specific PDG Identifiers. However, if one wishes to refer
to a specific PDG data item, it is best to look up and use the corresponding PDG Identifier.
The easiest way to find a desired PDG Identifier is to look up the corresponding quantity
in [pdgLive](https://pdglive.lbl.gov) and find the `JSON (beta)` button. The URL that the button points to,
as well as the JSON file that will be retrieved upon clicking it,
will identify the corresponding PDG Identifier.
