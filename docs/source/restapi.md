# REST API

The PDG REST API supports the downloading of PDG data in [JSON format](https://www.json.org/).
pdgLive uses this API to implement the `JSON` buttons. The REST API may also be used by user programs for
incidental downloading of PDG data.

## Terms of use

The PDG REST API is intended for incidental access.
Please do not use it if you wish to download a fair fraction or all
of the PDG data - Python API and database files are provided for use cases where this is desired.

To avoid overwhelming the PDG server, access is strictly rate-limited.
Please limit your access to the REST API to **less than 2 requests per second**. IP addresses that
substantially exceed this limit will be blocked for 5 minutes at a time from accessing all PDG services.
Repeat offenders may be permanently blocked.

## Data versions

The data provided by the REST API comes from the latest version of the *Review of Particle Physics* as presented on
the [PDG website](https://pdg.lbl.gov) and in [pdgLive](https://pdglive.lbl.gov). The *Review of Particle Physics*
is updated yearly. Whenever a new version becomes available, the data provided by the API is also updated. Between
these updates, minor updates may be made to address mistakes
(see [list of errata](https://pdg.lbl.gov/errata) on
the PDG website).
These updates are propagated to the REST API as soon as possible after they become available on pdgLive.
The `data_release_timestamp` gives the date and time when the last update was made (see description of `/info` below). 

For summary values only, the [PDG Identifier](pdgidentifiers) can be used to request data from a previous edition.


## Access

The PDG REST API uses URLs of the form
```
https://pdgapi.lbl.gov/PATH
```
where PATH is one of the paths given in the table below, and
PDGID is the PDG Identifier of the desired quantity.

| Path                     | Example                                                                                    | Description                                                       |
|--------------------------|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| /info                    | [https://pdgapi.lbl.gov/info](https://pdgapi.lbl.gov/info)                                 | Get metadata (edition, citation, version, license)                |
| /summaries/PDGID         | [https://pdgapi.lbl.gov/summaries/S126M](https://pdgapi.lbl.gov/summaries/S126M)           | Get summary data for PDG Identifier                               |
| /summaries/PDGID/EDITION | [https://pdgapi.lbl.gov/summaries/S126M/2020](https://pdgapi.lbl.gov/summaries/S126M/2020) | Get summary data from an earlier edition                          |
 | /listings/PDGID         | [https://pdgapi.lbl.gov/listings/S126M](https://pdgapi.lbl.gov/listings/S126M) | Get Particle Listings (i.e. measurements) data for PDG Identifier | 
| /doc                     | [https://pdgapi.lbl.gov/doc](https://pdgapi.lbl.gov/doc)                                   | This documentation (regular web page, not JSON)                   |

Except for the documentation pages under `/doc`, all paths return JSON documents.


## Contents of JSON documents

### Preamble

All JSON documents start with the following general information about the request:

| Key               | Data type | Description                                              |
|-------------------|:----------|----------------------------------------------------------|
| status_code       | Number    | HTTP response code                                       |
| status_message    | String    | Explanation of status (e.g. "OK" for successful request) |
| request_timestamp | String    | Time stamp of when the request was received              |
| request_url       | String    | URL for the request                                      |
| edition           | String    | Edition of the _Review of Particle Physics_ being used   |
| about             | String    | A help message providing the link to this documentation  |

### Data returned by /info

The `/info` path provides general information about the data being returned by the other paths:

| Key                    | Data type | Description                                                             |
|------------------------|-----------|-------------------------------------------------------------------------|
| data_release_timestamp | String    | Time stamp of when the data provided by the API was released            |
| citation               | String    | Citation for the *Review of Particle Physics* from which the data comes |
| license                | String    | License for using the data returned by the API                          |

### Data returned by /summaries

The `/summaries` path returns the data published for a given quantity
in the Summary Tables of the *Review of Particle Physics*. The following
information is returned when the PDG Identifier denotes a single particle property or branching fraction:

| Key         | Data type | Description                                                                                 |
|-------------|-----------|---------------------------------------------------------------------------------------------|
| pdgid       | String    | PDG Identifier/particle property for which data is returned                                 |
| description | String    | Plain-ASCII description of the quantity the PDG Identifier refers to                        |
| mode_number | String    | Only for branching fractions: number of this decay in current edition (*)                   |
| section     | String    | Only for branching fractions: section, if any, where mode appears (e.g. "Inclusive decays") |
| pdg_values  | Array     | Array of JSON objects, each describing a summary value (see below)                          |

(*) Please note that the mode_number of a decay may change from one edition of the *Review of Particle Physics* to the next one.

Each JSON object describing a summary value may contain the following data
(keys whose value is not meaningful for the present summary value are omitted):

| Key              | Data type | Description                                                 |
|------------------|-----------|-------------------------------------------------------------|
| value            | Number    | Central value or limit                                      |
| error_positive   | Number    | Positive error or null                                      |
| error_negative   | Number    | Negative error or null                                      |
| value_text       | String    | Plain-text representation of the value with errors or limit |
| unit             | String    | Units                                                       |
| scale_factor     | Number    | Error scale factor when applied to errors                   |
| is_limit         | Boolean   | true if value is a limit, omitted otherwise                 |
| is_upper_limit   | Boolean   | true if value is an upper limit, omitted otherwise          |
| is_lower_limit   | Boolen    | true if value is a lower limit, omitted otherwse            |
| confidence_level | Number    | Confidence level for limits or null                         |
| type             | String    | Type of data ("OUR FIT" etc)                                |

In case the PDG Identifier denotes a particle, the following is returned:

| Key         | Data type | Description                                                                                                                                                                                                                                                                                                                                            |
|-------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| pdgid       | String    | PDG Identifier of particle for which data is returned                                                                                                                                                                                                                                                                                                  |
| description | String    | Plain-ASCII description of the particle the PDG Identifier refers to                                                                                                                                                                                                                                                                                   |
| summaries   | Array     | A JSON objects with keys "properties" and/or "branching_fractions", each containing a list of JSON objects for the PDG Identfier(s) describing particle properties or branching fractions for this particle. These JSON objects are the same as what would be returned when querying for a single property or branching fraction, as documented above. |


### Data returned by /listings

The `/listings` path returns the data published for a given quantity
in the Particle Listings of the *Review of Particle Physics*. This includes an annotated list
of relevant measurements and information on how PDG arrived at its averages, fits or best limits published
in the Summary Tables for this quantity. Note that the Summary Table information is NOT included under '/listings' but
must be separately obtained via '/summaries' if desired.

The following information is returned by '/listings'. As for '/summaries', properties without value are not included.

| Key                | Data type | Description                                                                                                                                                                          |
|--------------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| pdgid              | String    | PDG Identifier/particle property for which data is returned                                                                                                                          |
| description        | String    | Plain-ASCII description of the quantity the PDG Identifier refers to                                                                                                                 |
| note               | String    | Explanatory note in ASCII format, typically shown in the header of the data table                                                                                                    |
| parent_pdgid       | String    | Parent PDG Identifier/particle of the returned data                                                                                                                                  |
| parent_description | String    | Plain-ASCII description of parent PDG Identifier/particle                                                                                                                            |
| measurements       | Array     | An array of JSON objects, each describing a measurement of the corresponding quantities (see below)                                                                                  |
| related_data       | Array     | An array of JSON objects for PDG Identifiers whose data contributes to the corresponding quantity. Each entry contains the JSON that /listings would return for that PDG Identifier. |

The key related_data is present for branching fractions (example: S035.1) and provides the information for all measured quantities (typically ratios of branching fractions) used to determine the corresponding branching fraction. 

Each JSON object describing a measurement may contain the following data
(keys whose value is not meaningful or known for the present quantity are omitted):

| Key                | Data type | Description                                                                                      |
|--------------------|-----------|--------------------------------------------------------------------------------------------------|
| document_id        | String    | PDG document id (example: "AAD 2023BP")                                                          |
| publication_name   | String    | Publication reference (example: ""PRL 131 251802")                                               |
| publication_year   | Integer   | Year of the publication                                                                          |
| doi                | String    | DOI of the publication                                                                           |
| inspire_id         | String    | INSPIRE ID of the publication                                                                    |
| title              | String    | Title of the publication (from INSPIRE)                                                          |
| technique          | String    | Abbreviation of the experiment or technique used by the measurement (example: "ATLS")            |
| comment            | String    | Comment shown in the Particle Listings (example: "p p, 13 TeV, gamma gamma, Z Z^* --> 4 lepton") |
| is_changed         | Boolean   | Flag indicating whether this measurement was added or changed compared to the previous edition   |
| measurement_values | Array     | Array of values or other information measured by or associated with this publication             |
| footnotes          | Array     | Array of footnotes associated with this publication                                              |

The elements in measurement_values describe the individual columns of the row describing a given measurement in a
table of the Particle Listings.
In many cases, there is only a single data column named "VALUE" that gives the result of the corresponding measurement
made by that publication. However, some data tables in the Listings give additional information such as measurement energy
or model assumptions. In such cases, measurement_values would have multiple entries with the information for the different columns.

Each JSON object in the measurement_values array may contain the following key/value pairs:

| Key                  | Data type | Description                                                                                                                                                                             |
|----------------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| column_name          | String    | Name of the column ("VALUE" for the value of a measurement)                                                                                                                             |
| value                | Number    | Central numerical value                                                                                                                                                                 |
| error_positive       | Number    | Positive total numerical uncertainty                                                                                                                                                    |
| error_negative       | Number    | Negative total numerical uncertainty                                                                                                                                                    |
| stat_error_positive  | Number    | Positive statistical numerical uncertainty                                                                                                                                              |
| stat_error_negative  | Number    | Negative statistical numerical uncertainty                                                                                                                                              |
| syst_error_positive  | Number    | Positive systematic numerical uncertainty                                                                                                                                               |
| syst_error_negative  | Number    | Negative systematic numerical uncertainty                                                                                                                                               |
| value_text           | String    | Text representation of value and uncertainties                                                                                                                                          |
| unit                 | String    | Unit of the value, such as "GeV"                                                                                                                                                        |
| used_in_average      | Boolean   | Flag indicating if value was used in PDG average                                                                                                                                        |
| used_in_fit          | Boolean   | Flag indicating if value was used in PDG fit                                                                                                                                            |
| display_value_text   | String    | Text representation of value and uncertainties as shown in the Particle Listings data table, factoring out any powers of ten and possible percent sign shown in the header of the table |
| display_power_of_ten | Integer   | Power of ten factored out from display_value_text                                                                                                                                       |
| display_in_percent   | Boolean   | Flag indicating if display_value_text is in percent (if true, display_power_of_ten is -2)                                                                                               |

Each JSON object in the footnotes array contains the following key/value pairs:

| Key        | Data type | Description                                                                                 |
|------------|-----------|---------------------------------------------------------------------------------------------|
| index      | Integer   | Index of the footnote                                                                       |
| text       | String    | Text of the footnote (ASCII representation)                                                 |
| is_changed | Boolean   | Flag indicating whether this footnote was added or changed compared to the previous edition |


## Error handling

If the request fails, an appropriate HTTP status code is returned,
together with a JSON document providing details on the error and the failed request .
The following status codes may be generated:

| HTTP status code | Error description                              |
|------------------|------------------------------------------------|
| 400              | Invalid path                                   |
| 404              | No such PDG Identifier                         |
| 500              | Internal error (this is a bug - please report) |


## License

The data downloaded via the PDG REST API is subject to the license used by the corresponding edition
of the _Review of Particle Physics_.
Starting with the 2024 edition, the _Review of Particle Physics_ is published under a
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.
