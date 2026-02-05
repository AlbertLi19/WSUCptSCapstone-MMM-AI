import os
import numpy as np
from fitter import Fitter
import matplotlib.pyplot as plt
import scipy.stats as ss

# Script for using the PDF/MLE/FWHM generation processes in the app to calculate from a txt file. Paste data to test in 'testdata.txt' separated by line with only the data itself (no headers)
# Script will print the best fitting PDF (using Fitter), and then the corresponding MLE/FWHM. It will print the results and a graphed output. 
# You can change the distributions and time threshold values at the bottom of the script as 'analyze_wrapper()' parameters.

def analyze_wrapper(selected_distributions, timeout_value):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'testdata.txt')

    data = np.loadtxt(file_path)

    def calculate_mle_and_fwhm(dist_name, param, x):
        dist = getattr(ss, dist_name)
        pdf = dist.pdf(x, **param)

        # MLE = pdf at maximum
        max_idx = np.argmax(pdf)
        x_peak = x[max_idx]
        y_peak = pdf[max_idx]

        # FWHM = width at half max height
        half_max = y_peak / 2
        indices_above_half = np.where(pdf >= half_max)[0]

        if len(indices_above_half) > 1:
            fwhm = x[indices_above_half[-1]] - x[indices_above_half[0]]
            fwhm_start = x[indices_above_half[0]]
            fwhm_end = x[indices_above_half[-1]]
        else:
            fwhm = 0
            fwhm_start = fwhm_end = x_peak

        return x_peak, y_peak, fwhm, fwhm_start, fwhm_end, half_max

    def fit_distribution(data, selected_distributions):
        f = Fitter(data, distributions=selected_distributions, timeout=timeout_value)
        f.fit()
        return next(iter(f.get_best().items()))

    # Fit
    dist_name, params = fit_distribution(data, selected_distributions)
    dist = getattr(ss, dist_name)

    x = np.linspace(data.min(), data.max(), 1000)
    pdf = dist.pdf(x, **params)

    x_peak, y_peak, fwhm, fwhm_start, fwhm_end, half_max = calculate_mle_and_fwhm(dist_name, params, x)

    return dist_name, x_peak, fwhm, data, x, pdf, half_max, fwhm_start, fwhm_end


def plot_data(data, x, pdf, half_max, fwhm_start, fwhm_end):
    plt.figure(figsize=(10, 6))

    # Histogram
    plt.hist(data, bins=50, density=True, alpha=0.5, label='Data Histogram')

    # PDF
    plt.plot(x, pdf, 'r-', label=f'{dist_name} PDF')

    # MLE
    plt.axvline(x_peak, color='g', linestyle='--', label=f'MLE (x = {x_peak:.2f})')

    # FWHM
    plt.hlines(half_max, fwhm_start, fwhm_end, color='b', linestyle='-', linewidth=2, label=f'FWHM = {fwhm:.2f}')
    plt.axvline(fwhm_start, color='b', linestyle=':', linewidth=1)
    plt.axvline(fwhm_end, color='b', linestyle=':', linewidth=1)

    # Lables
    plt.title(f'Data with Fitted PDF: {dist_name}')
    plt.xlabel('Value')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


selected_distributions = ['alpha', 'anglit', 'arcsine', 'argus', 'beta', 'betaprime', 'bradford', 'burr', 'burr12', 'cauchy', 'chi', 'chi2', 'cosine', 'crystalball', 'dgamma', 'dpareto_lognorm', 'dweibull', 'erlang', 'expon', 'exponnorm', 'exponpow', 'exponweib', 'f', 'fatiguelife', 'fisk', 'foldcauchy', 'foldnorm', 'gamma', 'gausshyper', 'genexpon', 'genextreme', 'gengamma', 'genhalflogistic', 'genhyperbolic', 'geninvgauss', 'genlogistic', 'gennorm', 'genpareto', 'gibrat', 'gompertz', 'gumbel_l', 'gumbel_r', 'halfcauchy', 'halfgennorm', 'halflogistic', 'halfnorm', 'hypsecant', 'invgamma', 'invgauss', 'invweibull', 'irwinhall', 'jf_skew_t', 'johnsonsb', 'johnsonsu', 'kappa3', 'kappa4', 'ksone', 'kstwo', 'kstwobign', 'landau', 'laplace', 'laplace_asymmetric', 'levy', 'levy_l', 'levy_stable', 'loggamma', 'logistic', 'loglaplace', 'lognorm', 'loguniform', 'lomax', 'maxwell', 'mielke', 'moyal', 'multivariate_normal', 'nakagami', 'ncf', 'nct', 'ncx2', 'norm', 'norminvgauss', 'pareto', 'pearson3', 'powerlaw', 'powerlognorm', 'powernorm', 'rayleigh', 'rdist', 'recipinvgauss', 'reciprocal', 'rel_breitwigner', 'rice', 'semicircular', 'skewcauchy', 'skewnorm', 'studentized_range', 't', 'trapezoid', 'triang', 'truncexpon', 'truncnorm', 'truncpareto', 'truncweibull_min', 'tukeylambda', 'uniform', 'vonmises', 'vonmises_fisher', 'vonmises_line', 'wald', 'weibull_max', 'weibull_min', 'wrapcauchy']
dist_name, x_peak, fwhm, data, x, pdf, half_max, fwhm_start, fwhm_end = analyze_wrapper(selected_distributions, 30)

print(f"Distribution: {dist_name}")
print(f"MLE: {x_peak}")
print(f"FWHM: {fwhm}")

# Plot (optional)
plot_data(data, x, pdf, half_max, fwhm_start, fwhm_end)