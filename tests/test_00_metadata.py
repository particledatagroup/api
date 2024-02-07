"""
Test cases for the info table and other metadata.
"""
from __future__ import print_function

import os
import time

import pdg


def test_api_version():
    assert pdg.__version__ == '0.0.7', 'version number mismatch'

def test_has_producer(api):
    assert api.info('producer') is not None, 'database does not have producer info'

def test_has_status(api):
    assert api.info('status') is not None, 'database does not have status info'

def test_has_schema_version(api):
    assert api.info('schema_version') is not None, 'database does not have schema version info'

def test_has_created(api):
    assert api.info('data_release') is not None, 'database does not have data_release data'

def test_has_created_timestamp(api):
    assert api.info('data_release_timestamp') is not None, 'database does not have data_release timestamp'
    os.environ['TZ'] = 'America/Los_Angeles'
    time.tzset()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(float(api.info('data_release'))))
    assert api.info('data_release_timestamp') == timestamp

def test_has_edition(api):
    assert api.info('edition') is not None, 'database does not have edition info'

def test_has_citation(api):
    assert api.info('citation') is not None, 'database does not have citation info'

def test_has_license(api):
    assert api.info('license') is not None, 'database does not have license info'

def test_has_about(api):
    assert api.info('about') is not None, 'database does not have about info'

def test_schema_version(api):
    assert float(api.info('schema_version')) >= pdg.MIN_SCHEMA_VERSION
