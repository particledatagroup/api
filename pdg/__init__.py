"""
Python API to access PDG data.

The Python package pdg provides access to the particle physics data
published by the Particle Data Group (PDG) in the Review of Particle Physics.

For documentation see https://pdgapi.lbl.gov/doc.

For general information about PDG and the Review of Particle Physics
please visit https://pdg.lbl.gov.
"""
__author__ = 'Particle Data Group'
__version__ = '0.2.0'


import os
from pdg.api import PdgApi
from pdg.errors import PdgApiError


# Constants
SQLITE_FILENAME = 'pdg.sqlite'      # Default SQLite database file used by this API
MIN_SCHEMA_VERSION = 0.3            # Minimum schema version required by this version of the API


def connect(database_url=None, pedantic=False):
    """Connect to PDG database and return configured PDG API object."""
    if database_url is None:
        api = PdgApi('sqlite:///%s' % os.path.join(os.path.dirname(__file__), SQLITE_FILENAME), pedantic)
    else:
        api = PdgApi(database_url, pedantic)
    schema_version = float(api.info('schema_version'))
    if schema_version < MIN_SCHEMA_VERSION:
        raise PdgApiError('database schema v%s too old - need at least v%s' % (schema_version, MIN_SCHEMA_VERSION))
    return api
