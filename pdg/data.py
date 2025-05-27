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
from pdg.units import UNIT_CONVERSION_FACTORS, convert
from pdg.errors import PdgApiError, PdgInvalidPdgIdError, PdgAmbiguousValueError, PdgNoDataError
from pdg.measurement import PdgMeasurement


class PdgSummaryValue(dict):
    """Container for a single value from the Summary Tables."""

    def __str__(self):
        indicator = self.value_type
        if not indicator:
            indicator = '[key = %s]' % self.value_type_key
        return '%-20s %-20s  %s' % (self.value_text, indicator, self.comment if self.comment else '')

    def pprint(self):
        """Print all data in this PdgSummaryValue object in a nice format (for debugging)."""
        pprint.pprint(self)

    def get_value(self, units=None):
        """Return value after conversion into units specified by parameter units (string).

        If units are not specified, the value is returned without conversion in the default units for this quantity.
        Check properties is_limit, is_lower_limit and is_upper_limit to determine if value is a central value or limit.
        """
        if units is None:
            return self['value']
        else:
            try:
                return convert(self['value'], self['unit_text'], units)
            except TypeError:
                return None

    def get_error_positive(self, units=None):
        """Return positive error after conversion into units specified by parameter units (string).

        If units are not specified, the positive error is returned without conversion in the default
        units for this quantity.
        """
        if units is None:
            return self['error_positive']
        else:
            return convert(self['error_positive'], self['unit_text'], units)

    def get_error_negative(self, units=None):
        """Return negative error after conversion into units specified by parameter units (string).

        If units are not specified, the negative error is returned without conversion in the default
        units for this quantity.
        """
        if units is None:
            return self['error_negative']
        else:
            return convert(self['error_negative'], self['unit_text'], units)

    def get_error(self, units=None):
        """Symmetric error or None, in units specified by parameter units (string).

        Returns symmetric error as average of positive and negative errors if they differ by less than 10% of
        their average. Otherwise, returns None. Also returns None if the quantity is a limit."""
        if self.is_limit:
            return None
        try:
            err_avg = (self.error_positive + self.error_negative) / 2.0
            if abs(self.error_positive - self.error_negative) < 0.1 * err_avg:
                return convert(err_avg, self['unit_text'], units)
            else:
                return None
        except TypeError:
            return None

    @property
    def pdgid(self):
        """PDG Identifier of quantity for which value is given."""
        return self['pdgid']

    @property
    def description(self):
        """Description of quantity for which value is given"""
        return self['description']

    @property
    def value_type_key(self):
        """Type of value, given by its key.

        See PdgApi.doc_value_type_keys() for the meaning of the different value type keys."""
        return self['value_type']

    @property
    def value_type(self):
        """Type of value, given as the PDG indicator string."""
        if self.value_type_key in ('AC', 'D', 'E'):
            return 'OUR AVERAGE'
        elif self.value_type_key in ('L',):
            return 'BEST LIMIT'
        elif self.value_type_key in ('OL',):
            return 'OUR LIMIT'
        elif self.value_type_key in ('FC', 'DR'):
            return 'OUR FIT'
        elif self.value_type_key in ('V', 'DV'):
            return 'OUR EVALUATION'
        else:
            return ''

    @property
    def in_summary_table(self):
        """True if value is included in Summary Table."""
        return self['in_summary_table']

    @property
    def confidence_level(self):
        """Confidence level for limits, None otherwise."""
        return self['confidence_level']

    @property
    def is_limit(self):
        """True if value is a limit."""
        return self['confidence_level'] is not None or self['limit_type'] is not None

    @property
    def is_upper_limit(self):
        """True if value is an upper limit."""
        return self['limit_type'] == 'U'

    @property
    def is_lower_limit(self):
        """True if value is an lower limit."""
        return self['limit_type'] == 'L'

    @property
    def comment(self):
        """Details for or comments on this value."""
        return self['comment']

    @property
    def value(self):
        """Numerical value in units given by property units.

        Check properties is_limit, is_lower_limit and is_upper_limit to determine if value is a central value or limit.
        """
        return self['value']

    @property
    def error_positive(self):
        """Numerical value of positive error in units given by property units."""
        return self['error_positive']

    @property
    def error_negative(self):
        """Numerical value of negative error in units given by property units."""

        return self['error_negative']

    @property
    def error(self):
        """Symmetric error or None.

        Returns symmetric error as average of positive and negative errors if they differ by less than 10% of
        their average. Otherwise, returns None. Also returns None if the quantity is a limit."""
        return self.get_error()

    @property
    def scale_factor(self):
        """PDG error scale factor that was applied to error_positive and error_negative."""
        return self['scale_factor'] or 1.0

    @property
    def units(self):
        """Units (in plain text format) used by value, error_positive,
        error_negative, and display_value_text."""
        return self['unit_text']

    # @property
    # def units_tex(self):
    #     """Units (in TeX format) used by value, error_positive, error_negative,
    #     and display_value_text."""
    #     return self['unit_tex']

    @property
    def value_text(self):
        """Value and uncertainty (in plain text format) in units given by
           property units, including the power of ten, if applicable
           (see display_power_of_ten)"""
        return self['value_text']

    # @property
    # def value_tex(self):
    #     """Value and uncertainty (in TeX format) in units given by property
    #        units, including the power of ten, if applicable (see
    #        display_power_of_ten)"""
    #     return self['value_tex']

    @property
    def display_value_text(self):
        """Value and uncertainty in plain text format as displayed in
           Listings tables. Does not include any power of ten or percent sign.
           Must be combined with the display_power_of_ten property in order
           to obtain the numerical value in units given by the property units."""
        return self['display_value_text']

    @property
    def display_power_of_ten(self):
        """Unit multiplier (as power of ten) as used for display in Listings."""
        return self['display_power_of_ten']

    @property
    def display_in_percent(self):
        """True if value is rendered in percent for display in Listings.
           Implies that display_power_of_ten is -2."""
        return self['display_in_percent']


