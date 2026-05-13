"""
Utilities for PDG API.
"""
import math
from typing import TYPE_CHECKING, Iterator, Optional, Tuple, cast

from sqlalchemy import select, bindparam
from sqlalchemy.engine.row import RowMapping

from pdg.errors import PdgNoDataError, PdgAmbiguousValueError, PdgRoundingError

if TYPE_CHECKING:
    from pdg.api import PdgApi


def pdg_round(value: float, error: float) -> Tuple[float, float]:
    """Apply PDG rounding rules to a value and error.

    Args:
        value: Value
        error: Error

    Returns:
        `(value, error)` after rounding
    """
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


def parse_id(pdgid: str) -> Tuple[str, Optional[str]]:
    """Parse and normalize a PDG Identifier.

    Args:
        pdgid: String representation of a PDG Identifier.

    Returns:
        Tuple of the normalized PDG Identifier (capitalized and without edition)
        and the edition (or `None` if the edition was unspecified in `pdgid`).
    """
    try:
        baseid, edition = pdgid.split('/')
    except ValueError:
        baseid = pdgid
        edition = None
    return baseid.upper(), edition


def base_id(pdgid: str) -> str:
    """Get normalized base part of PDG Identifier.

    Equivalent to calling :func:`parse_id` and discarding the edition.

    Args:
        pdgid: String representation of a PDG Identifier.
    """
    return parse_id(pdgid)[0]


def make_id(baseid: str, edition: Optional[str]=None) -> str:
    """Get normalized full PDG Identifier, possibly including edition.

    Args:
        baseid: String representation of a PDG Identifier, assumed not to
            specify an edition.
        edition: Optional edition.

    Returns:
        Normalized base part of identifier, along with edition (if specified),
        separated by a slash.
    """
    if baseid is None:
        return None
    if edition is None:
        return baseid.upper()
    else:
        return ('%s/%s' % (baseid, edition)).upper()


def get_row_data(api: 'PdgApi', table_name: str, row_id: int) -> RowMapping:
    """Get a dict built from a specified table row.

    Args:
        api: API object for retrieving data.
        table_name: Name of the table in the SQLite file.
        row_id: Value of the `id` column (i.e. the primary key) to look up.
    """
    table = api.db.tables[table_name]
    query = select(table).where(table.c.id == bindparam('id'))
    with api.engine.connect() as conn:
        matches = conn.execute(query, {'id': row_id}).fetchall()
    assert len(matches) == 1
    return matches[0]._mapping


def get_linked_ids(api: 'PdgApi', table_name: str, src_col: str, src_id: int, dest_col: str='id') \
        -> Iterator[int]:
    """Get an iterator over internal links in a specified table.

    Note:
        `dest_col` is assumed to be an ID column (i.e. an int).

    Args:
        table_name: Name of the table in the SQLite file.
        src_col: The column in which to search for the `src_id`.
        src_id: The value (in the `src_col` column) corresponding to the
            "source" rows.
        dest_col: The column containing the IDs of the "destination" rows.

    Returns:
        The values of the `dest_col` column for all rows in which the `src_col`
        column is equal to `src_id`.
    """
    table = api.db.tables[table_name]
    query = select(table.c[dest_col]) \
        .where(table.c[src_col] == bindparam('src_id'))
    with api.engine.connect() as conn:
        for entry in conn.execute(query, {'src_id': src_id}):
            yield cast(int, entry._mapping[dest_col])
