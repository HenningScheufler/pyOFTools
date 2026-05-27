"""Plot the CSVs produced by ``postProcess.py``.

Run after ``./Allrun`` (or after a live solver run). Matches the four
``@Table`` outputs defined in ``postProcess.py``.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

postProcessing = Path(__file__).parent / "postProcessing"

vol = pd.read_csv(postProcessing / "water_volume.csv")
area_df = pd.read_csv(postProcessing / "interface_area.csv")
mass = pd.read_csv(postProcessing / "mass_profile_x.csv")
plane_p = pd.read_csv(postProcessing / "mean_p_midplane.csv")

fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))

axes[0, 0].plot(vol["time"], vol["water_volume"], marker="o", markersize=3)
axes[0, 0].set(xlabel="time [s]", ylabel="water volume [m³]", title="Total water volume")

axes[0, 1].plot(area_df["time"], area_df["interface_area"], marker="o", markersize=3)
axes[0, 1].set(xlabel="time [s]", ylabel="interface area [m²]", title="α = 0.5 interface area")

mass_wide = mass.pivot(index="time", columns="group", values="mass")
mass_wide.plot(ax=axes[1, 0], marker="o", markersize=3)
axes[1, 0].set(xlabel="time [s]", ylabel="mass per bin [kg]", title="Mass along x (per bin)")
axes[1, 0].legend(title="bin", fontsize=8)

axes[1, 1].plot(plane_p["time"], plane_p["mean_p_midplane"], marker="o", markersize=3)
axes[1, 1].set(xlabel="time [s]", ylabel="mean p [Pa]", title="Mean p on y = 0.146 m plane")

fig.tight_layout()
plt.show()
