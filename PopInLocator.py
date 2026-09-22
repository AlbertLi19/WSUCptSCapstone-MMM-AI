
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import filedialog
from pathlib import Path


# settings
MULTIPLIER = 8

# Ignore the first 50 points when detecting pop-ins.
BASELINE_START = 50

# Require enough measurements for baseline calculations.
MIN_POINTS = 70
MIN_BASELINE_POINTS = 20


# exception

class InvalidDataError(Exception):
    """Raised when a file contains invalid experimental data."""
    pass


# select file

def select_file():

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Nanoindentation Data File",
        filetypes=[
            ("Text Files", "*.txt"),
            ("All Files", "*.*")
        ]
    )

    root.destroy()

    # User canceled file selection.
    if not file_path:
        print("No file selected.")
        return None

    file = Path(file_path)

    # Verify that the file exists.
    if not file.is_file():
        raise InvalidDataError(
            "The selected file does not exist."
        )

    # Verify the file extension.
    if file.suffix.lower() != ".txt":
        raise InvalidDataError(
            "Invalid file type. Please select a .txt file."
        )

    # Verify that the file is not empty.
    if file.stat().st_size == 0:
        raise InvalidDataError(
            "The selected file is empty."
        )

    return file


# 2. LOAD AND VALIDATE DATA

def load_data(file_path):

    # -----------------------------------------------------
    # Locate the column header automatically.
    # -----------------------------------------------------

    header_line = None

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        errors="replace"
    ) as file:

        # Search the first 100 lines for the column header.
        for line_number, line in enumerate(file):

            if line_number >= 100:
                break

            columns = [
                column.strip().lower()
                for column in line.strip().split("\t")
            ]

            # Expected column order:
            # Depth, Load, Time, Displacement, Force
            if (
                len(columns) == 5
                and "depth" in columns[0]
                and "load" in columns[1]
                and "time" in columns[2]
                and "disp" in columns[3]
                and "force" in columns[4]
            ):

                header_line = line_number
                break

    # Reject files without a recognizable header.
    if header_line is None:

        raise InvalidDataError(
            "Incorrect file format. Expected five columns: "
            "Depth, Load, Time, Displacement, Force."
        )

    # Read the experimental measurements

    df = pd.read_csv(
        file_path,
        sep="\t",
        skiprows=header_line,
        encoding="utf-8-sig",
        encoding_errors="replace",
        on_bad_lines="error"
    )

    # Check that exactly five columns were loaded.
    if len(df.columns) != 5:

        raise InvalidDataError(
            "The file must contain exactly five data columns."
        )

    # Check for missing measurements.
    if df.empty:

        raise InvalidDataError(
            "The file contains no experimental measurements."
        )

    # Rename columns.

    df.columns = [
        "Depth_nm",
        "Load_uN",
        "Time_s",
        "Dis_V",
        "Force_V"
    ]

    # Validate numerical measurements.

    for column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Reject missing or nonnumeric measurements.
    if df.isna().any().any():

        raise InvalidDataError(
            "The file contains missing or nonnumeric measurements."
        )

    # Reject infinite measurements.
    if not np.isfinite(df.to_numpy(dtype=float)).all():

        raise InvalidDataError(
            "The file contains infinite measurements."
        )

    # Verify minimum number of data points.

    if len(df) < MIN_POINTS:

        raise InvalidDataError(
            f"Insufficient data points. "
            f"Found {len(df)}, but at least "
            f"{MIN_POINTS} are required."
        )

    # Verify the time measurements.

    time_difference = df["Time_s"].diff().iloc[1:]

    if not (time_difference > 0).all():

        raise InvalidDataError(
            "Time measurements must be strictly increasing."
        )
    # Verify load and depth measurements.

    if df["Load_uN"].max() <= df["Load_uN"].min():

        raise InvalidDataError(
            "Invalid load measurements. "
            "Load values do not vary."
        )

    if df["Depth_nm"].max() <= df["Depth_nm"].min():

        raise InvalidDataError(
            "Invalid depth measurements. "
            "Depth values do not vary."
        )

    # Reset index so every data point has a valid index.
    df = df.reset_index(drop=True)

    print("\nFile loaded successfully.")
    print("Number of data points:", len(df))

    return df


# 3. find loading section

def get_loading_section(df):

    # Find maximum load.
    max_load_index = int(
        df["Load_uN"].idxmax()
    )

    # Keep loading portion.
    loading = df.iloc[
        :max_load_index + 1
    ].copy()

    # Ensure enough measurements remain after removing
    # the unloading section.
    minimum_loading_points = (
        BASELINE_START + MIN_BASELINE_POINTS
    )

    if len(loading) < minimum_loading_points:

        raise InvalidDataError(
            "Insufficient data in the loading section. "
            f"At least {minimum_loading_points} "
            "loading measurements are required."
        )

    # Make sure the loading section contains depth changes.
    if (
        loading["Depth_nm"].max()
        <= loading["Depth_nm"].min()
    ):

        raise InvalidDataError(
            "The loading section contains no depth variation."
        )

    print("\nMaximum load index:", max_load_index)

    print(
        "Maximum load:",
        loading["Load_uN"].max()
    )

    return loading


# 4. depth load

def calculate_derivatives(loading):

    # Change in depth between consecutive points.
    loading["dDepth_nm"] = (
        loading["Depth_nm"].diff()
    )

    # Change in load between consecutive points.
    loading["dLoad_uN"] = (
        loading["Load_uN"].diff()
    )

    # Calculate approximate derivative.
    #
    # Avoid division by zero or negative load increments.
    valid_load_change = loading["dLoad_uN"].where(
        loading["dLoad_uN"] > 0,
        np.nan
    )

    loading["dDepth_dLoad"] = (
        loading["dDepth_nm"] /
        valid_load_change
    )

    return loading


