"""Reproduce the saved threshold-versus-random-forest evaluation without retraining."""

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "app"))

from analysis_scripts import popin_locator, popin_ml


def score_events(truth, events, tolerance=5):
    remaining = set(truth)
    matches, extras = [], []
    for event in sorted(events, key=lambda event: (-event["score"], event["index"])):
        index = event["index"]
        nearby = [target for target in remaining if abs(index - target) <= tolerance]
        if nearby:
            target = min(nearby, key=lambda target: (abs(index - target), target))
            remaining.remove(target)
            matches.append({"predicted": index, "annotated": target, "error": abs(index - target)})
        else:
            extras.append(index)
    return {"matches": matches, "extra_indices": extras, "missed_indices": sorted(remaining)}


def summarize(outcomes):
    matches = [match for outcome in outcomes for match in outcome["matches"]]
    tp = len(matches)
    fp = sum(len(outcome["extra_indices"]) for outcome in outcomes)
    fn = sum(len(outcome["missed_indices"]) for outcome in outcomes)
    precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return {
        "curves": len(outcomes), "true_positives": tp, "false_positives": fp,
        "false_negatives": fn, "precision": precision, "recall": recall,
        "f1": 2 * tp / max(2 * tp + fp + fn, 1),
        "mean_index_error": float(np.mean([match["error"] for match in matches])) if matches else None,
        "location_tolerance_points": 5,
    }


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare():
    bundle = popin_ml.load_model()
    if type(bundle["classifier"]).__name__ != "RandomForestClassifier":
        raise ValueError("The saved model must be a RandomForestClassifier")
    records, audit, file_audit = popin_ml.collect_training_data(
        popin_ml.DEFAULT_DATA, popin_ml.DEFAULT_LABELS)
    membership = {}
    for split, files in bundle["report"]["split_files"].items():
        for name in files:
            if name in membership:
                raise ValueError(f"Overlapping saved splits: {name}")
            membership[name] = split
    names = {path.relative_to(popin_ml.DEFAULT_DATA).as_posix() for path in records}
    if names != set(membership):
        raise ValueError("Current labeled curves differ from the saved model's split membership")

    curves = []
    for path, record in sorted(records.items()):
        name = path.relative_to(popin_ml.DEFAULT_DATA).as_posix()
        algorithm = popin_locator.analyze_file(path)
        first = algorithm["pop_index"]
        algorithm_events = [] if first is None else [{"index": first, "score": 1.0}]
        forest_events = popin_ml.predict(record["curve"], bundle)
        curves.append({
            "file": name, "sha256": sha256(path), "split": membership[name],
            "annotated_indices": sorted(record["indices"]),
            "threshold_algorithm": {
                "threshold_nm": algorithm["threshold"],
                "candidate_count": algorithm["candidate_count"],
                "events": algorithm_events,
                **score_events(record["indices"], algorithm_events),
            },
            "random_forest": {"events": forest_events, **score_events(record["indices"], forest_events)},
        })
    groups = {}
    for split in ("test", "all", "train", "calibration"):
        selected = [curve for curve in curves if split == "all" or curve["split"] == split]
        groups[split] = {method: summarize([curve[method] for curve in selected])
                         for method in ("threshold_algorithm", "random_forest")}

    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return {
        "evaluated_at": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
        "git_revision": revision,
        "working_tree_note": "Source hashes identify evaluated code, including any uncommitted changes.",
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "scipy", "joblib")},
        "model": {"path": str(popin_ml.DEFAULT_MODEL.relative_to(ROOT)),
                  "sha256": sha256(popin_ml.DEFAULT_MODEL), "classifier": "RandomForestClassifier",
                  "feature_schema": bundle["feature_schema"], "threshold": bundle["threshold"]},
        "source_sha256": {str(Path(module.__file__).relative_to(ROOT)): sha256(Path(module.__file__))
                          for module in (popin_locator, popin_ml)} | {"tests/compare_popin.py": sha256(Path(__file__))},
        "labels_sha256": sha256(popin_ml.DEFAULT_LABELS),
        "scanned_files": len(file_audit), "eligible_curves": len(curves),
        "matched_annotations": sum(row["status"] == "matched" for row in audit),
        "unmatched_annotations": sum(row["status"] != "matched" for row in audit),
        "skipped_files": [row for row in file_audit if row["status"] != "matched"],
        "protocol": "Use the threshold algorithm's first candidate and all saved random forest events. "
                    "Match events one-to-one to Excel-matched measurement indices within +/-5 points. "
                    "Match highest classifier scores first. Keep saved split membership and model cutoff; no retraining or tuning.",
        "groups": groups, "curves": curves,
    }


