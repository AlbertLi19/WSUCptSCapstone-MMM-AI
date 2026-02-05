import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy.stats as ss
import fitter
import json

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import scipy.stats as ss

PDF_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','PDF Images')
COL_NAMES = ['Size', 'Aspect_Ratio', 'Orientation', 'Distance']

timeoutValue = 30

def pull_timeout(new_timeout):
    global timeoutValue
    timeoutValue = new_timeout

def fit_distribution_sample(data, selected_distributions): # Implement in fit_and_plot (how would this integrate with timer?)
        f = fitter.Fitter(data, distributions=selected_distributions, timeout=timeoutValue)
        f.fit(max_workers=1)
        return next(iter(f.get_best().items()))


def calculate_mle_and_fwhm(dist_name, param, x):
    dist = getattr(ss, dist_name)
    pdf = dist.pdf(x, **param)
    
    # MLE = pdf at maximum
    max_idx = np.argmax(pdf)
    x_peak = x[max_idx]
    y_peak = pdf[max_idx]

    # FWHM = width of y_peak / 2
    half_max = y_peak / 2
    indices_above_half = np.where(pdf >= half_max)[0]

    if len(indices_above_half) > 1:
        fwhm = x[indices_above_half[-1]] - x[indices_above_half[0]]
    else:
        fwhm = 0

    return x_peak, y_peak, fwhm, x[indices_above_half[0]], x[indices_above_half[-1]], half_max



def plot_best_pdf_curves(data, best_models_df, save_path=None, show=True, n_samples=100, x_points=1000):
    """
    Plot all PDF curve iterations for the single most likely PDF
    and automatically generate a combined 2x2 grid image once all 4 plots exist.
    """

    # --- Setup and validation ---
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    candidate_distributions = {
        "gamma": ss.gamma,
        "exponential": ss.expon,
        "chi-square": ss.chi2,
        "cauchy": ss.cauchy,
        "invgauss": ss.invgauss,
        "laplace": ss.laplace,
        "levy": ss.levy,
        "logistic": ss.logistic,
        "lognorm": ss.lognorm,
        "maxwell": ss.maxwell,
        "normal": ss.norm,
        "rayleigh": ss.rayleigh,
        "weibull": ss.weibull_min,
    }

    if best_models_df.empty or "dist" not in best_models_df.columns:
        print("⚠️ No valid model dataframe provided.")
        return

    # --- Select most probable model ---
    best_model_name = best_models_df.sort_values("prob", ascending=False)["dist"].iloc[0]
    print(f"📈 Plotting PDF curve iterations for best model: {best_model_name}")

    dist = candidate_distributions.get(best_model_name)
    if dist is None:
        print(f"⚠️ Distribution '{best_model_name}' not supported.")
        return

    # --- Fit distribution and create x values ---
    xmin, xmax = np.min(data), np.max(data)
    x = np.linspace(xmin, xmax, x_points)

    try:
        params = dist.fit(data)
    except Exception as e:
        print(f"❌ Fit failed for {best_model_name}: {e}")
        return

    # --- Generate multiple perturbed parameter samples ---
    param_samples = np.array([
        np.random.normal(p, abs(p) * 0.05 if p != 0 else 0.01, n_samples)
        for p in params
    ]).T

    plt.figure(figsize=(10, 6))
    curves = []

    for ps in param_samples:
        try:
            pdf_values = dist.pdf(x, *ps)
            plt.plot(x, pdf_values, color="gray", alpha=0.3, linewidth=1)
            curves.append(pdf_values)
        except Exception:
            continue

    # --- Average curve ---
    if curves:
        avg_curve = np.mean(curves, axis=0)
        plt.plot(x, avg_curve, color="red", linewidth=2, label=f"{best_model_name} (avg)")
        plt.hist(data, bins=30, density=True, color="gray", alpha=0.3, label="Data Histogram")

        plt.title(f"Best PDF: {best_model_name}", fontsize=16)
        plt.xlabel("Value", fontsize=14)
        plt.ylabel("Probability Density", fontsize=14)
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Saved individual PDF plot: {save_path}")

    if show:
        plt.show()
    plt.close()

    # --- Automatically generate 2x2 combined figure if all 4 exist ---
    folder = os.path.dirname(save_path) if save_path else os.getcwd()
    image_files = [
        ("Size", os.path.join(folder, "Size_PDF_Curves.png")),
        ("Aspect", os.path.join(folder, "Aspect_PDF_Curves.png")),
        ("Orientation", os.path.join(folder, "Orientation_PDF_Curves.png")),
        ("Spacing", os.path.join(folder, "Spacing_PDF_Curves.png")),
    ]

    # Check if all 4 exist before creating the combined image
    if all(os.path.exists(p) for _, p in image_files):
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle("Combined PDF Curves (2x2)", fontsize=18)

            for ax, (title, path) in zip(axes.ravel(), image_files):
                img = mpimg.imread(path)
                ax.imshow(img)
                ax.axis("off")
                ax.set_title(title, fontsize=14)

            plt.tight_layout(rect=[0, 0, 1, 0.96])
            combined_path = os.path.join(folder, "Combined_PDF_2x2.png")
            plt.savefig(combined_path, dpi=300, bbox_inches="tight")
            plt.close(fig)

            print(f"🎨 Combined 2x2 image created: {combined_path}")

        except Exception as e:
            print(f"⚠️ Failed to generate combined image: {e}")





