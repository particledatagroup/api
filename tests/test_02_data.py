"""
Test cases for the PDG data.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.errors import PdgInvalidPdgId
from pdg.mass import PdgMass
from pdg.particle import PdgParticle
from pdg.decay import PdgBranchingFraction


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect()

    def test_exception(self):
        self.assertRaises(PdgInvalidPdgId, self.api.get, 'nonexistent')

    def test_edition(self):
        self.assertEqual(self.api.get('s008').edition, self.api.default_edition())
        self.assertEqual(self.api.get('s008/2018').pdgid, 'S008/2018')
        self.assertEqual(self.api.get('s008/2018').baseid, 'S008')
        self.assertEqual(self.api.get('s008/2018').parent_pdgid(), None)
        self.assertEqual(self.api.get('s008.1/2018').parent_pdgid(), 'S008/2018')

    def test_charged_pion(self):
        pion = self.api.get('S008/2022')
        self.assertIsInstance(pion, PdgParticle)
        self.assertEqual(pion.pdgid, 'S008/2022')
        self.assertEqual(pion.data_edition(), self.api.info('edition'))
        self.assertEqual(pion.description(), 'pi+-')
        self.assertEqual(pion.data_type(), 'PART')
        self.assertEqual(pion.parent_pdgid(), None)
        self.assertEqual(pion.name(), 'pi+')
        self.assertEqual(pion.mcid(), 211)
        self.assertEqual(pion.charge(), 1.0)
        self.assertEqual(pion.quantum_I(), '1')
        self.assertEqual(pion.quantum_G(), '-')
        self.assertEqual(pion.quantum_J(), '0')
        self.assertEqual(pion.quantum_P(), '-')
        self.assertEqual(pion.quantum_C(), None)
        self.assertEqual(sum(1 for _ in pion.properties()), 12)
        self.assertEqual(sum(1 for _ in pion.properties(require_summary_data=True)), 10)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions()), 9)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions(include_subdecays=True)), 11)

    def test_charged_pion_mass(self):
        m = self.api.get('S008M/2022')
        self.assertEqual(m._count_data_entries('S008m', 2022), 2)
        self.assertIsInstance(m, PdgMass)
        self.assertEqual(m.description(), 'pi+- MASS')
        self.assertEqual(m.n_summary_table_values(), 1)
        self.assertEqual(m.parent_pdgid(), 'S008/2022')
        self.assertIsInstance(m.particle(), PdgParticle)
        # Enable following tests only after IN_SUMMARY_TABLE is properly set
        best_value = m.best_value()
        self.assertEqual(best_value.in_summary_table(), True)
        self.assertEqual(round(best_value.value(), 5), 139.57039)
        self.assertEqual(round(best_value.error_positive(), 5), 0.00018)
        self.assertEqual(round(best_value.error_negative(), 5), 0.00018)
        self.assertEqual(round(best_value.scale_factor(), 1), 1.8)
        self.assertEqual(best_value.unit_text(), 'MeV')
        self.assertEqual(best_value.display_value_text(), '139.57039+-0.00018')
        self.assertEqual(best_value.value_type(), 'FC')
        self.assertEqual(str(best_value).strip(), '139.57039+-0.00018   OUR FIT')
        best_value_GeV = m.best_value_in_GeV()
        self.assertEqual(round(best_value_GeV.value(), 8), 0.13957039)
        self.assertEqual(round(best_value_GeV.error_positive(), 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.error_negative(), 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.scale_factor(), 1), 1.8)
        self.assertEqual(best_value_GeV.unit_text(), 'GeV')

    def test_neutral_pion_decay(self):
        b = self.api.get('S009.1/2022')
        self.assertIsInstance(b, PdgBranchingFraction)
        self.assertEqual(b.description(), 'pi0 --> 2gamma')
        self.assertEqual(b.n_summary_table_values(), 1)
        self.assertEqual(b.parent_pdgid(), 'S009/2022')
        self.assertIsInstance(b.particle(), PdgParticle)
        self.assertEqual(b.is_subdecay(), False)
        self.assertEqual(b.subdecay_level(), 0)
        best_value = b.best_value()
        self.assertEqual(best_value.in_summary_table(), True)
        self.assertEqual(round(best_value.value(), 5), 0.98823)
        self.assertEqual(round(best_value.error_positive(), 5), 0.00034)
        self.assertEqual(round(best_value.error_negative(), 5), 0.00034)
        self.assertEqual(round(best_value.scale_factor(), 1), 1.5)
        self.assertEqual(best_value.unit_text(), None)
        self.assertEqual(best_value.display_value_text(), '(98.823+-0.034)E-2')
        self.assertEqual(best_value.value_type(), 'FC')
        # self.assertEqual(best_value.display_in_percent(), True)   # FIXME

    def test_subdecay_modes(self):
        self.assertEqual(self.api.get('S008.1').is_subdecay(), False)
        self.assertEqual(self.api.get('S008.3').is_subdecay(), True)
        self.assertEqual(self.api.get('S008.1').subdecay_level(), 0)
        self.assertEqual(self.api.get('S008.3').subdecay_level(), 1)


if __name__ == '__main__':
    unittest.main()
