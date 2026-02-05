import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as ss
import fitter

fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 6))

path = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/'
files = ['combined_data_63020B_IP']
colnames = ['Size', 'Aspect_Ratio', 'Orientation', 'Distance']
# path = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/63020B (ID D)/'
# files = ['63020B_IPStacked_Excel_File_MA_AR_NormAng_New_NormAbs','Stacked_file_C&D_63020B_IP']
# colnames = ['Major_Axis_Size', 'Aspect_ratio', 'Orientation', 'Spacing']

df = pd.read_csv(path + files[0] + '.csv')
size = np.abs(df[colnames[0]].dropna())
aspect = np.abs(df[colnames[1]].dropna())
orientation = np.abs(df[colnames[2]].dropna())
# df = pd.read_csv(path + files[1] + '.csv')
spacing = np.abs(df[colnames[3]].dropna())

scale = 200 / 1024
size *= scale
spacing *= scale

def fit_and_plot(data, ax, title, xlabel, color):
    f = fitter.Fitter(data)
    # f.distributions = ['weibull_min']
    f.fit()
    best_dist_name, best_params = next(iter(f.get_best().items()))
    
    dist = getattr(ss, best_dist_name)
    
    ax.hist(data, bins=30, density=True, color=color, alpha=0.7)
    
    x = np.linspace(data.min(), data.max(), 1000)
    pdf = dist.pdf(x, **best_params)
    ax.plot(x, pdf, color='black', linestyle='-', label=f'{best_dist_name} fit')
    ### MLE
    max_index = np.argmax(pdf)
    max_val = x[max_index]
    ax.axvline(x=max_val, color='red', linestyle='-', label='MLE')
    ### MLE
    ### FWHM
    peak = max(pdf)
    half_max = peak / 2
    above_half_max = np.where(pdf >= half_max)[0]
    fwhm = x[above_half_max[-1]] - x[above_half_max[0]]
    ax.hlines(half_max, x[above_half_max[0]], x[above_half_max[-1]], colors='blue', linestyles='-', label='FWHM')
    ###FWHM
    

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Relative Probability")
    ax.legend()

fit_and_plot(size, ax[0, 0], "Size Distribution", "Inclusion Major Axis (μm)", "blue")
fit_and_plot(aspect, ax[0, 1], "Aspect Ratio Distribution", "Inclusion Aspect Ratio", "orange")
fit_and_plot(orientation, ax[1, 0], "Orientation Distribution", "Inclusion Orientation Angle (degree)", "green")
fit_and_plot(spacing, ax[1, 1], "Spacing Distribution", "Inclusion Spacing (μm)", "red")

plt.tight_layout()
plt.savefig("hist_pdf_Data_Mine_63020B_IP.png")
plt.show()