def fit_and_plot(impurity_df: pd.DataFrame, spacing_df: pd.DataFrame, name, overlay=False, show=False, progress_signal=None):
    size = np.abs(impurity_df[COL_NAMES[0]].dropna())
    aspect = np.abs(impurity_df[COL_NAMES[1]].dropna())
    orientation = np.abs(impurity_df[COL_NAMES[2]].dropna())
    spacing = np.abs(spacing_df[COL_NAMES[3]].dropna())

    os.makedirs(PDF_FOLDER, exist_ok=True)

    # Candidate distributions
    candidate_distributions = {
        "gamma": ss.gamma,
        "exponential": ss.expon,
        "chi-square": ss.chi2,
        "cauchy": ss.cauchy,
        "invgauss": ss.invgauss,
        "laplace": ss.laplace,
        "levy": ss.levy,
        "logistic": ss.logistic,
        "lognorm": ss.lognorm,
        "maxwell": ss.maxwell,
        "normal": ss.norm,
        "rayleigh": ss.rayleigh,
        "weibull": ss.weibull_min,
    }

    def compute_aic(prob_data):
        """Fit all candidate distributions, compute AIC, and return weights (probabilities)."""
        results = []
        n = len(prob_data)
        for name, dist in candidate_distributions.items():
            try:
                params = dist.fit(prob_data)
                logL = np.sum(dist.logpdf(prob_data, *params))
                k = len(params)
                aic = 2 * k - 2 * logL
                results.append((name, aic))
            except Exception as e:
                continue

        # Convert AIC to model weights (probabilities)
        df = pd.DataFrame(results, columns=["dist", "aic"])
        df = df.sort_values("aic")
        min_aic = df["aic"].min()
        delta_aic = df["aic"] - min_aic
        weights = np.exp(-0.5 * delta_aic)
        weights /= np.sum(weights)
        df["prob"] = weights * 100  # percentage
        df = df[df["prob"] > 0.5]   # only show meaningful fits
        return df

    def plot_conf(ax, df, title):
        ax.bar(df["dist"], df["prob"])
        ax.set_title(title)
        ax.set_ylabel("Model Probability (%)")
        ax.set_xticklabels(df["dist"], rotation=45, ha="right")
        ax.set_ylim(0, 100)

    print("==== Starting manual AIC fitting and model comparison ====")
    print("Fitting Size...")
    size_df = compute_aic(size)
    if progress_signal: progress_signal.emit(1)
    print("Fitting Aspect...")
    aspect_df = compute_aic(aspect)
    if progress_signal: progress_signal.emit(2)
    print("Fitting Orientation...")
    orientation_df = compute_aic(orientation)
    if progress_signal: progress_signal.emit(3)
    print("Fitting Spacing...")
    spacing_df = compute_aic(spacing)
    if progress_signal: progress_signal.emit(4)

    plot_best_pdf_curves(size, size_df, save_path=os.path.join(PDF_FOLDER, "Size_PDF_Curves.png"))
    plot_best_pdf_curves(aspect, aspect_df, save_path=os.path.join(PDF_FOLDER, "Aspect_PDF_Curves.png"))
    plot_best_pdf_curves(orientation, orientation_df, save_path=os.path.join(PDF_FOLDER, "Orientation_PDF_Curves.png"))
    plot_best_pdf_curves(spacing, spacing_df, save_path=os.path.join(PDF_FOLDER, "Spacing_PDF_Curves.png"))

    

    # Plot results
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    plot_conf(ax[0, 0], size_df, "Size Distribution Probabilities")
    if progress_signal: progress_signal.emit(5)
    plot_conf(ax[0, 1], aspect_df, "Aspect Ratio Distribution Probabilities")
    if progress_signal: progress_signal.emit(6)
    plot_conf(ax[1, 0], orientation_df, "Orientation Distribution Probabilities")
    if progress_signal: progress_signal.emit(7)
    plot_conf(ax[1, 1], spacing_df, "Spacing Distribution Probabilities")
    if progress_signal: progress_signal.emit(8)

    plt.tight_layout()
    plt.savefig(os.path.join(PDF_FOLDER, "combined_PDFs_no_overlay.png")) # combined_PDFs_overlay.png for the overlay (from list) button - delete in this version?
    if show:
        plt.show()

    # Fit all variables
    size_df = compute_aic(size)
    aspect_df = compute_aic(aspect)
    orientation_df = compute_aic(orientation)
    spacing_df = compute_aic(spacing)

    # Get best fits (highest probability)
    best_models = {
        "Size": size_df.iloc[0],
        "Aspect": aspect_df.iloc[0],
        "Orientation": orientation_df.iloc[0],
        "Spacing": spacing_df.iloc[0],
    }

    x_points = 1000
    variable_data = {
        "Size": size,
        "Aspect": aspect,
        "Orientation": orientation,
        "Spacing": spacing,
    }

   
    json_file_path = os.path.join(PDF_FOLDER, f"{name}.json")

    saved_data = {}
    for var_name, best_row in best_models.items():
        dist_name = best_row["dist"]
        dist = candidate_distributions[dist_name]
        data_array = variable_data[var_name]

        # Fit once and generate curve
        params = dist.fit(data_array)
        xmin, xmax = np.min(data_array), np.max(data_array)
        x = np.linspace(xmin, xmax, x_points)
        pdf = dist.pdf(x, *params)
        norm_pdf = pdf / np.trapz(pdf, x)

        saved_data[var_name] = {
            "distribution": dist_name,
            "probability": float(best_row["prob"]),
            "parameters": [float(p) for p in params],
            "x": x.tolist(),
            "pdf": norm_pdf.tolist(),
        }

    # Write to JSON
    with open(json_file_path, "w") as f:
        json.dump(saved_data, f, indent=4)

    print(f"Saved best-fit JSON: {json_file_path}")
    print("==== Saved AIC-based model probability plots ====")

    
