# %%
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

filepath = Path(__file__).parent

vol_alpha = pd.read_csv(filepath / "postProcessing/vol_alpha.csv")
sns.lineplot(data=vol_alpha, x="time", y="alpha_water_volIntegrate")
plt.xlabel("Time [s]")
plt.ylabel("Volume of water [m³]")
plt.title("Volume of water over time")
plt.grid()
# %%
mass_width = pd.read_csv(filepath / "postProcessing/mass.csv")
mass_width["group"] = mass_width["group"].map(
    {1: "0-0.146m", 2: "0.146-0.292m", 3: "0.292-0.438m", 4: "0.438-0.584m"}
)
plt.figure()
sns.lineplot(data=mass_width, x="time", y="rho_volIntegrate", hue="group")
plt.xlabel("Time [s]")
plt.ylabel("Mass of water [kg]")
plt.title("Mass of water over time")
plt.grid()

mass_height = pd.read_csv(filepath / "postProcessing/mass_dist_height.csv")
mass_height["group"] = mass_height["group"].map(
    {1: "0-0.146m", 2: "0.146-0.292m", 3: "0.292-0.438m", 4: "0.438-0.584m"}
)
plt.figure()
sns.lineplot(data=mass_height, x="time", y="rho_volIntegrate", hue="group")
plt.xlabel("Time [s]")
plt.ylabel("Mass of water [kg]")
plt.title("Mass of water over time")
plt.grid()
plt.show()
