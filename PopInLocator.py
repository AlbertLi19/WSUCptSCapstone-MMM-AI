import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

file = "test2.txt"
df = pd.read_csv(file, sep="\t", skiprows=5, encoding_errors="replace")

# pop-in threshold = mean baseline signal + k * stdev
# smaller k means more sensitive, bigger k means more conservative
multiplier = 8

#rename columns so don't have to deal with invalid symbols
df.columns = ["Depth_nm", "Load_uN", "Time_s", "Dis_V", "Force_V"]
for column in df.columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")
df = df.dropna().reset_index(drop=True)
print("First row:\n")
print(df.head())
print("\nNumber of points:\n", len(df))

#find max load location
max_load_index = df["Load_uN"].idxmax()
#everything before max load is loading section
loading = df.loc[:max_load_index].copy()

print("\nMax load index:\n")
print(max_load_index)
print("\nMaximum load:\n")
print(loading["Load_uN"].max())

# need to find change between each point
loading["dDepth_nm"] = loading["Depth_nm"].diff()
loading["dLoad_uN"] = loading["Load_uN"].diff()
loading["dDepth_dLoad"] = (loading["dDepth_nm"] / loading["dLoad_uN"])

# need to estimate normal depth change

#ignore first 50 points to ignore startup behavior
baseline_data = loading.iloc[50:]["dDepth_nm"].dropna()

median_change = float(baseline_data.median())

# Median Absolute Deviation
mad = float(np.median(np.abs(baseline_data - median_change)))

# convert mad to stdev
stdev = float(1.4826 * mad)

# pop-in threshold,
threshold = median_change + multiplier * stdev
print("\nPop-in threshold:\n")
print(threshold)

# find possible pop-ins
candidates = loading[(loading["dDepth_nm"] > threshold) & (loading["dLoad_uN"] > 0)]
print("\nCandidates:\n")
print(candidates[
    [
        "Depth_nm",
        "Load_uN",
        "Time_s",
        "dDepth_nm",
        "dLoad_uN",
        "dDepth_dLoad"
    ]
      ])

if len(candidates) > 0:
    #find biggest sudden increase in depth
    pop_index = candidates["dDepth_nm"].idxmax()
    pop = loading.loc[pop_index]
    previous = loading.loc[pop_index - 1]
    print("Data point:", pop_index)

    print(
        f"Depth before pop-in: "
        f"{previous['Depth_nm']:.3f} nm"
    )

    print(
        f"Depth after pop-in:  "
        f"{pop['Depth_nm']:.3f} nm"
    )

    print(
        f"Depth jump:          "
        f"{pop['dDepth_nm']:.3f} nm"
    )

    print(
        f"Load:                "
        f"{pop['Load_uN']:.3f} uN"
    )

    print(
        f"Load change:         "
        f"{pop['dLoad_uN']:.3f} uN"
    )

    print(
        f"Time:                "
        f"{pop['Time_s']:.6f} s"
    )

    print(
        f"dDepth/dLoad:        "
        f"{pop['dDepth_dLoad']:.4f}"
    )
else:
    print("No pop-in found.")
    pop_index = None

#plot load-depth curve
plt.figure(figsize = (10, 6))
plt.plot(loading["Depth_nm"], loading["Load_uN"], label = "Load-Depth Curve")
if pop_index is not None:
    pop = loading.loc[pop_index]
    plt.scatter(
        pop["Depth_nm"],
        pop["Load_uN"],
        s = 100,
        label = "Detected Pop-in",
        zorder = 5
    )

    plt.annotate(
        "Pop-in",
        (pop["Depth_nm"], pop["Load_uN"]),
        xytext = (20, -40),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->")
    )

plt.xlabel("Depth (nm)")
plt.ylabel("Load (uN)")
plt.legend()
plt.grid(True)
plt.show()








