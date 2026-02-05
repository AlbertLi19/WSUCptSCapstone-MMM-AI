import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 6))
# path = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/63020B (ID D)/'
# files= [['63020B_TPStacked_Excel_File_MA_AR_NormAng_New_NormAbs', 'Stacked_file_C&D_63020B_TP']]
# colnames = ['Major_Axis_Size','Aspect_ratio','Orientation','Spacing']

path = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/'
files= [['combined_data_63020B_TP']]
colnames = ['Size','Aspect_Ratio','Orientation','Distance']

df = pd.read_csv(path + files[0][0] + '.csv')
size = np.abs(df[colnames[0]].dropna())
aspect = np.abs(df[colnames[1]].dropna())
orientation = np.abs(df[colnames[2]].dropna())
# df = pd.read_csv(path + files[0][1] + '.csv')
spacing = np.abs(df[colnames[3]].dropna())
## Convert Pixles to Microns using ratio provided by DR. Zare
scale = 200/1024
size *= scale
spacing *= scale
## Plot values
ax[0, 0].hist(size, density=True, color="blue", edgecolor="black")
ax[0, 0].set_title("Size Distribution")
ax[0, 0].set_xlabel("Inclusion Major Axis (μm)")
ax[0, 0].set_ylabel("Relative Probability")
ax[0, 1].hist(aspect, density=True, color="orange", edgecolor="black")
ax[0, 1].set_title("Aspect Ratio Distribution")
ax[0, 1].set_xlabel("Inclusion Aspect ratio")
ax[0, 1].set_ylabel("Relative Probability")
ax[1, 0].hist(orientation, density=True, color="green", edgecolor="black")
ax[1, 0].set_title("Orientation Distribution")
ax[1, 0].set_xlabel("Inclusion Orientation Angle (degree)")
ax[1, 0].set_ylabel("Relative Probability")
ax[1, 1].hist(spacing, density=True, color="red", edgecolor="black")
ax[1, 1].set_title("Spacing Distribution")
ax[1, 1].set_xlabel("Inclusion Spacing (μm)")
ax[1, 1].set_ylabel("Relative Probability")
plt.tight_layout()  # Automatically adjusts spacing
plt.savefig("Data_Mine_63020B_TP.png")
# plt.show()