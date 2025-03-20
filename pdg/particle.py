"""
Definition of top-level particle container class.
"""

from sqlalchemy import select, bindparam, distinct, func
from sqlalchemy import and_, or_
from pdg.errors import PdgApiError, PdgNoDataError, PdgAmbiguousValueError
from pdg.utils import make_id, best
from pdg.data import PdgData
from pdg.units import HBAR_IN_GEV_S


class PdgItem:
    """A class to represent an "item" encountered in e.g. a description of a
    decay's products. An item can correspond directly to one particle,
    indirectly to one particle (as an alias), to a set of particles (as a
    generic name), or to an arbitrary string. When possible, a PdgItem can be
    queried (via the particle/particles properties) for the associated
    particle(s).
    """
    def __init__(self, api, pdgitem_id, edition=None):
        """Constructor for a PdgItem. Intended for internal API use."""
        self.api = api
        self.pdgitem_id = pdgitem_id
        self.cache = {}
        self.edition = edition

    def __repr__(self):
        """Return a human-readable representation of the PdgItem."""
        name = self._get_pdgitem()['name']
        return 'PdgItem("%s")' % name

    def _get_pdgitem(self):
        """Load the PdgItem's data from the database."""
        if 'pdgitem' not in self.cache:
            pdgitem_table = self.api.db.tables['pdgitem']
            query = select(pdgitem_table).where(pdgitem_table.c.id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result is None:
                    raise PdgNoDataError('No PDGITEM entry for %s' % self.pdgitem_id)
                self.cache['pdgitem'] = result._mapping
        return self.cache['pdgitem']

    def _get_targets(self):
        """Get all PdgItems that this one maps directly to. Does not recurse."""
        pdgitem_map_table = self.api.db.tables['pdgitem_map']
        query = select(pdgitem_map_table).where(pdgitem_map_table.c.pdgitem_id == bindparam('pdgitem_id'))
        with self.api.engine.connect() as conn:
            rows = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchall()
            for row in rows:
                yield PdgItem(self.api, row.target_id)

    @property
    def has_particle(self):
        """Whether the PdgItem is associated with exactly one particle. The
        property has_particles indicates whether it is associated with one or
        more.
        """
        if 'has_particle' not in self.cache:
            pdgparticle_table = self.api.db.tables['pdgparticle']
            query = select(pdgparticle_table).where(pdgparticle_table.c.pdgitem_id == bindparam('pdgitem_id'))
            with self.api.engine.connect() as conn:
                result = conn.execute(query, {'pdgitem_id': self.pdgitem_id}).fetchone()
                if result:
                    self.cache['pdgparticle'] = result._mapping
                    self.cache['has_particle'] = True
                else:
                    targets = list(self._get_targets())
                    if len(targets) == 1 and targets[0].has_particle:
                        self.cache['pdgparticle'] = targets[0].cache['pdgparticle']
                        self.cache['has_particle'] = True
                    else:
                        self.cache['has_particle'] = False
        return self.cache['has_particle']

    @property
    def particle(self):
        """The particle associated with the PdgItem, if there is exactly one
        such particle. Raises PdgAmbiguousValueError if there are more than one,
        in which case the particles property can be used instead.
        """
        if not self.has_particle:
            if self.has_particles:
                raise PdgAmbiguousValueError('No unique PDGPARTICLE for PDGITEM %s' % self.pdgitem_id)
            raise PdgNoDataError('No PDGPARTICLE for PDGITEM %s' % self.pdgitem_id)
        p = self.cache['pdgparticle']
        return PdgParticle(self.api, p['pdgid'], edition=self.edition, set_mcid=p['mcid'],
                           set_name=p['name'])

    @property
    def particles(self):
        """The list of all particles associated with the PdgItem."""
        if self.has_particle:
            return [self.particle]
        else:
            result = []
            for target in self._get_targets():
                for p in target.particles:
                    result.append(p)
            return result

    @property
    def has_particles(self):
        """Whether the PdgItem is associated with at least one particle."""
        return len(list(self.particles)) > 0

    @property
    def name(self):
        """The name of the PdgItem."""
        return self._get_pdgitem()['name']

    # @property
    # def name_tex(self):
    #     """The TeX name of the PdgItem."""
    #     return self._get_pdgitem()['name_tex']

    @property
    def item_type(self):
        """The type of the PdgItem. A single character with the following meanings:
              'P': specific state (e.g. "pi+"),
              'A': "also" alias,
              'W': "was" alias,
              'S': shortcut,
              'B': both charges (e.g. "pi+-"),
              'C': both charges, conjugate (e.g. "pi-+"),
              'G': generic state (e.g. "pi"),
              'L': general list (e.g. "leptons"),
              'I': inclusive indicator (e.g. "X"),
              'T': arbitrary text
        """
        return self._get_pdgitem()['item_type']


class PdgParticle(PdgData):
    """Container class for all information about a given particle.

    In addition to access to basic particle properties such as mass, charge, quantum numbers and
    PDG MC ID, this class provides methods to iterate over the data on all particle properties listed
    in Particle Listings and Summary Tables, including branching fractions, masses, life-times, etc.
    """

    def __init__(self, api, pdgid, edition=None, set_mcid=None, set_name=None):
        """Constructor for a PdgParticle given its PDG Identifier and possibly its MC ID."""
        super(PdgParticle, self).__init__(api, pdgid, edition)
        self.set_mcid = set_mcid
        self.set_name = set_name

    def __str__(self):
        try:
            return 'Data for PDG Particle %s: %s' % (self.pdgid, self.name)
        except PdgAmbiguousValueError:
            return 'Data for PDG Particle %s: multiple particle matches' % self.pdgid

    def _repr_extra(self):
        return "name='%s'" % self.name

    def _get_particle_data(self):
        """Get particle data."""
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
                self.cache['pdgparticle'] = matches[0]._mapping
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
                    self.cache['pdgparticle'] = matches_g[0]._mapping
                else:
                    names = [p.name for p in matches_g]
                    mcids = list(set([p.mcid for p in matches]))
                    raise PdgAmbiguousValueError('Multiple particles for %s: MCID %s, names %s' % (self.baseid, mcids, names))
        return self.cache['pdgparticle']

    def properties(self,
                   data_type_key=None,
                   require_summary_data=True,
                   in_summary_table=None,
                   omit_branching_ratios=False):
        """Return iterator over specified particle property data.

        By default, all properties excluding branching fractions and branching fraction ratios are returned.

        data_type_key can be set to select specific properties. Possible keys are given by the list printed
        by PdgApi.doc_data_type_keys. The SQL wildcard character ('%') is allowed, so to select all properties,
        including branching fractions and ratios, set data_type_key='%'. As another example, to get all mass
        properties, use data_type_key='M'.

        require_summary_data can be set False to also include properties, where the selected edition of the Review
        of Particle Physics has no summary value(s) in Particle Listings or Summary Table.

        in_summary_table can be set to select properties, where a summary value is (True) or is not (False) included
        in the Summary Table for the selected edition. Setting in_summary_table to a value other than None
        implies require_summary_data=True.

        omit_branching_ratios can be set to True to exclude any branching fraction ratio properties that would
        be selected otherwise.
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


    def masses(self, require_summary_data=True):
        """Return iterator over mass data.

        For most particles, there is only a single mass property, and so the particle's
        PDG best mass value in GeV can be obtained e.g. from

        list(some_particle.masses())[0].best_value_in_GeV()

        For other particles (e.g. for the top quark) there are different ways to determine the mass and the user
        needs to decide which mass value is the most appropriate for their use case.
        """
        return self.properties('M', require_summary_data)

    def widths(self, require_summary_data=True):
        """Return iterator over width data."""
        return self.properties('G', require_summary_data)

    def lifetimes(self, require_summary_data=True):
        """Return iterator over lifetime data."""
        return self.properties('T', require_summary_data)

    def branching_fractions(self, data_type_key='BF%', require_summary_data=True):
        """Return iterator over given type(s) of branching fraction data.

        With data_type_key='BF%' (default), all branching fractions, including subdecay modes, are returned.

        require_summary_data can be set False to include branching fractions where the current edition has no
        summary value(s) in the Particle Listings or Summary Table.
        """
        if data_type_key[0:2] != 'BF':
            raise PdgApiError('illegal branching fraction data type key %s' % data_type_key)
        return self.properties(data_type_key, require_summary_data)

    def exclusive_branching_fractions(self, include_subdecays=False, require_summary_data=True):
        """Return iterator over exclusive branching fraction data.

        Set include_subdecays to True (default is False) to also include
        subdecay modes (i.e. modes shown indented in the Summary Tables).

        require_summary_data can be set False to include branching fractions where the current edition has
        no summary value(s) in the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFX%', require_summary_data)
        else:
            return self.branching_fractions('BFX', require_summary_data)

    def inclusive_branching_fractions(self, include_subdecays=False, require_summary_data=True):
        """Return iterator over inclusive branching fraction data.

        Set include_subdecays to True (default is False) to also include
        subdecay modes (i.e. modes shown indented in the Summary Tables).

        require_summary_data can be set True to request only branching fractions where the current edition has
        summary value(s) in the Particle Listings or Summary Table.
        """
        if include_subdecays:
            return self.branching_fractions('BFI%', require_summary_data)
        else:
            return self.branching_fractions('BFI', require_summary_data)

    @property
    def name(self):
        """Name of particle (ASCII format)."""
        return self._get_particle_data()['name']

    @property
    def mcid(self):
        """Monte Carlo ID of particle."""
        return self._get_particle_data()['mcid']

    @property
    def charge(self):
        """Charge of particle in units of e."""
        return self._get_particle_data()['charge']

    @property
    def quantum_I(self):
        """Quantum number I (isospin) of particle."""
        return self._get_particle_data()['quantum_i']

    @property
    def quantum_G(self):
        """Quantum number G (G parity) of particle."""
        return self._get_particle_data()['quantum_g']

    @property
    def quantum_J(self):
        """Quantum number J (spin) of particle."""
        return self._get_particle_data()['quantum_j']

    @property
    def quantum_P(self):
        """Quantum number P (parity) of particle."""
        return self._get_particle_data()['quantum_p']

    @property
    def quantum_C(self):
        """Quantum number C (C parity) of particle."""
        return self._get_particle_data()['quantum_c']

    @property
    def is_boson(self):
        """True if particle is a gauge boson."""
        return 'G' in self.data_flags

    @property
    def is_quark(self):
        """True if particle is a quark."""
        return 'Q' in self.data_flags

    @property
    def is_lepton(self):
        """True if particle is a lepton."""
        return 'L' in self.data_flags

    @property
    def is_meson(self):
        """True if particle is a meson."""
        return 'M' in self.data_flags

    @property
    def is_baryon(self):
        """True if particle is a baryon."""
        return 'B' in self.data_flags

    @staticmethod
    def _if_not_limit(prop, units, error=False):
        """If a PdgProperty's best summary value is NOT a limit, return it in
        the specified units. Otherwise return None. If error is True, return the
        error instead of the value.
        """
        summary = prop.best_summary()
        if summary.is_limit:
            return None
        if error:
            return summary.get_error(units)
        return summary.get_value(units)

    @property
    def mass(self):
        """Mass of the particle in GeV."""
        best_mass_property = best(self.masses(), self.api.pedantic, '%s mass (%s)' % (self.name, self.pdgid))
        return self._if_not_limit(best_mass_property, 'GeV')

    @property
    def mass_error(self):
        """Symmetric error on mass of particle in GeV, or None if mass error are asymmetric or mass is a limit."""
        best_mass_property = best(self.masses(), self.api.pedantic, '%s (%s)' % (self.pdgid, self.description))
        return self._if_not_limit(best_mass_property, 'GeV', error=True)

    @property
    def width(self):
        """Width of the particle in GeV."""
        try:
            best_width_property = best(self.widths(), self.api.pedantic, '%s width (%s)' % (self.name, self.pdgid))
            return self._if_not_limit(best_width_property, 'GeV')
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            # S063 has a lifetime entry but it's NULL
            if (not self.has_lifetime_entry) or (self.lifetime is None):
                return 0.
            return HBAR_IN_GEV_S / self.lifetime

    @property
    def width_error(self):
        """Symmetric error on width of particle in GeV, or None if width error are asymmetric or width is a limit."""
        try:
            best_width_property = best(self.widths(), self.api.pedantic, '%s (%s)' % (self.pdgid, self.description))
            return self._if_not_limit(best_width_property, 'GeV', error=True)
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            # S063 has a lifetime entry but it's NULL
            if (not self.has_lifetime_entry) or (self.lifetime is None):
                return 0.
            return self.lifetime_error * HBAR_IN_GEV_S / self.lifetime**2

    @property
    def lifetime(self):
        """Lifetime of the particle in seconds."""
        try:
            best_lifetime_property = best(self.lifetimes(), self.api.pedantic, '%s lifetime (%s)' % (self.name, self.pdgid))
            return self._if_not_limit(best_lifetime_property, 's')
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            if not self.has_width_entry:
                return float('inf')
            return HBAR_IN_GEV_S / self.width

    @property
    def lifetime_error(self):
        """Symmetric error on lifetime of particle in seconds, or None if lifetime error are asymmetric or lifetime is a limit."""
        try:
            best_lifetime_property = best(self.lifetimes(), self.api.pedantic, '%s (%s)' % (self.pdgid, self.description))
            err = self._if_not_limit(best_lifetime_property, 's', error=True)
            if err is None:
                err = 0.
            return err
        except PdgNoDataError:
            if self.api.pedantic:
                raise
            if not self.has_width_entry:
                return 0.
            return self.width_error * HBAR_IN_GEV_S / self.width**2

    @property
    def has_mass_entry(self):
        """Whether the particle has at least one defined mass."""
        return next(self.masses(), None) is not None

    @property
    def has_width_entry(self):
        """Whether the particle has at least one defined decay width."""
        return next(self.widths(), None) is not None

    @property
    def has_lifetime_entry(self):
        """Whether the particle has at least one defined lifetime."""
        return next(self.lifetimes(), None) is not None

    def mass_measurements(self, require_summary_data=True):
        for m in self.masses(require_summary_data=require_summary_data):
            for msmt in m.get_measurements():
                yield msmt

    def lifetime_measurements(self, require_summary_data=True):
        for t in self.lifetimes(require_summary_data=require_summary_data):
            for msmt in t.get_measurements():
                yield msmt

    def width_measurements(self, require_summary_data=True):
        for g in self.widths(require_summary_data=require_summary_data):
            for msmt in g.get_measurements():
                yield msmt


class PdgParticleList(PdgData, list):
    """A PdgData subclass to represent a list of PdgParticles. A PdgParticleList
    is returned when PdgApi.get is called with the PDGID of a (group of)
    particles.
    """
    def __init__(self, api, pdgid, edition=None):
        """Constructor for a PdgParticleList given its PDG Identifier."""
        super(PdgParticleList, self).__init__(api, pdgid, edition)

        pdgparticle_table = self.api.db.tables['pdgparticle']
        query = select(pdgparticle_table)
        query = query.where(func.lower(pdgparticle_table.c.pdgid) == bindparam('pdgid'))
        with self.api.engine.connect() as conn:
            result = conn.execute(query, {'pdgid': pdgid.lower()}).fetchall()
            for row in result:
                self.append(PdgParticle(api, pdgid, edition=edition, set_mcid=row.mcid,
                                        set_name=row.name))
