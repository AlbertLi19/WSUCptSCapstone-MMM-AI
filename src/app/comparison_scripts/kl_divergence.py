import numpy as np
from sklearn.neighbors import KernelDensity
from scipy.stats import wasserstein_distance



'''
Compute the kl divergence, wasserstein distance, and parametric distance between two distributions
p_samples: 
'''

# --- Metric Functions ---

def kl_divergence_kde(p_samples, q_samples, bandwidth=1):
    """Approximate KL divergence between P and Q using KDE."""
    kde_p = KernelDensity(kernel='gaussian', bandwidth=bandwidth).fit(p_samples)
    kde_q = KernelDensity(kernel='gaussian', bandwidth=bandwidth).fit(q_samples)
    log_p = kde_p.score_samples(p_samples)
    log_q = kde_q.score_samples(p_samples)
    return np.mean(log_p - log_q)

def parametric_diff(p_samples, q_samples):
    """Compute absolute difference in mean and std deviation."""
    mean_diff = np.abs(np.mean(p_samples) - np.mean(q_samples))
    std_diff = np.abs(np.std(p_samples) - np.std(q_samples))
    return mean_diff, std_diff

def custom_weighted_divergence(kl, wasser, mean_diff, std_diff,
                               lambda_kl=1.0, lambda_w=1.0, lambda_param=0.5):  
    param_diff = mean_diff + std_diff
    custom_score = (
        lambda_kl * kl +
        lambda_w * wasser +
        lambda_param * param_diff
    )
    return custom_score

def compute_difference_metrics(p_samples, q_samples):
    # Compute Metrics
    kl = kl_divergence_kde(p_samples, q_samples)
    wasser = wasserstein_distance(p_samples.ravel(), q_samples.ravel())
    mean_diff, std_diff = parametric_diff(p_samples, q_samples)

    custom_score = custom_weighted_divergence(kl, wasser, mean_diff, std_diff)

    return {
        "kl_divergence": kl,
        "wasserstein_distance": wasser,
        "mean_difference": mean_diff,
        "std_dev_difference": std_diff,
        "custom_score": custom_score
    }