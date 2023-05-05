"""
Classes supporting particle mass.
"""

from pdg.data import PdgProperty, PdgConvertedValue


class PdgMass(PdgProperty):

    def best_value_in_GeV(self):
        """Return PDG "best" value of the particle mass in GeV.

        NOTE: best_value() will return a PdgSummaryValue using the units
        shown in the Summary Table, which is not always GeV."""
        return PdgConvertedValue(self.best_value(), 'GeV')