# 5. pop-in threshold

def calculate_threshold(loading):

    # Ignore the initial measurements.
    baseline_data = (
        loading.iloc[BASELINE_START:]["dDepth_nm"]
        .dropna()
    )

    # Check that enough baseline data exists.
    if len(baseline_data) < MIN_BASELINE_POINTS:

        raise InvalidDataError(
            "Insufficient data to calculate the "
            "pop-in threshold."
        )

    # Convert to a NumPy array.
    baseline_array = baseline_data.to_numpy(
        dtype=float
    )

    # Calculate median depth change.
    median_change = float(
        np.median(baseline_array)
    )

    # Calculate Median Absolute Deviation.
    mad = float(
        np.median(
            np.abs(
                baseline_array - median_change
            )
        )
    )

    # Robust estimate of standard deviation.
    robust_std = float(
        1.4826 * mad
    )

    # Calculate threshold.
    threshold = float(
        median_change +
        MULTIPLIER * robust_std
    )

    # Verify the result is finite.
    if not np.isfinite(threshold):

        raise InvalidDataError(
            "Unable to calculate a valid pop-in threshold."
        )

    print("\nMedian depth change:", median_change)
    print("MAD:", mad)
    print("Robust standard deviation:", robust_std)
    print("Pop-in threshold:", threshold)

    return threshold


# 6. Identify first candidate

def find_first_popin(loading, threshold):

    # Search after the initial 50 measurements.
    search_data = loading.iloc[BASELINE_START:]

    # A candidate must have:
    # 1. An unusually large positive depth change.
    # 2. A positive load change.
    candidates = search_data[
        (search_data["dDepth_nm"] > threshold) &
        (search_data["dLoad_uN"] > 0)
    ]

    print(
        "\nNumber of pop-in candidates:",
        len(candidates)
    )

    # No candidate was detected.
    if candidates.empty:

        print(
            "\nNo pop-in candidates exceeded the threshold."
        )

        return None

    # Select the earliest candidate.
    pop_index = int(
        candidates.index[0]
    )

    pop = loading.loc[pop_index]
    previous = loading.loc[pop_index - 1]

    print("\n--------------------------------")
    print("FIRST POP-IN CANDIDATE DETECTED")
    print("--------------------------------")

    print("Data point:", pop_index)

    print(
        f"Depth before pop-in: "
        f"{previous['Depth_nm']:.3f} nm"
    )

    print(
        f"Depth after pop-in: "
        f"{pop['Depth_nm']:.3f} nm"
    )

    print(
        f"Depth jump: "
        f"{pop['dDepth_nm']:.3f} nm"
    )

    print(
        f"Load: "
        f"{pop['Load_uN']:.3f} µN"
    )

    print(
        f"Load change: "
        f"{pop['dLoad_uN']:.3f} µN"
    )

    print(
        f"Time: "
        f"{pop['Time_s']:.6f} s"
    )

    print(
        f"dDepth/dLoad: "
        f"{pop['dDepth_dLoad']:.4f}"
    )

    return pop_index


# 7. Generate graph

def generate_graph(loading, pop_index, file_path):

    fig, ax = plt.subplots(
        figsize=(14, 9)
    )

    # Plot complete loading curve.
    ax.plot(
        loading["Depth_nm"],
        loading["Load_uN"],
        color="blue",
        linewidth=0.8,
        label="Loading Curve"
    )

    # Mark the detected candidate if one exists.
    if pop_index is not None:

        pop = loading.loc[pop_index]

        ax.scatter(
            pop["Depth_nm"],
            pop["Load_uN"],
            color="red",
            s=100,
            label="First Pop-in Candidate",
            zorder=5
        )

        ax.annotate(
            "First Pop-in Candidate",
            (
                pop["Depth_nm"],
                pop["Load_uN"]
            ),
            xytext=(20, -40),
            textcoords="offset points",
            arrowprops=dict(
                arrowstyle="->",
                color="red"
            )
        )

    ax.set_xlabel(
        "Depth (nm)",
        fontsize=12
    )

    ax.set_ylabel(
        "Load (µN)",
        fontsize=12
    )

    ax.set_title(
        f"Pop-in Detection: {file_path.name}"
    )

    ax.legend()
    ax.grid(True)

    fig.tight_layout()

    plt.show()

    plt.close(fig)


def main():

    try:

        # Select a text file.
        file_path = select_file()

        # User canceled file selection.
        if file_path is None:
            return

        # Load and validate data.
        df = load_data(file_path)

        # Extract loading section.
        loading = get_loading_section(df)

        # Calculate depth and load changes.
        loading = calculate_derivatives(loading)

        # Calculate pop-in threshold.
        threshold = calculate_threshold(loading)

        # Find first candidate.
        pop_index = find_first_popin(
            loading,
            threshold
        )

        # Generate graph.
        generate_graph(
            loading,
            pop_index,
            file_path
        )

    # Invalid data or unsupported format.
    except InvalidDataError as error:

        print("\nDATA ERROR:")
        print(error)

    # File cannot be opened or read.
    except (OSError, UnicodeError) as error:

        print("\nFILE ERROR:")
        print(error)

    # Error while parsing the text file.
    except pd.errors.ParserError as error:

        print("\nFILE FORMAT ERROR:")
        print(error)

    # Error while opening the file selector.
    except tk.TclError as error:

        print("\nFILE SELECTOR ERROR:")
        print(error)

    # Catch any remaining unexpected errors.
    except Exception as error:

        print("\nUNEXPECTED ERROR:")
        print(type(error).__name__)
        print(error)


if __name__ == "__main__":
    main()