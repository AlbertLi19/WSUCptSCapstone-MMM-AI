
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from pathlib import Path
import tkinter as tk
from tkinter import filedialog


# =========================================================
# SETTINGS
# =========================================================

IMAGE_DPI = 600
MIN_POINTS = 20

# Graph dimensions in inches
FIGURE_WIDTH = 16
FIGURE_HEIGHT = 10


# =========================================================
# 1. SELECT FOLDER
# =========================================================

root = tk.Tk()
root.withdraw()

folder_path = filedialog.askdirectory(
    title="Select Folder Containing Nanoindentation Data"
)

root.destroy()

if not folder_path:
    print("No folder selected.")
    raise SystemExit

folder = Path(folder_path)

# Create a folder for generated graphs
output_folder = folder / "load_depth_graphs"
output_folder.mkdir(exist_ok=True)

print(f"\nSelected folder: {folder}")
print(f"Graphs will be saved to: {output_folder}")


# =========================================================
# 2. READ AND VALIDATE A TEXT FILE
# =========================================================

def load_data(file_path):

    # ---------------------------------------------
    # Find the actual column header
    # ---------------------------------------------

    header_line = None

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        errors="replace"
    ) as file:

        for line_number, line in enumerate(file):

            columns = [
                column.strip()
                for column in line.strip().split("\t")
            ]

            # Check for the expected five-column header.
            # Ignore the exact symbols used for units.
            if (
                len(columns) == 5
                and "depth" in columns[0].lower()
                and "load" in columns[1].lower()
                and "time" in columns[2].lower()
            ):

                header_line = line_number

                break

    # If no recognizable header exists, skip the file.
    if header_line is None:

        raise ValueError(
            "Could not find the Depth, Load, Time header."
        )

    # ---------------------------------------------
    # Read the numerical data
    # ---------------------------------------------

    df = pd.read_csv(
        file_path,
        sep="\t",
        skiprows=header_line + 1,
        header=None,
        encoding="utf-8-sig",
        encoding_errors="replace"
    )

    # Check that there are exactly five columns.
    if len(df.columns) != 5:

        raise ValueError(
            "File does not contain exactly five data columns."
        )

    # Rename columns consistently.
    df.columns = [
        "Depth_nm",
        "Load_uN",
        "Time_s",
        "Disp_V",
        "Force_V"
    ]

    # ---------------------------------------------
    # Validate measurements
    # ---------------------------------------------

    # Convert all measurements to numeric values.
    for column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Reject files containing invalid data.
    if df.isna().any().any():

        raise ValueError(
            "File contains missing or nonnumeric measurements."
        )

    # Reject infinite values.
    if not np.isfinite(df.to_numpy()).all():

        raise ValueError(
            "File contains infinite measurements."
        )

    # Check minimum number of measurements.
    if len(df) < MIN_POINTS:

        raise ValueError(
            "File does not contain enough data points."
        )

    # Check that time increases.
    if not (df["Time_s"].diff().iloc[1:] > 0).all():

        raise ValueError(
            "Time values are not strictly increasing."
        )

    # Check that load varies.
    if df["Load_uN"].max() <= df["Load_uN"].min():

        raise ValueError(
            "Load values do not vary."
        )

    df = df.reset_index(drop=True)

    return df

# =========================================================
# 3. GENERATE DETAILED LOAD-DEPTH GRAPH
# =========================================================

def generate_graph(df, file_path):

    # Find maximum load
    max_load_index = df["Load_uN"].idxmax()

    # Separate loading and unloading portions
    loading = df.iloc[:max_load_index + 1]

    unloading = df.iloc[max_load_index:]

    # Create a large figure
    fig, ax = plt.subplots(
        figsize=(FIGURE_WIDTH, FIGURE_HEIGHT)
    )

    # ---------------------------------------------
    # Plot loading portion
    # ---------------------------------------------

    ax.plot(
        loading["Depth_nm"],
        loading["Load_uN"],
        color="blue",
        linewidth=0.8,
        label="Loading",
        solid_joinstyle="round"
    )

    # ---------------------------------------------
    # Plot unloading portion
    # ---------------------------------------------

    if len(unloading) > 1:

        ax.plot(
            unloading["Depth_nm"],
            unloading["Load_uN"],
            color="darkorange",
            linewidth=0.8,
            label="Unloading",
            solid_joinstyle="round"
        )

    # ---------------------------------------------
    # Graph title and axis labels
    # ---------------------------------------------

    ax.set_title(
        f"Nanoindentation Load-Depth Curve\n"
        f"{file_path.name}",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    ax.set_xlabel(
        "Indentation Depth (nm)",
        fontsize=15
    )

    ax.set_ylabel(
        "Load (µN)",
        fontsize=15
    )

    # ---------------------------------------------
    # Detailed axis formatting
    # ---------------------------------------------

    # Display approximately 12 major ticks
    ax.xaxis.set_major_locator(
        ticker.MaxNLocator(nbins=12)
    )

    ax.yaxis.set_major_locator(
        ticker.MaxNLocator(nbins=12)
    )

    # Add minor ticks between major ticks
    ax.xaxis.set_minor_locator(
        ticker.AutoMinorLocator(5)
    )

    ax.yaxis.set_minor_locator(
        ticker.AutoMinorLocator(5)
    )

    # Disable scientific notation and offset labels
    ax.ticklabel_format(
        axis="both",
        style="plain",
        useOffset=False
    )

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=12,
        length=6
    )

    ax.tick_params(
        axis="both",
        which="minor",
        length=3
    )

    # ---------------------------------------------
    # Gridlines
    # ---------------------------------------------

    ax.grid(
        True,
        which="major",
        linestyle="--",
        linewidth=0.6,
        alpha=0.5
    )

    ax.grid(
        True,
        which="minor",
        linestyle=":",
        linewidth=0.4,
        alpha=0.25
    )

    # ---------------------------------------------
    # Show the full data range
    # ---------------------------------------------

    ax.margins(
        x=0.02,
        y=0.03
    )

    ax.legend(
        fontsize=12,
        loc="best"
    )

    fig.tight_layout()

    # ---------------------------------------------
    # Save graph
    # ---------------------------------------------

    output_path = (
        output_folder /
        f"{file_path.stem}_load_depth.png"
    )

    fig.savefig(
        output_path,
        dpi=IMAGE_DPI,
        bbox_inches="tight"
    )

    # Close figure to prevent memory buildup
    plt.close(fig)

    return output_path


# =========================================================
# 4. PROCESS EVERY TEXT FILE
# =========================================================

text_files = sorted(
    file_path
    for file_path in folder.iterdir()
    if file_path.is_file()
    and file_path.suffix.lower() == ".txt"
)

print(f"\nFound {len(text_files)} text files.\n")

successful = 0
skipped = 0

for file_path in text_files:

    print(f"Processing: {file_path.name}")

    try:

        # Read and validate file
        df = load_data(file_path)

        # Generate complete load-depth graph
        output_path = generate_graph(
            df,
            file_path
        )

        successful += 1

        print(
            f"  Graph saved: {output_path.name}"
        )

    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        pd.errors.ParserError,
        UnicodeError,
        OSError
    ) as error:

        skipped += 1

        print(f"  Skipped: {error}")

    print()


# =========================================================
# 5. PRINT SUMMARY
# =========================================================

print("=" * 50)
print("GRAPH GENERATION COMPLETE")
print("=" * 50)

print(f"Total text files: {len(text_files)}")
print(f"Graphs generated: {successful}")
print(f"Files skipped: {skipped}")

print(
    f"\nSaved graphs can be found in:\n"
    f"{output_folder}"
)