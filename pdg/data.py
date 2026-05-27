"""
Container base classes for PDG data.

All PDG data classes use lazy (i.e. only when needed) loading of data from the database
as implemented in the `PdgData` base class. In most cases, the data is read only once and
cached for subsequent use.

`PdgProperty` is a subclass of `PdgData` and adds the retrieval of summary values, measurement
data, etc., that is shared by all classes supporting the retrieval of different kinds of
particle physics properties such as branching fractions or particle masses.
"""

import pprint
from sqlalchemy import select, bindparam, func
from pdg.utils import parse_id, make_id
from pdg.units import UNIT_CONVERSION_FACTORS, convert
from pdg.errors import PdgApiError, PdgInvalidPdgIdError, PdgAmbiguousValueError, PdgNoDataError
from pdg.measurement import PdgMeasurement
from typing import TYPE_CHECKING, Iterator, Optional, cast

if TYPE_CHECKING:
    from pdg.api import PdgApi
    from pdg.particle import PdgParticle, PdgParticleList


class PdgSummaryValue(dict):
    "Container for a single value from the Summary Tables."

    def __str__(self) -> str:
        """Get description of the summary value.

        Returns:
            String with details including the value, its type, and any comments.
        """
        indicator = self.value_type
        if not indicator:
            indicator = '[key = %s]' % self.value_type_key
        return '%-20s %-20s  %s' % (self.value_text, indicator, self.comment if self.comment else '')

    def pprint(self) -> None:
        "Print all data in this `PdgSummaryValue` object in a nice format (for debugging)."
        pprint.pprint(self)

    def get_value(self, units: Optional[str]=None) -> Optional[float]:
        """Get value in specified units.

        Note:
            Check properties :func:`is_limit`, :func:`is_lower_limit` and
            :func:`is_upper_limit` to determine if value is a central value or
            limit.

        Args:
            units: Can be set to the desired unit (see
                :func:`~pdg.units.convert` for supported units). If unspecified,
                the value is returned without conversion in the default units
                for this quantity.

        Returns:
            Value, or `None` if there is no value in the database or if the unit
            conversion is invalid or unsupported.
        """
        if units is None:
            return self['value']
        else:
            try:
                return convert(self['value'], self['unit_text'], units)
            except TypeError:
                return None

    def get_error_positive(self, units: Optional[str]=None) -> float:
        """Get positive error in specified units.

        Args:
            units: Can be set to the desired unit (see
                :func:`~pdg.units.convert` for supported units). If unspecified,
                the positive error is returned without conversion in the default
                units for this quantity.

        Returns:
            Positive error, or `None` if there is no positive error in the
            database or if the unit conversion is invalid or unsupported.
        """
        if units is None:
            return self['error_positive']
        else:
            return convert(self['error_positive'], self['unit_text'], units)

    def get_error_negative(self, units: Optional[str]=None) -> float:
        """Get negative error in specified units.

        Args:
            units: Can be set to the desired unit (see
                :func:`~pdg.units.convert` for supported units). If unspecified,
                the negative error is returned without conversion in the default
                units for this quantity.

        Returns:
            Negative error, or `None` if there is no negative error in the
            database or if the unit conversion is invalid or unsupported.
        """
        if units is None:
            return self['error_negative']
        else:
            return convert(self['error_negative'], self['unit_text'], units)

    def get_error(self, units: Optional[str]=None) -> Optional[float]:
        """Get symmetric error in specified units.

        Args:
            units: Can be set to the desired unit (see
                :func:`~pdg.units.convert` for supported units). If unspecified,
                the error is returned without conversion in the default units
                for this quantity.

        Returns:
            Symmetric error as average of positive and negative errors if they
            differ by less than 10% of their average. Otherwise, returns `None`.
            Also returns `None` if the quantity is a limit, or if there is
            otherwise no positive or negative error in the database, or if the
            unit conversion is invalid or unsupported.
        """
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
    def pdgid(self) -> str:
        "PDG Identifier of quantity for which value is given."
        return self['pdgid']

    @property
    def description(self) -> str:
        "Description of quantity for which value is given"
        return self['description']

    @property
    def value_type_key(self) -> str:
        """Type of value, given by its key.

        See :meth:`PdgApi.doc_value_type_keys
        <pdg.api.PdgApi.doc_value_type_keys>` for the meaning of the different
        value type keys.
        """
        return self['value_type']

    @property
    def value_type(self) -> str:
        "Type of value, given as the PDG indicator string."
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
    def in_summary_table(self) -> bool:
        "`True` if value is included in Summary Table."
        return self['in_summary_table']

    @property
    def confidence_level(self) -> Optional[float]:
        "Confidence level for limits, `None` otherwise."
        return self['confidence_level']

    @property
    def is_limit(self) -> bool:
        "`True` if value is a limit."
        return self['confidence_level'] is not None or self['limit_type'] is not None

    @property
    def is_upper_limit(self) -> bool:
        "`True` if value is an upper limit."
        return self['limit_type'] == 'U'

    @property
    def is_lower_limit(self) -> bool:
        "`True` if value is an lower limit."
        return self['limit_type'] == 'L'

    @property
    def comment(self) -> str:
        "Details for or comments on this value."
        return self['comment']

    @property
    def value(self) -> float:
        """Numerical value in units given by property :attr:`units`.

        Check properties :attr:`is_limit`, :attr:`is_lower_limit` and
        :attr:`is_upper_limit` to determine if value is a central value or limit.
        """
        return self['value']

    @property
    def error_positive(self) -> float:
        """Numerical value of positive error in units given by property
        :attr:`units`.
        """
        return self['error_positive']

    @property
    def error_negative(self) -> float:
        """Numerical value of negative error in units given by property
        :attr:`units`.
        """
        return self['error_negative']

    @property
    def error(self) -> Optional[float]:
        """Symmetric error or `None`.

        The symmetric error is the average of positive and negative errors if
        they differ by less than 10% of their average. If not, or if the
        quantity is a limit, the symmetric error is `None`.
        """
        return self.get_error()

    @property
    def scale_factor(self) -> float:
        """PDG error scale factor that was applied to :attr:`error_positive` and
        :attr:`error_negative`.
        """
        return self['scale_factor'] or 1.0

    @property
    def units(self) -> str:
        """Units (in plain text format) used by :attr:`value`,
        :attr:`error_positive`, :attr:`error_negative`, and
        :attr:`display_value_text`.
        """
        return self['unit_text']

    # @property
    # def units_tex(self):
    #     """Units (in TeX format) used by :attr:`value`,
    #     :attr:`error_positive`, :attr:`error_negative`, and
    #     :attr:`display_value_text`.
    #     """
    #     return self['unit_tex']

    @property
    def value_text(self) -> str:
        """Value and uncertainty (in plain text format) in units given by
        property :attr:`units`, including the power of ten, if applicable
        (see :attr:`display_power_of_ten`)
        """
        return self['value_text']

    # @property
    # def value_tex(self):
    #     """Value and uncertainty (in TeX format) in units given by property
    #     units, including the power of ten, if applicable (see
    #     display_power_of_ten)"""
    #     return self['value_tex']

    @property
    def display_value_text(self) -> str:
        """Value and uncertainty in plain text format as displayed in
           Listings tables. Does not include any power of ten or percent sign.
           Must be combined with the :attr:`display_power_of_ten` property in
           order to obtain the numerical value in units given by the property
           :attr:`units`.
        """
        return self['display_value_text']

    @property
    def display_power_of_ten(self) -> int:
        "Unit multiplier (as power of ten) as used for display in Listings."
        return self['display_power_of_ten']

    @property
    def display_in_percent(self) -> bool:
        """`True` if value is rendered in percent for display in Listings.
        Implies that :attr:`display_power_of_ten` is -2.
        """
        return self['display_in_percent']


