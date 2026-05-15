"""
Definition of top-level particle container class.
"""

from sqlalchemy import select, bindparam, distinct, func
from sqlalchemy import and_, or_
from pdg.errors import PdgApiError, PdgNoDataError, PdgAmbiguousValueError
from pdg.measurement import PdgMeasurement
from pdg.utils import make_id
from pdg.data import PdgLifetime, PdgMass, PdgWidth, PdgData, PdgProperty
from pdg.units import HBAR_IN_GEV_S
from typing import TYPE_CHECKING, Iterator, Optional, cast

if TYPE_CHECKING:
    from pdg.api import PdgApi
    from pdg.decay import PdgBranchingFraction


class PdgItem:
    """A class to represent an "item" encountered in e.g. a description of a
    decay's products.

    An item can correspond directly to one particle, indirectly to one particle
    (as an alias), to a set of particles (as a generic name), or to an arbitrary
    string. When possible, a `PdgItem` can be queried (via the :attr:`particle`
    and :attr:`particles` properties) for the associated particle(s).
    """
    def __init__(self, api: 'PdgApi', pdgitem_id: int, edition: Optional[str]=None):
        """
        Note:
            The constructor is intended for internal API use.

        Args:
            api: API object for retrieving data.
            pdgitem_id: Primary key of the item in the SQLite file.
            edition: If set, specifies the edition of the RPP
        """
        self.api = api
        self.pdgitem_id = pdgitem_id
        self.cache: dict[str, bool | dict] = {}
        self.edition = edition

    def __repr__(self) -> str:
        "Get a concise representation of the `PdgItem`."
        name = self._get_pdgitem()['name']
        return 'PdgItem("%s")' % name

    def _get_pdgitem(self) -> dict:
        "Load the `PdgItem`'s data from the database."
        if 'pdgitem' not in self.cache:
            pdgitem_table = self.api.db.tables['pdgitem']
            query = select(pdgitem_table).where(pdgitem_table.c.id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result is None:
                    raise PdgNoDataError('No PDGITEM entry for %s' % self.pdgitem_id)
                self.cache['pdgitem'] = dict(result._mapping)
        return cast(dict, self.cache['pdgitem'])

    def _get_targets(self) -> Iterator['PdgItem']:
        "Get all `PdgItem`s that this one maps directly to. Does not recurse."
        pdgitem_map_table = self.api.db.tables['pdgitem_map']
        query = select(pdgitem_map_table).where(pdgitem_map_table.c.pdgitem_id == bindparam('pdgitem_id'))
        with self.api.engine.connect() as conn:
            rows = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchall()
            for row in rows:
                yield PdgItem(self.api, row.target_id)

    @property
    def has_particle(self) -> bool:
        """Whether the `PdgItem` is associated with exactly one particle.

        The property :attr:`has_particles` indicates whether it is associated
        with one or more particles, rather than exactly one.
        """
        if 'has_particle' not in self.cache:
            pdgparticle_table = self.api.db.tables['pdgparticle']
            query = select(pdgparticle_table).where(pdgparticle_table.c.pdgitem_id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result:
                    self.cache['pdgparticle'] = dict(result._mapping)
                    self.cache['has_particle'] = True
                else:
                    targets = list(self._get_targets())
                    if len(targets) == 1 and targets[0].has_particle:
                        self.cache['pdgparticle'] = targets[0].cache['pdgparticle']
                        self.cache['has_particle'] = True
                    else:
                        self.cache['has_particle'] = False
        return cast(bool, self.cache['has_particle'])

    @property
    def particle(self) -> 'PdgParticle':
        """The particle associated with the `PdgItem`, if there is exactly one.

        Raises:
            :exc:`~pdg.errors.PdgAmbiguousValueError`: If there is more than one
                associated particle, in which case the :attr:`particles`
                property can be used instead.
        """
        if not self.has_particle:
            if self.has_particles:
                raise PdgAmbiguousValueError('No unique PDGPARTICLE for PDGITEM %s' % self.pdgitem_id)
            raise PdgNoDataError('No PDGPARTICLE for PDGITEM %s' % self.pdgitem_id)
        p = cast(dict, self.cache['pdgparticle'])
        return PdgParticle(self.api, p['pdgid'], edition=self.edition, set_mcid=p['mcid'],
                           set_name=p['name'])

    @property
    def particles(self) -> list['PdgParticle']:
        """The list of all particles associated with the `PdgItem`.

        The property :attr:`particles` can be used when one expects exactly one
        associated particle.
        """
        if self.has_particle:
            return [self.particle]
        else:
            result = []
            for target in self._get_targets():
                for p in target.particles:
                    result.append(p)
            return result

    @property
    def has_particles(self) -> bool:
        """Whether the `PdgItem` is associated with at least one particle.

        The property :attr:`has_particle` indicates whether it is associated
        with exactly one particle.
        """
        return len(list(self.particles)) > 0

    @property
    def name(self) -> str:
        "The name of the `PdgItem`."
        return self._get_pdgitem()['name']

    @property
    def canonical_name(self) -> str:
        """The canonical name of the unique particle referred to by this `PdgItem`.

        If this item refers to more than one particle, then this is simply equal
        to the :attr:`name` property.
        """
        if self.has_particle:
            return self.particle.name
        return self.name

    # @property
    # def name_tex(self):
    #     "The TeX name of the PdgItem."
    #     return self._get_pdgitem()['name_tex']

    @property
    def item_type(self) -> str:
        """The type of the PdgItem.

        A single character with the following meanings:

        ====  ======================================
        Type  Meaning
        ====  ======================================
        P     Specific state (e.g. "pi+")
        A     "Also" alias
        W     "Was" alias
        S     Shortcut
        B     Both charges (e.g. "pi+-")
        C     Both charges, conjugate (e.g. "pi-+")
        G     Generic state (e.g. "pi")
        L     General list (e.g. "leptons")
        I     Inclusive indicator (e.g. "X")
        T     Arbitrary text
        ====  ======================================
        """
        return self._get_pdgitem()['item_type']


class PdgParticle(PdgData):
    """Container class for all information about a given particle.

    In addition to access to basic particle properties such as mass, charge, quantum numbers and
    MC ID, this class provides methods to iterate over the data on all particle properties listed
    in Particle Listings and Summary Tables, including branching fractions, masses, life-times, etc.
    """

    def __init__(self, api: 'PdgApi', pdgid: str, edition: Optional[str]=None, set_mcid: Optional[int]=None, set_name: Optional[str]=None):
        """
        Args:
            api: PDG API object to be used for retrieving data.
            pdgid: PDG Identifier for this particle (or multiplet, etc.).
            edition: Can be set to a specific edition, from which the data
                should later be retrieved.
            set_mcid: Can be set to a MC ID to select e.g. a particular charge
                state from a multiplet.
            set_name: Can be set to a particle name, similarly to `set_mcid`.
        """
        super(PdgParticle, self).__init__(api, pdgid, edition)
        self.set_mcid = set_mcid
        self.set_name = set_name

    def __str__(self) -> str:
        "Get a human-readable description of the `PdgParticle`"
        try:
            return 'Data for PDG Particle %s: %s' % (self.pdgid, self.name)
        except PdgAmbiguousValueError:
            return 'Data for PDG Particle %s: multiple particle matches' % self.pdgid

    def _repr_extra(self) -> str:
        "Extra details for `__repr__`"
        return "name='%s'" % self.name

    def best(self, properties: Iterator[PdgProperty], quantity: Optional[str]=None) \
            -> PdgProperty:
        """Return the "best" property from an iterable of properties.

        A series of heuristics are used to filter the set of candidates. The
        API's `pedantic` setting determines the degree of ambiguity tolerated.

        Args:
            properties: Iterator over :class:`~pdg.data.PdgProperty` objects to
                choose from.
            quantity: Optional string that describes what was being sought in
                case of error.

        Returns:
            "Best" property. If, after filtering, multiple candidates remain,
            then (unless the API is in pedantic mode) the returned property is
            the one that appears first according to the `sort` column in the
            SQLite file.

        Raises:
            :exc:`PdgNoDataError`: If no property qualifies.
            :exc:`PdgAmbiguousValueError`: If the API is in pedantic mode and
                multiple candidates remain after filtering.
        """
        # filter out "alternative" properties
        props = [p for p in properties if 'A' not in p.data_flags]
        # in non-pedantic mode, filter out "special" values
        if not self.api.pedantic:
            props = [p for p in props if 's' not in p.data_flags]
        # filter out properties that don't have measurements
        # (unless there are no other options; see pi0)
        if len(props) > 1:
            props = [p for p in props if p.num_measurements > 0]

        # if we have any default properties, filter out all the others
        default_props = [p for p in props if 'D' in p.data_flags]
        if default_props:
            props = default_props
        if len(props) == 1:
            return props[0]

        # filter out properties that have the wrong charge magnitude
        props = [p for p in props
                 if (p.cp_charge_flag is None)
                 or (abs(p.cp_charge_flag) == abs(self.charge))]
        if len(props) == 1:
            return props[0]

        # filter out properties that have the wrong "CP charge"
        props = [p for p in props
                 if (p.cp_charge_flag is None)
                 or (p.cp_charge_flag == self.cp_charge)]
        if len(props) == 1:
            return props[0]

        for_what = ' for %s' % quantity if quantity else ''
        if len(props) == 0:
            raise PdgNoDataError('No best property found%s' % for_what)
        else:
            if self.api.pedantic:
                err = 'Ambiguous best property%s' % for_what
                raise PdgAmbiguousValueError(err)
            else:
                return props[0]

    def _get_particle_data(self) -> dict:
        "Get particle data."
        if 'pdgparticle' not in self.cache:
            pdgparticle_table = self.api.db.tables['pdgparticle']
            query = select(pdgparticle_table)
            query = query.where(pdgparticle_table.c.pdgid == bindparam('pdgid'))
            if self.set_mcid is not None:
                query = query.where(pdgparticle_table.c.mcid == bindparam('mcid'))
            if self.set_name is not None:
                query = query.where(pdgparticle_table.c.name == bindparam('name'))
            with self.api.engine.connect() as conn:
                params = {'pdgid': self.baseid, 'mcid': self.set_mcid, 'name': self.set_name}
                matches = conn.execute(query, params).fetchall()
            if len(matches) == 1:
                self.cache['pdgparticle'] = dict(matches[0]._mapping)
            else:
                # Charge-specific state either not found or ambiguous
                query = select(pdgparticle_table)
                query = query.where(pdgparticle_table.c.pdgid == bindparam('pdgid'))
                if self.set_mcid is not None:
                    query = query.where(pdgparticle_table.c.mcid == bindparam('mcid'))
                query = query.where(pdgparticle_table.c.cc_type == 'S')
                query = query.where(pdgparticle_table.c.name.notlike('%bar%'))   # Exclude generic "*bar" states
                with self.api.engine.connect() as conn:
                    params = {'pdgid': self.baseid, 'mcid': self.set_mcid}
                    matches_g = conn.execute(query, params).fetchall()
                if len(matches_g) == 0:
                    mcid_string = ', MC ID = %s' % self.set_mcid if self.set_mcid else ''
                    raise PdgNoDataError('Particle data for %s%s not found' % (self.pdgid, mcid_string))
                elif len(matches_g) == 1:
                    self.cache['pdgparticle'] = dict(matches_g[0]._mapping)
                else:
                    names = [p.name for p in matches_g]
                    mcids = list(set([p.mcid for p in matches]))
                    raise PdgAmbiguousValueError('Multiple particles for %s: MCID %s, names %s' % (self.baseid, mcids, names))
        return cast(dict, self.cache['pdgparticle'])

    def properties(self,
                   data_type_key: Optional[str]=None,
                   require_summary_data: bool=True,
                   in_summary_table: Optional[bool]=None,
                   omit_branching_ratios: bool=False) \
            -> Iterator[PdgData]:
        """Get iterator over specified particle property data.

        By default, all properties excluding branching fractions and branching fraction ratios are returned.

        Args:
            data_type_key: Can be set to select specific properties. Possible
                keys are given by the list printed by
                :meth:`PdgApi.doc_data_type_keys
                <pdg.api.PdgApi.doc_data_type_keys>`. The SQL wildcard character
                ('%') is allowed, so to select all properties, including
                branching fractions and ratios, set `data_type_key` to '%'. As
                another example, to get all mass properties, set
                `data_type_key` to 'M'.
            require_summary_data: Can be set to `False` to also include
                properties where the selected edition of the Review of Particle
                Physics has no summary value(s) in the Particle Listings or
                Summary Table.
            in_summary_table: Can be set to select properties, where a summary
                value is (`True`) or is not (`False`) included in the Summary
                Table for the selected edition. Setting `in_summary_table` to a
                value other than `None` implies that `require_summary_data` is
                `True`.
            omit_branching_ratios: Can be set to `True` to exclude any branching
                fraction ratio properties that would be selected otherwise.

        Returns:
            Iterator over particle property data.
        """
        pdgid_table = self.api.db.tables['pdgid']
        query = select(distinct(pdgid_table.c.pdgid))
        if require_summary_data or in_summary_table is not None:
            pdgdata_table = self.api.db.tables['pdgdata']
            query = query.join(pdgdata_table)
            query = query.where(pdgdata_table.c.edition == bindparam('edition'))
            if in_summary_table is not None:
                query = query.where(pdgdata_table.c.in_summary_table == bindparam('in_summary_table'))
        query = query.where(pdgid_table.c.parent_pdgid.like(bindparam('parent_id')))
        if data_type_key is None:
            # NOTE: like/notlike SQL operators never match null values
            query = query.where((pdgid_table.c.data_type.notlike('BF%')) | (pdgid_table.c.data_type.is_(None)))
            query = query.where((pdgid_table.c.data_type.notlike('BR%')) | (pdgid_table.c.data_type.is_(None)))
        else:
            # NOTE: like may or may not be case-sensitive, depending on database, so use it only for BR* and BF*
            # NOTE: like will not match null values, so data_type='%' must be treated separately
            if '%' in data_type_key:
                if data_type_key != '%':
                    query = query.where(pdgid_table.c.data_type.like(bindparam('data_type_key')))
            else:
                query = query.where(pdgid_table.c.data_type == bindparam('data_type_key'))
            if omit_branching_ratios:
                query = query.where((pdgid_table.c.data_type.notlike('BR%')) | (pdgid_table.c.data_type.is_(None)))
        query = query.order_by(pdgid_table.c.sort)
        with self.api.engine.connect() as conn:
            for entry in conn.execute(query, {'parent_id': self.baseid+'%',
                                              'edition': self.edition,
                                              'data_type_key': data_type_key,
                                              'in_summary_table': in_summary_table}):
                prop = self.api.get(make_id(entry.pdgid, self.edition))

                # For masses, widths, and lifetimes, we must take care to choose
                # the appropriate entry according to the particle's charge.
                # Other types of properties don't require further checks.
                if prop.data_type not in 'MGT':
                    yield prop

                # NOTE: Now that 's' properties are sorted last, we can safely
                # include them without breaking best() etc.

                # If this property is not charge-specific, yield it.
                elif not any(flag in prop.data_flags for flag in '012'):
                    yield prop

                # If this particle isn't a specific charge state, yield
                # everything.
                elif self.charge is None:
                    yield prop

                # Finally check whether the charges match
                elif str(int(abs(self.charge))) in prop.data_flags:
                    yield prop


    def masses(self, require_summary_data: bool=True) -> Iterator[PdgMass]:
        """Get iterator over mass data.

        For most particles, there is only a single mass property. However, for
        some particles (e.g. the top quark) there are different ways to
        determine the mass, and the user needs to decide which mass value is the
        most appropriate for their use case.

        Args:
            require_summary_data: Can be set to `False` to also include
                masses where the selected edition of the Review of Particle
                Physics has no summary value(s) in the Particle Listings or
                Summary Table.
        """
        return cast(Iterator[PdgMass],
                    self.properties('M', require_summary_data))

    def widths(self, require_summary_data: bool=True) -> Iterator[PdgWidth]:
        """Get iterator over width data.

        See :func:`masses` for further commentary.

        Args:
            require_summary_data: Can be set to `False` to also include
                widths where the selected edition of the Review of Particle
                Physics has no summary value(s) in the Particle Listings or
                Summary Table.
        """
        return cast(Iterator[PdgWidth],
                    self.properties('G', require_summary_data))

    def lifetimes(self, require_summary_data: bool=True) -> Iterator[PdgLifetime]:
        """Get iterator over lifetime data.

        See :func:`masses` for further commentary.

        Args:
            require_summary_data: Can be set to `False` to also include
                lifetimes where the selected edition of the Review of Particle
                Physics has no summary value(s) in the Particle Listings or
                Summary Table.
        """
        return cast(Iterator[PdgLifetime],
                    self.properties('T', require_summary_data))

    def branching_fractions(self, data_type_key: str='BF%', require_summary_data: bool=True) \
            -> Iterator['PdgBranchingFraction']:
        """Get iterator over given type(s) of branching fraction data.

        Args:
            data_type_key: Can be set to e.g. 'BFX2' to select only those
                exclusive branching fractions that are two levels deep in the
                subdecay hierarchy. With a `data_type_key` of 'BF%' (the
                default), all branching fractions, including subdecay modes, are
                returned.
            require_summary_data: Can be set `False` to include branching
                fractions where the current edition has no summary value(s) in
                the Particle Listings or Summary Table.
        """
        if data_type_key[0:2] != 'BF':
            raise PdgApiError('illegal branching fraction data type key %s' % data_type_key)
        return cast(Iterator['PdgBranchingFraction'],
                    self.properties(data_type_key, require_summary_data))

    def exclusive_branching_fractions(self, include_subdecays: bool=False, require_summary_data: bool=True) \
            -> Iterator['PdgBranchingFraction']:
        """Get iterator over exclusive branching fraction data.

        Args:
            include_subdecays: Can be set to `True` (default is `False`) to also
                include subdecay modes (i.e. modes shown indented in the Summary
                Tables).
            require_summary_data: Can be set to `False` to include branching
                fractions where the current edition has no summary value(s) in
                the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFX%', require_summary_data)
        else:
            return self.branching_fractions('BFX', require_summary_data)

    def inclusive_branching_fractions(self, include_subdecays: bool=False, require_summary_data: bool=True) \
            -> Iterator['PdgBranchingFraction']:
        """Get iterator over inclusive branching fraction data.

        Args:
            include_subdecays: Can be set to `True` (default is `False`) to also
                include subdecay modes (i.e. modes shown indented in the Summary
                Tables).
            require_summary_data: Can be set to `False` to include branching
                fractions where the current edition has no summary value(s) in
                the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFI%', require_summary_data)
        else:
            return self.branching_fractions('BFI', require_summary_data)

    @property
    def name(self) -> str:
        "Name of particle (ASCII format)."
        return self._get_particle_data()['name']

    @property
    def mcid(self) -> int:
        "Monte Carlo ID of particle."
        return self._get_particle_data()['mcid']

    @property
    def charge(self) -> float:
        "Charge of particle in units of `e`."
        return self._get_particle_data()['charge']

    @property
    def quantum_I(self) -> str:
        "Quantum number I (isospin) of particle."
        return self._get_particle_data()['quantum_i']

    @property
    def quantum_G(self) -> str:
        "Quantum number G (G parity) of particle."
        return self._get_particle_data()['quantum_g']

    @property
    def quantum_J(self) -> str:
        "Quantum number J (spin) of particle."
        return self._get_particle_data()['quantum_j']

    @property
    def quantum_P(self) -> str:
        "Quantum number P (parity) of particle."
        return self._get_particle_data()['quantum_p']

    @property
    def quantum_C(self) -> str:
        "Quantum number C (C parity) of particle."
        return self._get_particle_data()['quantum_c']

    @property
    def is_boson(self) -> bool:
        "`True` if particle is a gauge boson."
        return 'G' in self.data_flags

    @property
    def is_quark(self) -> bool:
        "`True` if particle is a quark."
        return 'Q' in self.data_flags

    @property
    def is_lepton(self) -> bool:
        "`True` if particle is a lepton."
        return 'L' in self.data_flags

    @property
    def is_meson(self) -> bool:
        "`True` if particle is a meson."
        return 'M' in self.data_flags

    @property
    def is_baryon(self) -> bool:
        "`True` if particle is a baryon."
        return 'B' in self.data_flags

    @staticmethod
    def _if_not_limit(prop: PdgProperty, units: str, error: bool=False) -> Optional[float]:
        """Helper used by :attr:`mass`, etc.

        Args:
            prop: The `PdgProperty` in question.
            units: Units to convert the value into.
            error: If `True`, return the error instead of the value.

        Returns:
            If `prop's best summary value is NOT a limit, return it in the
            specified units. Otherwise return `None`. If `error` is `True`,
            return the error instead of the value.
        """
        summary = prop.best_summary()
        assert summary is not None
        if summary.is_limit:
            return None
        if error:
            return summary.get_error(units)
        return summary.get_value(units)

    @property
    def mass(self) -> Optional[float]:
        "Mass of the particle in GeV."
        best_mass_property = self.best(self.masses(), '%s mass (%s)' % (self.name, self.pdgid))
        return self._if_not_limit(best_mass_property, 'GeV')

    @property
    def mass_error(self) -> Optional[float]:
        """Symmetric error on mass of particle in GeV, or `None` if mass error are
        asymmetric or mass is a limit.
        """
        best_mass_property = self.best(self.masses(), '%s (%s)' % (self.pdgid, self.description))
        return self._if_not_limit(best_mass_property, 'GeV', error=True)

    @property
    def width(self) -> Optional[float]:
        "Width of the particle in GeV."
        try:
            best_width_property = self.best(self.widths(), '%s width (%s)' % (self.name, self.pdgid))
            return self._if_not_limit(best_width_property, 'GeV')
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            # S063 has a lifetime entry but it's NULL
            if (not self.has_lifetime_entry) or (self.lifetime is None):
                return 0.
            return HBAR_IN_GEV_S / self.lifetime

    @property
    def width_error(self) -> Optional[float]:
        """Symmetric error on width of particle in GeV, or `None` if width error
        are asymmetric or width is a limit.
        """
        try:
            best_width_property = self.best(self.widths(), '%s (%s)' % (self.pdgid, self.description))
            return self._if_not_limit(best_width_property, 'GeV', error=True)
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            # S063 has a lifetime entry but it's NULL
            if (not self.has_lifetime_entry) or (self.lifetime is None):
                return 0.
            err = self.lifetime_error
            if err is None:
                return None
            return err * HBAR_IN_GEV_S / self.lifetime**2

    @property
    def lifetime(self) -> Optional[float]:
        """Lifetime of the particle in seconds.

        Returns:
            Lifetime, or `None` if there is no best lifetime property and the
            API is not in pedantic mode. In non-pedantic mode, if there is no
            lifetime data, then the decay width will be used, if available. If
            there is no width data either, then the particle is assumed to be
            stable and a lifetime of infinity will be returned.

        Raises:
            :exc:`~pdg.errors.PdgNoDataError`: If there is no best lifetime
                and the API is in pedantic mode.
        """
        try:
            best_lifetime_property = self.best(self.lifetimes(), '%s lifetime (%s)' % (self.name, self.pdgid))
            return self._if_not_limit(best_lifetime_property, 's')
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            width = self.width
            if width is None:
                return float('inf')
            return HBAR_IN_GEV_S / width

    @property
    def lifetime_error(self) -> Optional[float]:
        """Symmetric error on lifetime of particle in seconds

        Returns:
            Lifetime error, or `None` if lifetime error are asymmetric or
            lifetime is a limit.

        Raises:
            :exc:`~pdg.errors.PdgNoDataError`: If there is no best lifetime
                and the API is in pedantic mode.
        """
        try:
            best_lifetime_property = self.best(self.lifetimes(), '%s (%s)' % (self.pdgid, self.description))
            err = self._if_not_limit(best_lifetime_property, 's', error=True)
            if err is None:
                err = 0.
            return err
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            if not self.has_width_entry:
                return 0.
            width, err = self.width, self.width_error
            if width is None or err is None:
                return None
            return err * HBAR_IN_GEV_S / width**2

    @property
    def has_mass_entry(self) -> bool:
        "Whether the particle has at least one defined mass."
        return next(self.masses(), None) is not None

    @property
    def has_width_entry(self) -> bool:
        "Whether the particle has at least one defined decay width."
        return next(self.widths(), None) is not None

    @property
    def has_lifetime_entry(self) -> bool:
        "Whether the particle has at least one defined lifetime."
        return next(self.lifetimes(), None) is not None

    @property
    def cp_charge(self) -> int:
        """The charge of the nominal "particle" (as opposed to "antiparticle")
        for this species.

        E.g., for the proton and antiproton, this is 1. Useful for
        distinguishing e.g. the `Sigma_b()+` (and `Sigmabar_b()-`) from the
        `Sigma_b()-` (and `Sigmabar_b()+`).
        """
        cc_type = self._get_particle_data()['cc_type']
        assert cc_type in ['S', 'P', 'A']
        sign = -1 if cc_type == 'A' else 1
        return sign * int(self.charge)

    def mass_measurements(self, require_summary_data: bool=True) \
            -> Iterator[PdgMeasurement]:
        "Get iterator over all mass measurements for this particle."
        for m in self.masses(require_summary_data=require_summary_data):
            for msmt in m.get_measurements():
                yield msmt

    def lifetime_measurements(self, require_summary_data: bool=True) \
            -> Iterator[PdgMeasurement]:
        "Get iterator over all lifetime measurements for this particle."
        for t in self.lifetimes(require_summary_data=require_summary_data):
            for msmt in t.get_measurements():
                yield msmt

    def width_measurements(self, require_summary_data: bool=True) \
            -> Iterator[PdgMeasurement]:
        "Get iterator over all decay width measurements for this particle."
        for g in self.widths(require_summary_data=require_summary_data):
            for msmt in g.get_measurements():
                yield msmt

    @property
    def self_conjugate(self) -> bool:
        "Whether this particle is self-conjugate."
        cc_type = self._get_particle_data()['cc_type']
        return cc_type == 'S'

    @property
    def antiparticle(self) -> PdgParticle:
        "This particle's antiparticle (or itself, if self-conjugate)"
        if self.self_conjugate:
            return self
        return PdgParticle(self.api, self.pdgid, edition=self.edition,
                           set_mcid=-self.mcid)


class PdgParticleList(PdgData, list):
    """A `PdgData` subclass to represent a list of `PdgParticle` object.

    A `PdgParticleList` is returned when :meth:`PdgApi.get <pdg.api.PdgApi.get>`
    is called with the PDG Identifier of a (group of) particles.
    """
    def __init__(self, api: 'PdgApi', pdgid: str, edition: Optional[str]=None):
        """
        Note:
            The constructor is intended for internal API use.

        Args:
            api: API object for retrieving data.
            pdgitem_id: Primary key of the item in the SQLite file.
            edition: If set, specifies the edition of the RPP
        """
        super(PdgParticleList, self).__init__(api, pdgid, edition)

        pdgparticle_table = self.api.db.tables['pdgparticle']
        query = select(pdgparticle_table)
        query = query.where(func.lower(pdgparticle_table.c.pdgid) == bindparam('pdgid'))
        with self.api.engine.connect() as conn:
            result = conn.execute(query, {'pdgid': pdgid.lower()}).fetchall()
            for row in result:
                self.append(PdgParticle(api, pdgid, edition=edition, set_mcid=row.mcid,
                                        set_name=row.name))