class PdgConvertedValue(PdgSummaryValue):
    """A PdgSummaryValue class for storing summary values after unit conversion."""

    def __init__(self, value, to_units):
        """Instantiate a copy of PdgSummaryValue value with new units to_unit."""
        super(PdgConvertedValue, self).__init__(value)
        self.original_units = value.units
        try:
            old_factor = UNIT_CONVERSION_FACTORS[self.original_units]
        except KeyError:
            raise PdgApiError('Cannot convert from %s' % self.original_units)
        try:
            new_factor = UNIT_CONVERSION_FACTORS[to_units]
        except KeyError:
            raise PdgApiError('Cannot convert to %s' % to_units)
        if old_factor[1] != new_factor[1]:
            raise PdgApiError('Illegal unit conversion from %s to %s', old_factor[1], new_factor[1])
        conversion_factor = old_factor[0]/new_factor[0]
        for k in ('value', 'error_positive', 'error_negative', ):
            if self[k] is not None:
                self[k] *= conversion_factor
        for k in ('value_text', 'display_power_of_ten'):
            self[k] = None
        self['display_in_percent'] = False
        self['unit_text'] = to_units


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
        2. An edition specified by parameter edition
        3. The default edition specified by the database to which the API is connected

        The chosen edition can be queried by calling edition() and changed at any by calling set_edition().
        """
        self.api = api
        self.baseid, self._edition = parse_id(pdgid)
        if self._edition is None:
            self._edition = edition
        if self._edition is None:
            self._edition = self.api.edition
        self.pdgid = make_id(self.baseid, self._edition)
        self.cache = dict()

    def __str__(self):
        return 'Data for PDG Identifier %s: %s' % (self.pdgid, self.description)

    def __repr__(self):
        extra = self._repr_extra()
        if extra:
            extra = ', ' + extra
        return "%s('%s'%s)" % (self.__class__.__name__, make_id(self.baseid, self.edition),
                               extra)

    def _repr_extra(self):
        """A method that subclasses can override in order to add info to the
        result of __repr__.
        """
        return ''

    def _get_pdgid(self):
        """Get PDG Identifier information."""
        if 'pdgid' not in self.cache:
            pdgid_table = self.api.db.tables['pdgid']
            query = select(pdgid_table).where(pdgid_table.c.pdgid == bindparam('pdgid'))
            with self.api.engine.connect() as conn:
                try:
                    self.cache['pdgid'] = conn.execute(query, {'pdgid': self.baseid}).fetchone()._mapping
                except AttributeError:
                    raise PdgInvalidPdgIdError('PDG Identifier %s not found' % self.pdgid)
        return self.cache['pdgid']

    def _get_summary_values(self):
        """Get all summary data values."""
        if 'summary' not in self.cache:
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

    def get_parent_pdgid(self, include_edition=True):
        """Return PDG Identifier of this property's parent. In most cases, this
        will be the PDG ID of the particle itself. For those properties, such as
        neutrino mixing angles, that don't have a specific parent particle, the
        parent will be a top-level section (S067 in this case). If this
        property's direct parent is a subsection header, it will be skipped, and
        the PDGID of the top-level section or particle will be returned
        instead."""
        if self._get_pdgid()['parent_pdgid'] is None:
            return None
        p = self
        while p._get_pdgid()['parent_pdgid'] is not None:
            p = self.api.get(p._get_pdgid()['parent_pdgid'], self.edition)
        return p.pdgid if include_edition else p.baseid

    def get_particles(self):
        """Return PdgParticleList for this property's particle."""
        p = self.api.get(self.get_parent_pdgid())
        if p.data_type != 'PART':
            err = 'Identifier %s does not have a parent particle'
            raise PdgNoDataError(err)
        return p

    def get_particle(self):
        """Returns PdgParticle for this property's particle. Raises
        PdgAmbiguousValueError when there are multiple matches."""
        ps = self.get_particles()
        assert len(ps) > 0
        if len(ps) > 1:
            err = "More than one PdgParticle found. Consider using get_particles() instead."
            raise PdgAmbiguousValueError(err)
        return ps[0]

    def get_children(self, recurse=False):
        pdgid_table = self.api.db.tables['pdgid']
        ## NOTE: Querying on IDs doesn't work because the `parent_id` seems off
        # query = select(pdgid_table.c.pdgid) \
        #     .where(pdgid_table.c.parent_id == bindparam('parent_id'))
        # params = {'parent_id': self._get_pdgid()['id']}
        query = select(pdgid_table.c.pdgid) \
            .where(pdgid_table.c.parent_pdgid == bindparam('parent_pdgid'))
        params = {'parent_pdgid': self.baseid}
        with self.api.engine.connect() as conn:
            child_pdgids = [row.pdgid for row
                            in conn.execute(query, params)]
        for child_pdgid in child_pdgids:
            child = self.api.get(child_pdgid)
            yield child
            if recurse:
                for c in child.get_children(recurse=True):
                    yield c

    @property
    def edition(self):
        """Year of edition for which data is requested."""
        return self._edition

    @edition.setter
    def edition(self, edition):
        """Set year of edition used for retrieving data (invalidates cache)."""
        self._edition = edition
        self.pdgid = make_id(self.baseid, self._edition)
        self.cache = dict()

    @property
    def description(self):
        """Description of data."""
        return self._get_pdgid()['description']

    @property
    def data_type(self):
        """Type of data."""
        return self._get_pdgid()['data_type']

    @property
    def data_flags(self):
        """Flags augmenting data type information."""
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
            return [v for v in self._get_summary_values() if v.in_summary_table]
        else:
            return self._get_summary_values()

    def n_summary_table_values(self):
        """Return number of summary values in Summary Table for this quantity."""
        return len(self.summary_values(summary_table_only=True))

    def best_summary(self, summary_table_only=False):
        """Return the PDG "best" summary value for this quantity.

        If there is either a single summary value in Particle Listings and Summary Tables, or there are multiple
        summary values but only one is included in the Summary Tables, then this value is returned as the
        PDG best value.

        If there are multiple summary values (e.g. based on assuming or not assuming CPT in the evaluation) and
        PdgApi.pedantic is False, the first value shown in Summary Tables or Particle Listings will be returned.
        If PdgApi.pedantic is True, a PdgAmbiguousValue Exception will be raised.

        If there are no summary values, None is returned.

        If summary_table_only is True, then the best value must be included in the Summary Table and cannot
        be shown only in the Particle Listings.
        """
        if not summary_table_only:
            summaries = self.summary_values(summary_table_only=False)
            if len(summaries) == 1:
                return summaries[0]
            else:
                return self.best_summary(summary_table_only=True)
        else:
            summaries = self.summary_values(summary_table_only=True)
            if len(summaries) == 1:
                return summaries[0]
            elif len(summaries) == 0:
                return None
            else:
                if self.api.pedantic:
                    raise PdgAmbiguousValueError('%s (%s) has multiple summary values' % (self.pdgid, self.description))
                else:
                    return summaries[0]

    def has_best_summary(self, summary_table_only=False):
        """Return True if there is a single PDG "best" value (see best_value() for definition)."""
        try:
            return self.best_summary(summary_table_only) is not None
        except PdgAmbiguousValueError:
            return False

    def get_measurements(self):
        """Return all of the measurements associated with this property."""
        pdgmsmt_table = self.api.db.tables['pdgmeasurement']
        query = select(pdgmsmt_table.c.id)
        query = query.where(pdgmsmt_table.c.pdgid == bindparam('pdgid'))
        with self.api.engine.connect() as conn:
            for entry in conn.execute(query, {'pdgid': self.baseid}):
                yield PdgMeasurement(self.api, entry.id)

    @property
    def confidence_level(self):
        """Shortcut for best_summary().confidence_level."""
        return self.best_summary().confidence_level

    @property
    def is_limit(self):
        """Shortcut for best_summary().is_limit."""
        return self.best_summary().is_limit

    @property
    def value(self):
        """Shortcut for best_summary().value."""
        return self.best_summary().value

    @property
    def error(self):
        """Shortcut for best_summary().error."""
        return self.best_summary().error

    @property
    def error_positive(self):
        """Shortcut for best_summary().error."""
        return self.best_summary().error_positive

    @property
    def error_negative(self):
        """Shortcut for best_summary().error."""
        return self.best_summary().error_negative

    @property
    def scale_factor(self):
        """Shortcut for best_summary().scale_factor."""
        return self.best_summary().scale_factor

    @property
    def units(self):
        """Shortcut for best_summary().units."""
        return self.best_summary().units

    @property
    def comment(self):
        """Shortcut for best_summary().comment."""
        return self.best_summary().comment

    @property
    def value_text(self):
        """Shortcut for best_summary().value_text."""
        return self.best_summary().value_text

    @property
    def display_value_text(self):
        """Shortcut for best_summary().display_value_text."""
        return self.best_summary().display_value_text


class PdgMass(PdgProperty):
    pass


class PdgWidth(PdgProperty):
    pass


class PdgLifetime(PdgProperty):
    pass


class PdgText(PdgData):
    pass
