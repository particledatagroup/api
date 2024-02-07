#!/usr/bin/env python3

import sys

import pytest
import sqlalchemy

import pdg

# NOTE: Use "pytest -s" in order to see the printed output
print()
header = 'Testing with Python %s, SQLAlchemy %s' % (sys.version, sqlalchemy.__version__)
print(header)
print('*'*len(header))
API = pdg.connect()
if len(API.editions) == 1:
    print('WARNING: testing with single-edition database - not all tests can be run')
print()
print(API)

@pytest.fixture
def api():
    API.pedantic = False
    return API
