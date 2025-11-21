"""
Utilities for PDG API.
"""
import math

from sqlalchemy import select, bindparam

from pdg.errors import PdgNoDataError, PdgAmbiguousValueError, PdgRoundingError


def pdg_round(value, error):
    """Return (value, error) as numbers rounded following PDG rounding rules."""
    # FIXME: might switch to returning decimal.Decimal rather than floats
    if error <= 0.:
        raise PdgRoundingError('PDG rounding requires error larger than zero')
    log = math.log10(abs(error))
    if abs(error) < 1.0 and int(log) != log:
        power = int(log)
    else:
        power = int(log) + 1
    reduced_error = error * 10 ** (-power)
    if reduced_error < 0.355:
        n_digits = 2
    elif reduced_error < 0.950:
        n_digits = 1
    else:
        reduced_error = 0.1
        power += 1
        n_digits = 2
    new_error = round(reduced_error, n_digits) * 10 ** power
    new_value = round(value * 10 ** (-power), n_digits) * 10 ** power
    return new_value, new_error


def parse_id(pdgid):
    """Parse PDG Identifier and return (normalized base identifier, edition)."""
    try:
        baseid, edition = pdgid.split('/')
    except ValueError:
        baseid = pdgid
        edition = None
    return baseid.upper(), edition


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




def get_row_data(api, table_name, row_id):
    """Return dict built from the row of the specified table that has an id of
    row_id.
    """
    table = api.db.tables[table_name]
    query = select(table).where(table.c.id == bindparam('id'))
    with api.engine.connect() as conn:
        matches = conn.execute(query, {'id': row_id}).fetchall()
    assert len(matches) == 1
    return matches[0]._mapping


def get_linked_ids(api, table_name, src_col, src_id, dest_col='id'):
    """Return iterator over all values of dest_col in the specified table for which
    src_col = src_id.
    """
    table = api.db.tables[table_name]
    query = select(table.c[dest_col]) \
        .where(table.c[src_col] == bindparam('src_id'))
    with api.engine.connect() as conn:
        for entry in conn.execute(query, {'src_id': src_id}):
            yield entry._mapping[dest_col]