class PdgConvertedValue(PdgSummaryValue):
    """A `PdgSummaryValue` subclass for storing summary values after unit conversion.

    After being initialized from some other `PdgSummaryValue`, a
    `PdgConvertedValue` can be treated like any `PdgSummaryValue`. The unit
    conversion will be reflected in all properties relating to the numerical
    value, its errors, and its units.
    """

    def __init__(self, value: PdgSummaryValue, to_units: str):
        """
        Args:
            value: A :class:`~pdg.data.PdgSummaryValue` to convert.
            to_units: The new units. See :func:`~pdg.units.convert`
                for supported units.
        """
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

    When a `PdgData` object is instantiated, the edition of the Review of
    Particle Physics from which data will be retrieved is determined by the
    first edition information found from the following list:

    1. An edition specified as part of the PDG Identifier
    2. An edition specified by parameter `edition` of the constructor
    3. The default edition specified by the database to which the API is connected

    The chosen edition can be queried by calling :func:`edition` and changed
    at any time by calling :func:`set_edition`.
    """
    def __init__(self, api: 'PdgApi', pdgid: str, edition: Optional[str]=None):
        """
        Note:
            In most cases, user code should not need to call the constructor
            directly. Instead, the use of e.g. :meth:`PdgApi.get
            <pdg.api.PdgApi.get>` is recommended.

        Args:
            api: A :class:`~pdg.api.PdgApi` object to be used for retrieving data.
            pdgid: The PDG Identifier for the desired data.
            edition: If set, and if the `pdgid` does not specify the edition, then
                the data will be looked up in this edition.
        """
        self.api = api
        self.baseid, self._edition = parse_id(pdgid)
        if self._edition is None:
            self._edition = edition
        if self._edition is None:
            self._edition = self.api.default_edition
        self.pdgid = make_id(self.baseid, self._edition)
        self.cache: dict[str, dict | list[dict] | list[PdgSummaryValue]] = {}

    def __str__(self) -> str:
        """Get human-readable description of the data.

        Returns:
            Details including the identifier's name and description.
        """
        return 'Data for PDG Identifier %s: %s' % (self.pdgid, self.description)

    def __repr__(self) -> str:
        """Get concise description of the data.

        Returns:
            Details including the class name, the identifier, and any additional
            information specific to a subclass of :class:`PdgData`.
        """
        extra = self._repr_extra()
        if extra:
            extra = ', ' + extra
        return "%s('%s'%s)" % (self.__class__.__name__, make_id(self.baseid, self.edition),
                               extra)

    def _repr_extra(self) -> str:
        """A method that subclasses can override in order to add info to the
        result of :func:`__repr__`.
        """
        return ''

    def _get_pdgid(self) -> dict:
        """Get PDG Identifier information.

        Returns:
            Contents of this data's corresponding row in the SQLite file's
            `pdgid` table. 
        """
        if 'pdgid' not in self.cache:
            pdgid_table = self.api.db.tables['pdgid']
            query = select(pdgid_table).where(pdgid_table.c.pdgid == bindparam('pdgid'))
            with self.api.engine.connect() as conn:
                try:
                    row = conn.execute(query, {'pdgid': self.baseid}).fetchone()
                    assert row is not None
                    self.cache['pdgid'] = dict(row._mapping)
                except AttributeError:
                    raise PdgInvalidPdgIdError('PDG Identifier %s not found' % self.pdgid)
        assert isinstance(self.cache['pdgid'], dict)
        return self.cache['pdgid']

    def _get_summary_values(self) -> list[PdgSummaryValue]:
        """Get all summary data values.

        Returns:
            List of all :class:`PdgSummaryValue` objects for this data.
        """
        if 'summary' not in self.cache:
            pdgid_table = self.api.db.tables['pdgid']
            pdgdata_table = self.api.db.tables['pdgdata']
            query = select(pdgdata_table, pdgid_table.c.description).join(pdgid_table)
            query = query.where(pdgid_table.c.pdgid == bindparam('pdgid'))
            query = query.where(pdgdata_table.c.edition == bindparam('edition'))
            query = query.order_by(pdgdata_table.c.sort)
            summary: list[PdgSummaryValue] = []
            with self.api.engine.connect() as conn:
                for entry in conn.execute(query, {'pdgid': self.baseid, 'edition': self.edition}):
                    summary.append(PdgSummaryValue(entry._mapping))
            self.cache['summary'] = summary
        return cast(list[PdgSummaryValue], self.cache['summary'])

    def _count_data_entries(self, pdgid: str, edition: str) -> int:
        """Count number of data entries for a given PDG identifier and edition.

        Args:
            pdgid: PDG identifier.
            edition: Edition.

        Returns:
            Number of data entries.
        """
        pdgdata_table = self.api.db.tables['pdgdata']
        query = select(func.count("*")).select_from(pdgdata_table)
        query = query.where(pdgdata_table.c.pdgid == bindparam('pdgid'))
        query = query.where(pdgdata_table.c.edition == bindparam('edition'))
        with self.api.engine.connect() as conn:
            count = conn.execute(query, {'pdgid': pdgid.upper(), 'edition': edition}).scalar()
            assert count is not None
            return count

    def get_parent_pdgid(self, include_edition: bool=True) -> Optional[str]:
        """Return PDG Identifier of this data's parent.

        In most cases, this will be the PDG ID of the particle itself. For those
        properties, such as neutrino mixing angles, that don't have a specific
        parent particle, the parent will be a top-level section (`S067` in this
        case). If this property's direct parent is a subsection header, it will
        be skipped, and the PDG Identifier of the top-level section or particle
        will be returned instead.

        Args:
            include_edition: Whether to include the edition when formatting the
                PDG Identifier.

        Returns:
            PDG Identifier of this property's parent.
        """
        if self._get_pdgid()['parent_pdgid'] is None:
            return None
        p = self
        while p._get_pdgid()['parent_pdgid'] is not None:
            p = self.api.get(p._get_pdgid()['parent_pdgid'], self.edition)
        return p.pdgid if include_edition else p.baseid

    def get_particles(self) -> 'PdgParticleList':
        """Get `PdgParticleList` for this property's particle.

        Raises:
            :exc:`~pdg.errors.PdgNoDataError`: If the identifier does not have
                any parent particles.

        Returns:
            All parent particles for this property.
        """
        parent = self.get_parent_pdgid()
        if parent is not None:
            p = self.api.get(parent)
            if p.data_type == 'PART':
                return cast('PdgParticleList', p)
        err = f'Identifier {self.pdgid} does not have a parent particle'
        raise PdgNoDataError(err)

    def get_particle(self) -> 'PdgParticle':
        """Get `PdgParticle` for this property's particle.

        Raises:
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If there are multiple matches.

        Returns:
            The parent particle for this property.
        """
        ps = self.get_particles()
        assert len(ps) > 0
        if len(ps) > 1:
            err = "More than one PdgParticle found. Consider using get_particles() instead."
            raise PdgAmbiguousValueError(err)
        return ps[0]

    def get_children(self, recurse: bool=False) -> Iterator['PdgData']:
        """Get all properties that descend from this one.

        Args:
            recurse: Whether to scan recursively and return grandchildren, etc.

        Returns:
            Iterator over descendent properties.
        """
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
    def edition(self) -> Optional[str]:
        "Year of edition for which data is requested."
        return self._edition

    @edition.setter
    def edition(self, edition: str) -> None:
        "Set year of edition used for retrieving data (invalidates cache)."
        self._edition = edition
        self.pdgid = make_id(self.baseid, self._edition)
        self.cache = dict()

    @property
    def description(self) -> str:
        "Description of data."
        return self._get_pdgid()['description']

    @property
    def data_type(self) -> str:
        "Type of data."
        return self._get_pdgid()['data_type']

    @property
    def data_flags(self) -> str:
        "Flags augmenting data type information."
        return self._get_pdgid()['flags']

    @property
    def cp_charge_flag(self) -> Optional[int]:
        """The particular "CP charge" that this data corresponds to.

        See :attr:`PdgParticle.cp_charge <pdg.particle.PdgParticle.cp_charge>`
        documentation for the meaning of the "CP charge". This flag will be `None`
        if the data applies to ALL particles listed under the PDG identifier.
        """
        digits = [c for c in self.data_flags if c.isdigit()]
        if len(digits) == 0:
            return None
        assert len(digits) == 1
        mag = int(digits[0])
        if mag != 0:
            assert ('+' in self.data_flags) ^ ('-' in self.data_flags)
        sign = -1 if '-' in self.data_flags else 1
        return sign * mag


class PdgProperty(PdgData):
    "Base class for containers for data containers for particle properties."

    def summary_values(self, summary_table_only: bool=False) -> list[PdgSummaryValue]:
        """Get list of summary values for this quantity.

        Args:
            summary_table_only: Whether to get only summary values listed in the
                Summary Tables. By default, all summary values are included,
                even if they are only shown in the Particle Listings and not
                listed in the Summary Tables.

        Returns:
            List of summary values.
        """
        if summary_table_only:
            return [v for v in self._get_summary_values() if v.in_summary_table]
        else:
            return self._get_summary_values()

    def n_summary_table_values(self) -> int:
        "Get number of summary values in Summary Table for this quantity."
        return len(self.summary_values(summary_table_only=True))

    def best_summary(self, summary_table_only: bool=False) \
            -> Optional[PdgSummaryValue]:
        """Get the PDG "best" summary value for this quantity.

        If there is either a single summary value in Particle Listings and
        Summary Tables, or there are multiple summary values but only one is
        included in the Summary Tables, then this value is returned as the PDG
        best value.

        If there are multiple summary values (e.g. based on assuming or not
        assuming CPT in the evaluation) and the API is not in pedantic mode, the
        first value shown in Summary Tables or Particle Listings will be
        returned. In pedantic mode, a :exc:`~pdg.errors.PdgAmbiguousValueError`
        exception will be raised.

        If there are no summary values, `None` is returned.

        Args:
            summary_table_only: If `True`, then the best value must be included
                in the Summary Table and cannot be shown only in the Particle
                Listings.

        Returns:
             "Best" summary value, or `None` (see above).

        Raises:
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If the API is in pedantic
                mode and there are multiple relevant summary values.
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

    def has_best_summary(self, summary_table_only: bool=False) -> bool:
        """Query whether there is a single PDG "best" value for this property.

        See documentation of :func:`best_summary` for definition of "best".

        Args:
            summary_table_only: If `True`, then the best value must be included
                in the Summary Table and cannot be shown only in the Particle
                Listings.

        Returns:
            `True` if there is exactly one "best" value. 
        """
        try:
            return self.best_summary(summary_table_only) is not None
        except PdgAmbiguousValueError:
            return False

    def get_measurements(self) -> Iterator[PdgMeasurement]:
        "Get all of the measurements associated with this property."
        pdgmsmt_table = self.api.db.tables['pdgmeasurement']
        query = select(pdgmsmt_table.c.id)
        query = query.where(pdgmsmt_table.c.pdgid == bindparam('pdgid'))
        with self.api.engine.connect() as conn:
            for entry in conn.execute(query, {'pdgid': self.baseid}):
                yield PdgMeasurement(self.api, entry.id)

    @property
    def num_measurements(self) -> int:
        "Get the number of measurements associated with this property."
        pdgmsmt_table = self.api.db.tables['pdgmeasurement']
        query = select(func.count('*'))
        query = query.where(pdgmsmt_table.c.pdgid == bindparam('pdgid'))
        with self.api.engine.connect() as conn:
            row = conn.execute(query, {'pdgid': self.baseid}).fetchone()
            assert row is not None
            return row[0]

    @property
    def confidence_level(self) -> Optional[float]:
        "Shortcut for `best_summary().confidence_level`."
        best = self.best_summary()
        assert best is not None
        return best.confidence_level

    @property
    def is_limit(self) -> bool:
        "Shortcut for `best_summary().is_limit`."
        best = self.best_summary()
        assert best is not None
        return best.is_limit

    @property
    def value(self) -> float:
        "Shortcut for `best_summary().value`."
        best = self.best_summary()
        assert best is not None
        return best.value

    @property
    def error(self) -> Optional[float]:
        "Shortcut for `best_summary().error`."
        best = self.best_summary()
        assert best is not None
        return best.error

    @property
    def error_positive(self) -> float:
        "Shortcut for `best_summary().error`."
        best = self.best_summary()
        assert best is not None
        return best.error_positive

    @property
    def error_negative(self) -> float:
        "Shortcut for `best_summary().error`."
        best = self.best_summary()
        assert best is not None
        return best.error_negative

    @property
    def scale_factor(self) -> float:
        "Shortcut for `best_summary().scale_factor`."
        best = self.best_summary()
        assert best is not None
        return best.scale_factor

    @property
    def units(self) -> str:
        "Shortcut for `best_summary().units`."
        best = self.best_summary()
        assert best is not None
        return best.units

    @property
    def comment(self) -> str:
        "Shortcut for `best_summary().comment`."
        best = self.best_summary()
        assert best is not None
        return best.comment

    @property
    def value_text(self) -> str:
        "Shortcut for `best_summary().value_text`."
        best = self.best_summary()
        assert best is not None
        return best.value_text

    @property
    def display_value_text(self) -> str:
        "Shortcut for `best_summary().display_value_text`."
        best = self.best_summary()
        assert best is not None
        return best.display_value_text


class PdgMass(PdgProperty):
    "A `PdgProperty` subclass representing a particle's mass."
    pass


class PdgWidth(PdgProperty):
    "A `PdgProperty` subclass representing a particle's decay width."
    pass


class PdgLifetime(PdgProperty):
    "A `PdgProperty` subclass representing a particle's lifetime."
    pass


class PdgText(PdgData):
    """A `PdgData` subclass representing a generic text.

    Used e.g. to represent subsection headings.
    """
    pass
