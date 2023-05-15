"""
Classes supporting decays and branching fractions/ratios.
"""

from pdg.data import PdgProperty


class PdgBranchingFraction(PdgProperty):

    @property
    def mode_number(self):
        """Mode number of this decay.

        Note that the decay mode number may change from one edition of the Review of Particle Physics
        to the next one."""
        return self._get_pdgid()['mode_number']

    @property
    def is_subdecay(self):
        """True if this is a subdecay ("indented") decay mode."""
        data_type_code = self.data_type
        if len(data_type_code) < 4:
            return False
        else:
            return data_type_code[0:3] == 'BFX' or data_type_code[0:3] == 'BFI'

    @property
    def subdecay_level(self):
        """Return indentation level of a decay mode."""
        if self.is_subdecay:
            return int(self.data_type[3])
        else:
            return 0
