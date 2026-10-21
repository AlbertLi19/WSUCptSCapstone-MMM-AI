# Pop-in algorithm comparison

Evaluated: 2026-10-20T21:36:25.687434-07:00. Python 3.9.13.

This is a fresh evaluation of the saved random forest against the threshold algorithm. The model was not retrained or tuned. The held-out test split is the primary comparison.

## Held-out test results

| Method | Curves | Correct events (TP) | Extra events (FP) | Missed events (FN) | Precision | Recall | F1 | Mean index error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Threshold algorithm | 23 | 22 | 0 | 1 | 100.00% | 95.65% | 0.9778 | 1.409 |
| Random forest | 23 | 22 | 3 | 1 | 88.00% | 95.65% | 0.9167 | 0.864 |

Precision is the fraction of detections matched to annotations; recall is the fraction of annotations detected. F1 balances precision and recall. Mean index error covers matched events only. These are event metrics, not per-measurement classification accuracy.

## Results by split

| Split | Curves | Method | Precision | Recall | F1 |
| --- | ---: | --- | ---: | ---: | ---: |
| test | 23 | threshold algorithm | 100.00% | 95.65% | 0.9778 |
| test | 23 | random forest | 88.00% | 95.65% | 0.9167 |
| all | 115 | threshold algorithm | 99.08% | 93.91% | 0.9643 |
| all | 115 | random forest | 89.76% | 99.13% | 0.9421 |
| train | 69 | threshold algorithm | 98.46% | 92.75% | 0.9552 |
| train | 69 | random forest | 88.46% | 100.00% | 0.9388 |
| calibration | 23 | threshold algorithm | 100.00% | 95.65% | 0.9778 |
| calibration | 23 | random forest | 95.83% | 100.00% | 0.9787 |

## Protocol and reproducibility

Use the threshold algorithm's first candidate and all saved random forest events. Match events one-to-one to Excel-matched measurement indices within +/-5 points. Match highest classifier scores first. Keep saved split membership and model cutoff; no retraining or tuning.

Scanned 125 files; evaluated 115 eligible curves against 115 matched annotations. Unmatched annotations: 0; skipped files: 10.

The threshold detector uses its existing median + 8 × robust standard deviation rule, searches from measurement 50, requires positive load changes, and reports the first candidate. The random forest uses `normalized_local_shape_v2` features and its saved cutoff of 0.200; it can report multiple events per curve.

Run from the repository root with project dependencies installed:

```bash
python tests/compare_popin.py
python -m pytest tests -q
```

The comparison command replaces this Markdown report and [raw results](popin_comparison.json). The JSON includes per-curve detections, matches, missed/extra indices, split membership, package versions, and SHA-256 hashes of the model, annotations, evaluated curves, and source files.

## Limits

All-curve and training results are optimistic for the fitted random forest. Calibration curves were used to choose its cutoff. Held-out membership comes from the saved model's training report; this run does not independently certify the provenance of those original splits. The test group is small and uses the available labeled experiments, so results do not establish accuracy on unseen materials. Unannotated real events count as extra detections. The threshold detector's first-event output and the forest's multiple-event output reflect their actual GUI behavior.
