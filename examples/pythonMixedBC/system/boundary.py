"""Time-varying temperature on inflow, zero gradient on outflow."""

import numpy as np

from pyOFTools.bc import MixedBC, ScalarMixed


class HotInflow(MixedBC):
    Tmean: float  # read from 0/T
    amplitude: float = 10  # optional in 0/T

    def update(self) -> ScalarMixed:
        return ScalarMixed(
            refValue=self.Tmean + self.amplitude * np.sin(self.time),
            refGrad=0.0,
            valueFraction=(self.phi < 0).astype(float),
        )
