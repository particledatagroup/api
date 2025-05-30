"""
Test cases for the PDG data.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError
from pdg.data import PdgConvertedValue, PdgMass
from pdg.particle import PdgParticle, PdgParticleList
from pdg.decay import PdgBranchingFraction


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect()

    def test_exception(self):
        self.assertRaises(PdgInvalidPdgIdError, self.api.get, 'nonexistent')

    def test_edition(self):
        self.assertEqual(self.api.get('s008').edition, self.api.default_edition)
        if '2018' not in self.api.editions:
            return
        self.assertEqual(self.api.get('s008/2018').pdgid, 'S008/2018')
        self.assertEqual(self.api.get('s008/2018').baseid, 'S008')
        self.assertEqual(self.api.get('s008/2018').get_parent_pdgid(), None)
        self.assertEqual(self.api.get('s008.1/2018').get_parent_pdgid(), 'S008/2018')

    def test_charged_pion_2022(self):
        if '2022' not in self.api.editions:
            return
        pion = self.api.get('S008/2022')[0]
        self.assertIsInstance(pion, PdgParticle)
        self.assertEqual(pion.pdgid, 'S008/2022')
        self.assertEqual(pion.edition, '2022')
        self.assertEqual(pion.description, 'pi+-')
        self.assertEqual(pion.data_type, 'PART')
        self.assertEqual(pion.get_parent_pdgid(), None)
        self.assertEqual(pion.name, 'pi+')
        self.assertEqual(pion.mcid, 211)
        self.assertEqual(pion.charge, 1.0)
        self.assertEqual(pion.quantum_I, '1')
        self.assertEqual(pion.quantum_G, '-')
        self.assertEqual(pion.quantum_J, '0')
        self.assertEqual(pion.quantum_P, '-')
        self.assertEqual(pion.quantum_C, None)
        self.assertEqual(sum(1 for _ in pion.properties(require_summary_data=False)), 14)
        self.assertEqual(sum(1 for _ in pion.properties(require_summary_data=True)), 10)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions()), 9)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions(include_subdecays=True)), 11)

    def test_charged_pion_mass_2022(self):
        if '2022' not in self.api.editions:
            return
        m = self.api.get('S008M/2022')
        self.assertEqual(m._count_data_entries('S008m', 2022), 2)
        self.assertIsInstance(m, PdgMass)
        self.assertEqual(m.description, 'pi+- MASS')
        self.assertEqual(m.n_summary_table_values(), 1)
        self.assertEqual(m.get_parent_pdgid(), 'S008/2022')
        self.assertRaises(PdgAmbiguousValueError, lambda: m.get_particle())
        self.assertIsInstance(m.get_particles(), PdgParticleList)
        self.assertIsInstance(m.get_particles()[0], PdgParticle)
        # Enable following tests only after IN_SUMMARY_TABLE is properly set
        best_value = m.best_summary()
        self.assertEqual(best_value.in_summary_table, True)
        self.assertEqual(round(best_value.value, 5), 139.57039)
        self.assertEqual(round(best_value.error_positive, 5), 0.00018)
        self.assertEqual(round(best_value.error_negative, 5), 0.00018)
        self.assertEqual(round(best_value.error,5), 0.00018)
        self.assertEqual(round(best_value.scale_factor, 1), 1.8)
        self.assertEqual(best_value.units, 'MeV')
        # self.assertEqual(best_value.units_tex, 'MeV')
        self.assertEqual(best_value.value_text, '139.57039+-0.00018')
        # self.assertEqual(best_value.value_tex, None) # FIXME
        self.assertEqual(best_value.display_value_text, '139.57039+-0.00018')
        self.assertEqual(best_value.value_type_key, 'FC')
        self.assertEqual(str(best_value).strip(), '139.57039+-0.00018   OUR FIT')
        best_value_GeV = PdgConvertedValue(best_value, 'GeV')
        self.assertEqual(round(best_value_GeV.value, 8), 0.13957039)
        self.assertEqual(round(best_value_GeV.error_positive, 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.error_negative, 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.scale_factor, 1), 1.8)
        self.assertEqual(best_value_GeV.units, 'GeV')

    def test_neutral_pion_decay_2022(self):
        if '2022' not in self.api.editions:
            return
        b = self.api.get('S009.1/2022')
        self.assertIsInstance(b, PdgBranchingFraction)
        self.assertEqual(b.description, 'pi0 --> 2gamma')
        self.assertEqual(b.n_summary_table_values(), 1)
        self.assertEqual(b.get_parent_pdgid(), 'S009/2022')
        self.assertIsInstance(b.get_particle(), PdgParticle)
        self.assertEqual(b.is_subdecay, False)
        self.assertEqual(b.subdecay_level, 0)
        best_value = b.best_summary()
        self.assertEqual(best_value.in_summary_table, True)
        self.assertEqual(round(best_value.value, 5), 0.98823)
        self.assertEqual(round(best_value.error_positive, 5), 0.00034)
        self.assertEqual(round(best_value.error_negative, 5), 0.00034)
        self.assertEqual(round(best_value.scale_factor, 1), 1.5)
        self.assertEqual(best_value.units, '')
        # self.assertEqual(best_value.units_tex, '')
        self.assertEqual(best_value.value_text, '(98.823+-0.034)E-2')
        # self.assertEqual(best_value.value_tex, None)                # FIXME
        self.assertEqual(best_value.display_value_text, '98.823+-0.034')
        self.assertEqual(best_value.display_power_of_ten, -2)
        self.assertEqual(best_value.value_type_key, 'FC')
        self.assertEqual(best_value.display_in_percent, True)

    def test_subdecay_modes(self):
        self.assertEqual(self.api.get('S008.1').is_subdecay, False)
        self.assertEqual(self.api.get('S008.3').is_subdecay, True)
        self.assertEqual(self.api.get('S008.1').subdecay_level, 0)
        self.assertEqual(self.api.get('S008.3').subdecay_level, 1)

    def test_limit_2022(self):
        if '2022' not in self.api.editions:
            return
        self.assertEqual(self.api.get('S008.11').best_summary().is_limit, True)
        self.assertEqual(self.api.get('S008.11').best_summary().is_upper_limit, True)
        self.assertEqual(self.api.get('S008.11').best_summary().is_lower_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_upper_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_lower_limit, False)

    def test_error_2022(self):
        if '2022' not in self.api.editions:
            return
        self.assertEqual(self.api.get('S066M2E/2022').best_summary().error, None)
        self.assertEqual(self.api.get('M013.4/2022').best_summary().error, 0.0218379495175522 )

    def test_data_flags(self):
        self.assertEqual(self.api.get('S003AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S004AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S016AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S017AMU').data_flags, 'A0s')
        self.assertEqual(self.api.get('Q007TP').data_flags, 'D')
        self.assertEqual(self.api.get('Q007TP2').data_flags, 's')
        self.assertEqual(self.api.get('Q007TP4').data_flags, 's')

    def test_old_bugs(self):
        # Check fix for metadata bug in v0.0.5
        self.assertIsNotNone(self.api.get('S086DRA').best_summary())
        self.assertIsNotNone(self.api.get('S086DGS').best_summary())
        # Check that LIMIT_TYPE is NULL instead of the empty string
        self.assertFalse(self.api.get('S041.3').is_limit)

    def test_value_parsing(self):
        # Check that DISPLAY_VALUE_TEXT is being parsed properly
        # Symmetric errors:
        self.assertEqual(round(self.api.get('S086T').value*1e12, 2), 1.52)
        self.assertEqual(round(self.api.get('S086T').error_positive*1e15, 1), 6)
        self.assertEqual(round(self.api.get('S086T').error_negative*1e15, 1), 6)
        self.assertEqual(round(self.api.get('S086T').error*1e15, 1), 6)
        # Slightly asymmetric errors:
        self.assertEqual(round(self.api.get('S063T').value*1e12, 2), 1.64)
        self.assertEqual(round(self.api.get('S063T').error_positive*1e13, 1), 1.6)
        self.assertEqual(round(self.api.get('S063T').error_negative*1e13, 1), 1.6)
        self.assertEqual(round(self.api.get('S063T').error*1e13, 2), 1.6)
        # Very asymmetric errors:
        self.assertEqual(round(self.api.get('S041P63').value*1e3, 1), 10.2)
        self.assertEqual(round(self.api.get('S041P63').error_positive*1e3, 1), 3.2)
        self.assertEqual(round(self.api.get('S041P63').error_negative*1e3, 1), 6.9)
        self.assertIsNone(self.api.get('S041P63').error)

    def test_HFLAV_comment(self):
        if int(self.api.default_edition) >= 2024:
            self.assertEqual(self.api.get('S042T').comment,
                             '(Produced by HFLAV)')

    def test_parent_pdgid(self):
        mass = self.api.get('Q007TP4')
        # We want to verify that the intermediate section gets skipped, so
        # first, we check that the direct parent is in fact such a section
        direct_parent = self.api.get(mass._get_pdgid()['parent_pdgid'])
        self.assertEqual(direct_parent.data_type, 'SEC')
        # Now we can check that the section gets skipped
        self.assertEqual(mass.get_parent_pdgid(include_edition=False), 'Q007')

    def test_decay_pdgid_map(self):
        bf = self.api.get('B000.2')
        br_pdgids = sorted([br.baseid for br in bf.branching_ratios()])
        self.assertEqual(br_pdgids, ['B000R01', 'B000R2'])
        br = self.api.get('B000R2')
        bf_pdgids = sorted([bf.baseid for bf in br.branching_fractions()])
        self.assertEqual(bf_pdgids, ['B000.1', 'B000.2'])


if __name__ == '__main__':
    unittest.main()
