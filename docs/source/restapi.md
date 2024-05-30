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

| Path                     | Example                                                                                    | Description                                        |
|--------------------------|--------------------------------------------------------------------------------------------|----------------------------------------------------|
| /info                    | [https://pdgapi.lbl.gov/info](https://pdgapi.lbl.gov/info)                                 | Get metadata (edition, citation, version, license) |
| /summaries/PDGID         | [https://pdgapi.lbl.gov/summaries/S126M](https://pdgapi.lbl.gov/summaries/S126M)           | Get summary data for PDG Identifiers               |
| /summaries/PDGID/EDITION | [https://pdgapi.lbl.gov/summaries/S126M/2020](https://pdgapi.lbl.gov/summaries/S126M/2020) | Get summary data from an earlier edition           |
| /doc                     | [https://pdgapi.lbl.gov/doc](https://pdgapi.lbl.gov/doc)                                   | This documentation (regular web page, not JSON)    |

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
