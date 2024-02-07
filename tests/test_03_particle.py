"""
Test cases for PdgParticle.
"""
from __future__ import print_function

from pytest import raises

from pdg.errors import PdgAmbiguousValueError, PdgNoDataError


def test_all_particle_data(api):
    n_errors = 0
    for p in api.get_particles():
        try:
            p._get_particle_data()
        except Exception as e:
            n_errors += 1
            print(e)
    assert n_errors == 0

def test_name(api):
    assert api.get_particle_by_name('p').mcid == 2212
    assert api.get_particle_by_name('pbar').mcid == -2212

def test_mcid(api):
    assert api.get_particle_by_mcid(5).name == 'b'
    assert api.get_particle_by_mcid(-5).name == 'bbar'
    assert api.get_particle_by_mcid(5).mcid == 5
    assert api.get_particle_by_mcid(-5).mcid == -5
    assert api.get_particle_by_mcid(11).name == 'e-'
    assert api.get_particle_by_mcid(-11).name == 'e+'
    assert api.get_particle_by_mcid(39).name == 'graviton'
    assert api.get_particle_by_mcid(100211).name == 'pi(1300)+'
    assert api.get_particle_by_mcid(-30323).name == 'K^*(1680)-'
    assert api.get_particle_by_mcid(-30323).mcid == -30323

def test_quantum_P(api):
    assert api.get_particle_by_name('u').quantum_P == '+'
    assert api.get_particle_by_name('ubar').quantum_P == '-'
    assert api.get_particle_by_name('t').quantum_P == '+'
    assert api.get_particle_by_name('tbar').quantum_P == '-'
    assert api.get_particle_by_name('p').quantum_P == '+'
    assert api.get_particle_by_name('pbar').quantum_P == '-'
    assert api.get_particle_by_name('n').quantum_P == '+'
    assert api.get_particle_by_name('nbar').quantum_P == '-'
    assert api.get_particle_by_mcid(3122).quantum_P == '+'
    assert api.get_particle_by_mcid(-3122).quantum_P == '-'

def test_mass_2023(api):
    if '2023' not in api.editions:
        return
    masses = list(api.get('q007/2023').masses())
    assert masses[0].pdgid == 'Q007TP/2023'
    assert round(masses[0].best_summary().value,9) == 172.687433378
    assert masses[1].pdgid == 'Q007TP2/2023'
    assert round(masses[1].best_summary().value,9) == 162.500284698
    assert masses[2].pdgid == 'Q007TP4/2023'
    assert round(masses[2].best_summary().value,9) == 172.463424407
    assert round(api.get('s008/2023').mass,9) == 0.139570391
    assert round(api.get('s008/2023').mass_error,16) == 1.820071604e-07

def test_flags(api):
    assert api.get('S008').is_boson == False
    assert api.get('S008').is_quark == False
    assert api.get('S008').is_lepton == False
    assert api.get('S008').is_meson == True
    assert api.get('S008').is_baryon == False
    assert api.get('q007').is_quark == True
    assert api.get('s000').is_boson == True
    assert api.get('S003').is_lepton == True
    assert api.get('S041').is_meson == True
    assert api.get('S016').is_baryon == True

def test_properties(api):
    assert len(list(api.get('S017').properties('M'))) == 2

def test_ambiguous_defaults(api):
    assert round(api.get('Q007').mass, 1) == 172.7
    assert api.get('S013D').best_summary().comment == 'Assuming CPT'

def test_best_widths_and_lifetimes(api):
    pi0 = api.get_particle_by_name('pi0')
    assert pi0.has_lifetime_entry
    assert not pi0.has_width_entry
    assert round(pi0.lifetime * 1e17, 2) == 8.43
    assert round(pi0.lifetime_error * 1e17, 3) == 0.134
    api.pedantic = True
    with raises(PdgNoDataError):
        pi0.width
    with raises(PdgNoDataError):
        pi0.width_error
    api.pedantic = False
    assert round(pi0.width * 1e9, 2) == 7.81
    assert round(pi0.width_error * 1e9, 3) == 0.125

    W = api.get_particle_by_name('W')
    assert W.has_width_entry
    assert not W.has_lifetime_entry
    assert W.width == 2.085
    assert W.width_error == 0.042
    api.pedantic = True
    with raises(PdgNoDataError):
        W.lifetime
    with raises(PdgNoDataError):
        W.lifetime_error
    api.pedantic = False
    assert round(W.lifetime * 1e25, 2) == 3.16
    assert round(W.lifetime_error * 1e25, 3) == 0.064

def test_Kstar_892(api):
    api.pedantic = False
    p = api.get('M018')
    assert p.is_generic
    assert len(list(p.masses())) == 4
    assert len(list(p.widths())) == 3
    assert list(p.lifetimes()) == []
    with raises(PdgAmbiguousValueError):
        p.mass
    with raises(PdgAmbiguousValueError):
        p.width
    with raises(PdgAmbiguousValueError):
        p.lifetime
    assert p.charge == None

    api.pedantic = True
    p = api.get('M018')
    assert p.is_generic
    assert len(list(p.masses())) == 4
    assert len(list(p.widths())) == 3
    assert list(p.lifetimes()) == []
    with raises(PdgAmbiguousValueError):
        p.mass
    with raises(PdgAmbiguousValueError):
        p.width
    with raises(PdgNoDataError):
        p.lifetime
    assert p.charge == None

    for api.pedantic in [True, False]:
        p = api.get_particle_by_mcid(323)
        assert not p.is_generic
        assert len(list(p.masses())) == 3
        assert len(list(p.widths())) == 2
        assert len(list(p.lifetimes())) == 0
        assert p.charge == 1.0
    api.pedantic = False
    p = api.get_particle_by_mcid(323)
    assert round(p.mass, 3) == 0.892
    assert round(p.width, 4) == 0.0514
    assert round(p.lifetime * 1e23, 2) == 1.28
    api.pedantic = True
    p = api.get_particle_by_mcid(323)
    with raises(PdgAmbiguousValueError):
        p.mass
    with raises(PdgAmbiguousValueError):
        p.width
    with raises(PdgNoDataError):
        p.lifetime

    for api.pedantic in [True, False]:
        p = api.get_particle_by_mcid(-323)
        assert not p.is_generic
        assert len(list(p.masses())) == 3
        assert len(list(p.widths())) == 2
        assert len(list(p.lifetimes())) == 0
        assert p.charge == -1.0
    api.pedantic = False
    p = api.get_particle_by_mcid(-323)
    assert round(p.mass, 3) == 0.892
    assert round(p.width, 4) == 0.0514
    assert round(p.lifetime * 1e23, 2) == 1.28
    api.pedantic = True
    p = api.get_particle_by_mcid(-323)
    with raises(PdgAmbiguousValueError):
        p.mass
    with raises(PdgAmbiguousValueError):
        p.width
    with raises(PdgNoDataError):
        p.lifetime

    for api.pedantic in [True, False]:
        p = api.get_particle_by_mcid(313)
        assert not p.is_generic
        assert len(list(p.masses())) == 2
        assert len(list(p.widths())) == 1
        assert len(list(p.lifetimes())) == 0
        assert p.charge == 0.0
    api.pedantic = False
    p = api.get_particle_by_mcid(313)
    assert round(p.mass, 3) == 0.896
    assert round(p.width, 4) == 0.0473
    assert round(p.lifetime * 1e23, 2) == 1.39
    api.pedantic = True
    p = api.get_particle_by_mcid(313)
    with raises(PdgAmbiguousValueError):
        p.mass
    assert round(p.width, 4) == 0.0473
    with raises(PdgNoDataError):
        p.lifetime
