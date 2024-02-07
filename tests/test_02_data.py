"""
Test cases for the PDG data.
"""
from __future__ import print_function

from pytest import raises

from pdg.errors import PdgInvalidPdgIdError
from pdg.data import PdgConvertedValue, PdgMass
from pdg.particle import PdgParticle
from pdg.decay import PdgBranchingFraction


def test_exception(api):
    with raises(PdgInvalidPdgIdError):
        api.get('nonexistent')

def test_edition(api):
    assert '2022' in api.editions
    if '2018' not in api.editions:
        return
    assert api.get('s008').edition == api.default_edition
    assert api.get('s008/2018').pdgid == 'S008/2018'
    assert api.get('s008/2018').baseid == 'S008'
    assert api.get('s008/2018').get_parent_pdgid() == None
    assert api.get('s008.1/2018').get_parent_pdgid() == 'S008/2018'

def test_charged_pion_2022(api):
    pion = api.get('S008/2022')
    assert isinstance(pion, PdgParticle)
    assert pion.pdgid == 'S008/2022'
    assert pion.edition == '2022'
    assert pion.description == 'pi+-'
    assert pion.data_type == 'PART'
    assert pion.get_parent_pdgid() == None
    assert pion.name == 'pi+'
    assert pion.mcid == 211
    assert pion.charge == 1.0
    assert pion.quantum_I == '1'
    assert pion.quantum_G == '-'
    assert pion.quantum_J == '0'
    assert pion.quantum_P == '-'
    assert pion.quantum_C == None
    assert sum(1 for _ in pion.properties(require_summary_data=False)) == 12
    assert sum(1 for _ in pion.properties(require_summary_data=True)) == 10
    assert sum(1 for _ in pion.exclusive_branching_fractions()) == 9
    assert sum(1 for _ in pion.exclusive_branching_fractions(include_subdecays=True)) == 11

def test_charged_pion_mass_2022(api):
    m = api.get('S008M/2022')
    assert m._count_data_entries('S008m', 2022) == 2
    assert isinstance(m, PdgMass)
    assert m.description == 'pi+- MASS'
    assert m.n_summary_table_values() == 1
    assert m.get_parent_pdgid() == 'S008/2022'
    assert isinstance(m.get_particle(), PdgParticle)
    # Enable following tests only after IN_SUMMARY_TABLE is properly set
    best_value = m.best_summary()
    assert best_value.in_summary_table == True
    assert round(best_value.value, 5) == 139.57039
    assert round(best_value.error_positive, 5) == 0.00018
    assert round(best_value.error_negative, 5) == 0.00018
    assert best_value.error is not None
    assert round(best_value.error,5) == 0.00018
    assert round(best_value.scale_factor, 1) == 1.8
    assert best_value.units == 'MeV'
    assert best_value.display_value_text == '139.57039+-0.00018'
    assert best_value.value_type_key == 'FC'
    assert str(best_value).strip() == '139.57039+-0.00018   OUR FIT'
    best_value_GeV = PdgConvertedValue(best_value, 'GeV')
    assert round(best_value_GeV.value, 8) == 0.13957039
    assert round(best_value_GeV.error_positive, 8) == 1.8E-7
    assert round(best_value_GeV.error_negative, 8) == 1.8E-7
    assert round(best_value_GeV.scale_factor, 1) == 1.8
    assert best_value_GeV.units == 'GeV'

def test_neutral_pion_decay_2022(api):
    b = api.get('S009.1/2022')
    assert isinstance(b, PdgBranchingFraction)
    assert b.description == 'pi0 --> 2gamma'
    assert b.n_summary_table_values() == 1
    assert b.get_parent_pdgid() == 'S009/2022'
    assert isinstance(b.get_particle(), PdgParticle)
    assert b.is_subdecay == False
    assert b.subdecay_level == 0
    best_value = b.best_summary()
    assert best_value.in_summary_table == True
    assert round(best_value.value, 5) == 0.98823
    assert round(best_value.error_positive, 5) == 0.00034
    assert round(best_value.error_negative, 5) == 0.00034
    assert round(best_value.scale_factor, 1) == 1.5
    assert best_value.units == ''
    assert best_value.display_value_text == '(98.823+-0.034)E-2'
    assert best_value.value_type_key == 'FC'
    # assert best_value.display_in_percent == True   # FIXME

def test_subdecay_modes(api):
    assert api.get('S008.1').is_subdecay == False
    assert api.get('S008.3').is_subdecay == True
    assert api.get('S008.1').subdecay_level == 0
    assert api.get('S008.3').subdecay_level == 1

def test_limit_2022(api):
    assert api.get('S008.11').best_summary().is_limit == True
    assert api.get('S008.11').best_summary().is_upper_limit == True
    assert api.get('S008.11').best_summary().is_lower_limit == False
    assert api.get('S008FV').best_summary().is_limit == False
    assert api.get('S008FV').best_summary().is_upper_limit == False
    assert api.get('S008FV').best_summary().is_lower_limit == False

def test_error_2022(api):
    assert api.get('S066M2E/2022').best_summary().error == None
    assert api.get('M013.4/2022').best_summary().error == 0.0218379495175522

def test_data_flags(api):
    assert api.get('S003AMU').data_flags == 'As'
    assert api.get('S004AMU').data_flags == 'As'
    assert api.get('S016AMU').data_flags == 'As'
    assert api.get('S017AMU').data_flags == 'A0s'
    assert api.get('Q007TP').data_flags == 'D'
    assert api.get('Q007TP2').data_flags == 's'
    assert api.get('Q007TP4').data_flags == ''

def test_old_bugs(api):
    # Check fix for metadata bug in v0.0.5
    assert api.get('S086DRA').best_summary() is not None
    assert api.get('S086DGS').best_summary() is not None
