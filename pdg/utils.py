"""
Utilities for PDG API.
"""


def parse_id(pdgid):
    """Parse PDG Identifier and return (normalized base identifier, edition)."""
    try:
        baseid, edition = pdgid.split('/')
    except ValueError:
        baseid = pdgid
        edition = None
    return (baseid.upper(), edition)


def base_id(pdgid):
    """Return normalized base part of PDG Identifier."""
    return parse_id(pdgid)[0]


def make_id(baseid, edition=None):
    """Return normalized full PDG Identifier, possibly including edition."""
    if baseid is None:
        return None
    if edition is None:
        return baseid.upper()
    else:
        return ('%s/%s' % (baseid, edition)).upper()
