"""
Test cases for the info table and other metadata.
"""
from __future__ import print_function

import sys
import os
import unittest
import time
import sqlalchemy

import pdg


class TestMetaData(unittest.TestCase):

    api = None

    @classmethod
    def setUpClass(cls):
        print()
        header = 'Testing with Python %s, SQLAlchemy %s' % (sys.version, sqlalchemy.__version__)
        print(header)
        print('*'*len(header))
        cls.api = pdg.connect()
        if len(cls.api.editions) == 1:
            print('WARNING: testing with single-edition database - not all tests can be run')
        print()
        print(cls.api)

    def test_api_version(self):
        self.assertEqual(pdg.__version__, '0.2.0', 'version number mismatch')

    def test_has_producer(self):
        self.assertIsNotNone(self.api.info('producer'), 'database does not have producer info')

    def test_has_status(self):
        self.assertIsNotNone(self.api.info('status'), 'database does not have status info')

    def test_has_schema_version(self):
        self.assertIsNotNone(self.api.info('schema_version'), 'database does not have schema version info')

    def test_has_created(self):
        self.assertIsNotNone(self.api.info('data_release'), 'database does not have data_release data')

    def test_has_created_timestamp(self):
        self.assertIsNotNone(self.api.info('data_release_timestamp'), 'database does not have data_release timestamp')
        os.environ['TZ'] = 'America/Los_Angeles'
        time.tzset()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(float(self.api.info('data_release'))))
        self.assertEqual(self.api.info('data_release_timestamp'), timestamp)

    def test_has_edition(self):
        self.assertIsNotNone(self.api.info('edition'), 'database does not have edition info')

    def test_has_citation(self):
        self.assertIsNotNone(self.api.info('citation'), 'database does not have citation info')

    def test_has_license(self):
        self.assertIsNotNone(self.api.info('license'), 'database does not have license info')

    def test_has_about(self):
        self.assertIsNotNone(self.api.info('about'), 'database does not have about info')

    def test_schema_version(self):
        self.assertTrue(float(self.api.info('schema_version')) >= pdg.MIN_SCHEMA_VERSION)


if __name__ == '__main__':
    unittest.main()
