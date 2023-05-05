"""
Container base classes for PDG data.

All PDG data classes use lazy (i.e. only when needed) loading of data from the database
as implemented in the PdgData base class. In most cases, the data is read only once and
cached for subsequent use.

PdgProperty is a subclass of PdgData and adds the retrieval of summary values, measurement
data, etc., that is shared by all classes supporting the retrieval of different kinds of
particle physics properties such as branching fractions or particle masses.
"""

import pprint
from sqlalchemy import select, bindparam, func
from pdg.utils import parse_id, make_id
from pdg.units import UNIT_CONVERSION_FACTORS
from pdg.errors import PdgApiError, PdgInvalidPdgId, PdgAmbiguousValue


class PdgSummaryValue(dict):
    """Container for a single value from the PDG Summary Tables."""

    def __str__(self):
        if self.value_type() in ('AC', 'D', 'E'):
            indicator = 'OUR AVERAGE'
        elif self.value_type() in ('L',):
            indicator = 'BEST LIMIT'
        elif self.value_type() in ('OL',):
            indicator = 'OUR LIMIT'
        elif self.value_type() in ('FC', 'DR'):
            indicator = 'OUR FIT'
        elif self.value_type() in ('V', 'DV'):
            indicator = 'OUR EVALUATION'
        else:
            indicator = '[key = %s]' % self.value_type()
        return '%-20s %-20s  %s' % (self.display_value_text(), indicator, self.comment() if self.comment() else '')

    def pprint(self):
        """Print all data in this PdgSummaryValue object in a nice format (for debugging)."""
        pprint.pprint(self)

    def pdgid(self):
        """PDG Identifier of quantity for which the value is given."""
        return self['pdgid']

    def description(self):
        """Description of quantity for which the value is given"""
        return self['description']

    def value_type(self):
        """Get type of value."""
        return self['value_type']

    def in_summary_table(self):
        """Return True is value is included in Summary Table."""
        return self['in_summary_table']

    def confidence_level(self):
        """Return confidence level for limits, None otherwise."""
        return self['confidence_level']

    def is_limit(self):
        """Return True if value is a limit."""
        return self['confidence_level'] is not None

    def comment(self):
        """Get details for or comments on this value."""
        return self['comment']

    def value(self):
        """Get numerical central value.

        Units are given by unit_text() and depend on the specific data item.
        Check is_limit() to determine whether value() is a central value or a limit."""
        return self['value']

    def error_positive(self):
        """Get numerical value of positive uncertainty.

        Units are given by unit_text() and depend on the specific data item."""
        return self['error_positive']

    def error_negative(self):
        """Get numerical value of negative uncertainty.

        Units are given by unit_text() and depend on the specific data item."""
        return self['error_negative']

    def scale_factor(self):
        """Get PDG scale factor applied to error_positive() and error_negative()."""
        return self['scale_factor']

    def unit_text(self):
        """Return the unit in text format."""
        return self['unit_text']

    def display_value_text(self):
        """Get value and uncertainty in plain text format.

        Units are given by unit_text() and depend on the specific data item."""
        return self['display_value_text']

    def display_power_of_ten(self):
        """Return unit multiplier (as power of ten) as used for display in PDG Summary Tables."""
        return self['display_power_of_ten']

    def display_in_percent(self):
        """True if value is rendered in percent for display in PDG Summary Tables."""
        return self['display_in_percent']


class PdgConvertedValue(PdgSummaryValue):
    """A PdgSummaryValue class for storing summary values after unit conversion."""

    def __init__(self, value, to_unit):
        """Instantiate a copy of PdgSummaryValue value with new units to_unit."""
        super(PdgConvertedValue, self).__init__(value)
        self.original_unit = value.unit_text()
        try:
            old_factor = UNIT_CONVERSION_FACTORS[self.original_unit]
        except KeyError:
            raise PdgApiError('Cannot convert from %s' % self.original_unit)
        try:
            new_factor = UNIT_CONVERSION_FACTORS[to_unit]
        except KeyError:
            raise PdgApiError('Cannot convert to %s' % to_unit)
        if old_factor[1] != new_factor[1]:
            raise PdgApiError('Illegal unit conversion from %s to %s', old_factor[1], new_factor[1])
        conversion_factor = old_factor[0]/new_factor[0]
        for k in ('value', 'error_positive', 'error_negative', ):
            if self[k] is not None:
                self[k] *= conversion_factor
        for k in ('value_text', 'display_power_of_ten'):
            self[k] = None
        self['display_in_percent'] = False
        self['unit_text'] = to_unit