def markdown(report):
    lines = [
        "# Pop-in algorithm comparison", "",
        f"Evaluated: {report['evaluated_at']}. Python {report['python']}.", "",
        "This is a fresh evaluation of the saved random forest against the threshold algorithm. "
        "The model was not retrained or tuned. The held-out test split is the primary comparison.", "",
        "## Held-out test results", "",
        "| Method | Curves | Correct events (TP) | Extra events (FP) | Missed events (FN) | Precision | Recall | F1 | Mean index error |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method, label in (("threshold_algorithm", "Threshold algorithm"), ("random_forest", "Random forest")):
        result = report["groups"]["test"][method]
        error = result["mean_index_error"]
        error_text = f"{error:.3f}" if error is not None else "N/A"
        lines.append(f"| {label} | {result['curves']} | {result['true_positives']} | {result['false_positives']} | "
                     f"{result['false_negatives']} | {result['precision']:.2%} | {result['recall']:.2%} | "
                     f"{result['f1']:.4f} | {error_text} |")
    lines += ["", "Precision is the fraction of detections matched to annotations; recall is the fraction of "
              "annotations detected. F1 balances precision and recall. Mean index error covers matched events only. "
              "These are event metrics, not per-measurement classification accuracy.", "",
              "## Results by split", "",
              "| Split | Curves | Method | Precision | Recall | F1 |", "| --- | ---: | --- | ---: | ---: | ---: |"]
    for split, methods in report["groups"].items():
        for method, result in methods.items():
            lines.append(f"| {split} | {result['curves']} | {method.replace('_', ' ')} | "
                         f"{result['precision']:.2%} | {result['recall']:.2%} | {result['f1']:.4f} |")
    lines += ["", "## Protocol and reproducibility", "", report["protocol"], "",
              f"Scanned {report['scanned_files']} files; evaluated {report['eligible_curves']} eligible curves against "
              f"{report['matched_annotations']} matched annotations. Unmatched annotations: {report['unmatched_annotations']}; "
              f"skipped files: {len(report['skipped_files'])}.", "",
              "The threshold detector uses its existing median + 8 × robust standard deviation rule, searches "
              "from measurement 50, requires positive load changes, and reports the first candidate. "
              f"The random forest uses `{report['model']['feature_schema']}` features and its saved "
              f"cutoff of {report['model']['threshold']:.3f}; it can report multiple events per curve.", "",
              "Run from the repository root with project dependencies installed:", "", "```bash",
              "python tests/compare_popin.py", "python -m pytest tests -q", "```", "",
              "The comparison command replaces this Markdown report and [raw results](popin_comparison.json). "
              "The JSON includes per-curve detections, matches, missed/extra indices, split membership, package versions, "
              "and SHA-256 hashes of the model, annotations, evaluated curves, and source files.", "",
              f"Git revision at evaluation: `{report['git_revision']}`. {report['working_tree_note']}", "",
              "## Limits", "",
              "All-curve and training results are optimistic for the fitted random forest. Calibration curves were used "
              "to choose its cutoff. Held-out membership comes from the saved model's training report; this run does "
              "not independently certify the provenance of those original splits. The test group is small and uses "
              "the available labeled experiments, so results do not establish accuracy on unseen materials. "
              "Unannotated real events count as extra detections. The threshold detector's first-event output and the "
              "forest's multiple-event output reflect their actual GUI behavior.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    report = compare()
    folder = ROOT / "tests" / "reports"
    folder.mkdir(exist_ok=True)
    (folder / "popin_comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (folder / "popin_comparison.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["groups"]["test"], indent=2))
    print(f"Reports saved to {folder}")
