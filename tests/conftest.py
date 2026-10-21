import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Match the import root used when launching src/app/main.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "app"))


@pytest.fixture
def write_popin_curve(tmp_path):
    """Write deterministic instrument exports without a dataset or saved model."""
    def write(name="curve.txt", points=120, jumps=(), load=None, time=None):
        depth = np.arange(points, dtype=float)
        for index, size in jumps:
            depth[index:] += size
        frame = pd.DataFrame({
            "Depth (nm)": depth,
            "Load (uN)": np.arange(points, dtype=float) * 2 if load is None else load,
            "Time (s)": np.arange(points, dtype=float) / 100 if time is None else time,
            "Depth (V)": np.zeros(points),
            "Load (V)": np.zeros(points),
        })
        path = tmp_path / name
        path.write_text("Instrument export\n" + frame.to_csv(sep="\t", index=False), encoding="utf-8")
        return path
    return write