class PdgData(object):
    """Base class for PDG data containers.

    This class implements the lazy data retrieval from the database
    and is the base class for all PDG data container classes.
    """

    def __init__(self, api, pdgid, edition=None):
        """Instantiate a PdgData object for the given PDG Identifier pdgid.

        When a PdgData object is instantiated, the edition of the Review of Particle Physics
        from which data will be retrieved is determined by the first edition information found
        from the following list:

        1. An edition specified as part of the PDG Identifier
        2. An edition is specified by parameter edition
        3. The default edition specified by the database to which the API is connected

        The chosen edition can be queried by calling edition() and changed at any by calling set_edition().
        """
        self.api = api
        self.baseid, self.edition = parse_id(pdgid)
        if self.edition is None:
            self.edition = edition
        if self.edition is None:
            self.edition = self.api.edition
        self.pdgid = make_id(self.baseid, self.edition)
        self.cache = dict()

    def __str__(self):
        return 'Data for PDG Identifier %s: %s' % (self.pdgid, self.description())

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, make_id(self.baseid, self.edition))

    def _get_pdgid(self):
        """Get PDG Identifier information."""
        if 'pdgid' not in self.cache:
            pdgid_table = self.api.db.tables['pdgid']
            query = select(pdgid_table).where(pdgid_table.c.pdgid == bindparam('pdgid'))
            with self.api.engine.connect() as conn:
                try:
                    self.cache['pdgid'] = conn.execute(query, {'pdgid': self.baseid}).fetchone()._mapping
                except AttributeError:
                    raise PdgInvalidPdgId('PDG Identifier %s not found' % self.pdgid)
        return self.cache['pdgid']

    def _get_summary_values(self):
        """Get all summary data values."""
        if 'summary' not in self.cache:
            # FIXME: if we keep PDGDATA.PDGID, don't need to join with PDGID
            pdgid_table = self.api.db.tables['pdgid']
            pdgdata_table = self.api.db.tables['pdgdata']
            query = select(pdgdata_table, pdgid_table.c.description).join(pdgid_table)
            query = query.where(pdgid_table.c.pdgid == bindparam('pdgid'))
            query = query.where(pdgdata_table.c.edition == bindparam('edition'))
            query = query.order_by(pdgdata_table.c.sort)
            self.cache['summary'] = []
            with self.api.engine.connect() as conn:
                for entry in conn.execute(query, {'pdgid': self.baseid, 'edition': self.edition}):
                    self.cache['summary'].append(PdgSummaryValue(entry._mapping))
        return self.cache['summary']

    def _count_data_entries(self, pdgid, edition):
        """Count number of data entries for a given PDG identifier and edition."""
        pdgdata_table = self.api.db.tables['pdgdata']
        query = select(func.count("*")).select_from(pdgdata_table)
        query = query.where(pdgdata_table.c.pdgid == bindparam('pdgid'))
        query = query.where(pdgdata_table.c.edition == bindparam('edition'))
        with self.api.engine.connect() as conn:
            return conn.execute(query, {'pdgid': pdgid.upper(), 'edition': edition}).scalar()

    def set_edition(self, edition):
        """Set edition of the Review of Particle Physics to be used for retrieving data.

        Note: calling set_edition will invalidate the data cache of the PdgData instance.
        """
        self.edition = edition
        self.pdgid = make_id(self.baseid, self.edition)
        self.cache = dict()

    def parent_pdgid(self, include_edition=True):
        """Return PDG Identifiers of parent quantity."""
        if include_edition:
            return make_id(self._get_pdgid()['parent_pdgid'], self.edition)
        else:
            return self._get_pdgid()['parent_pdgid']

    def particle(self):
        """Return PdgParticle for this property's particle."""
        p = self
        while (p.baseid != p.parent_pdgid(False) and p.parent_pdgid(False)):
            p = self.api.get(p.parent_pdgid())
        return p

    def data_edition(self):
        """Return year of edition for which data is requested."""
        return self.edition

    def description(self):
        """Return description of data."""
        return self._get_pdgid()['description']

    def data_type(self):
        """Return type of data."""
        return self._get_pdgid()['data_type']

    def data_flags(self):
        """Return flags augmenting data type information."""
        return self._get_pdgid()['flags']


class PdgProperty(PdgData):
    """Base class for containers for data containers for particle properties."""

    def summary_values(self, summary_table_only=False):
        """Return list of summary values for this quantity.

        By default, all summary values are included, even if they are only shown in the
        Particle Listings and not listed in the Summary Tables. Set summary_table_only to
        True to get only summary values listed in the Summary Tables.
        """
        if summary_table_only:
            return [v for v in self._get_summary_values() if v.in_summary_table()]
        else:
            return self._get_summary_values()

    def n_summary_table_values(self):
        """Return number of summary values in Summary Table for this quantity."""
        return len(self.summary_values(summary_table_only=True))

    def best_value(self, summary_table_only=False):
        """Return the PDG "best" value for this quantity.

        If there is either a single summary value in Particle Listings and Summary Tables, or there are multiple
        summary values but only one is included in the Summary Tables, then this value is returned as the
        PDG best value. Otherwise, there is no unambiguous PDG "best" value.

        If there are no summary values at all, None is returned.
        If there are multiple summary values, e.g. based on assuming or not assuming CPT, a PdgAmbiguousValue
        Exception will be raised.

        If summary_table_only is True, then best value must be included in the Summary Table and cannot be shown only
        in the Particle Listings.
        """
        if not summary_table_only:
            summaries = self.summary_values(summary_table_only=False)
            if len(summaries) == 1:
                return summaries[0]
            else:
                return self.best_value(summary_table_only=True)
        else:
            summaries = self.summary_values(summary_table_only=True)
            if len(summaries) == 1:
                return summaries[0]
            elif len(summaries) == 0:
                return None
            else:
                raise PdgAmbiguousValue('%s (%s) has multiple summary values' % (self.pdgid, self.description()))

    def has_best_value(self, summary_table_only=False):
        """Return True if there is a single PDG "best" value (see best_value() for definition)."""
        try:
            return self.best_value(summary_table_only) is not None
        except PdgAmbiguousValue:
            return False
