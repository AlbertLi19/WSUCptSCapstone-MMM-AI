from pathlib import Path

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis_scripts.popin_locator import InvalidDataError, analyze_file
from analysis_scripts import popin_ml


class ModelWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            self.succeeded.emit(self.operation())
        except Exception as error:
            self.failed.emit(f"{type(error).__name__}: {error}")
        finally:
            self.finished.emit()


class PopInLocatorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_file = None
        self._model = None
        self._model_thread = None
        self._model_worker = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)

        self._init_ui()
        if popin_ml.DEFAULT_MODEL.exists() or popin_ml.BUNDLED_MODEL.exists():
            try:
                self._model = popin_ml.load_model()
                self._model_label.setText("Normalized shape model ready. Select a file to run either detection method.")
            except Exception as error:
                self._model_label.setText(f"Saved model could not be loaded: {error}. Click Train Shape Model to rebuild it.")
        self._update_buttons()
        self._draw_empty_plot("No pop-in data loaded")

    def _init_ui(self):
        title = QLabel("Pop-in Locator")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(title)

        controls_group = QGroupBox("Nanoindentation Data")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(10)

        button_row = QHBoxLayout()
        self._select_file_button = QPushButton("Select File")
        self._select_file_button.setMinimumHeight(36)
        self._select_file_button.clicked.connect(self._select_file)
        button_row.addWidget(self._select_file_button)

        self._run_button = QPushButton("Run Detection")
        self._run_button.setMinimumHeight(36)
        self._run_button.setEnabled(False)
        self._run_button.clicked.connect(self._run_detection)
        button_row.addWidget(self._run_button)
        self._create_model_button = QPushButton("Train Shape Model")
        self._create_model_button.setToolTip(
            "Scan all training text files, skip invalid or unannotated curves, and train using normalized shape.")
        self._create_model_button.setMinimumHeight(36)
        self._create_model_button.clicked.connect(self._create_model)
        button_row.addWidget(self._create_model_button)

        self._run_model_button = QPushButton("Run Model")
        self._run_model_button.setMinimumHeight(36)
        self._run_model_button.clicked.connect(self._run_model)
        button_row.addWidget(self._run_model_button)
        button_row.addStretch()
        controls_layout.addLayout(button_row)

        self._file_label = QLabel("No file selected")
        self._file_label.setWordWrap(True)
        controls_layout.addWidget(self._file_label)
        self._model_label = QLabel("No model available. Click Train Shape Model to train from the Excel labels and curves.")
        self._model_label.setWordWrap(True)
        controls_layout.addWidget(self._model_label)
        self._layout.addWidget(controls_group)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        results_group = QGroupBox("Detection Results")
        results_layout = QVBoxLayout(results_group)
        self._results_text = QTextEdit()
        self._results_text.setReadOnly(True)
        self._results_text.setMinimumWidth(360)
        self._results_text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._results_text.setStyleSheet(
            "QTextEdit { background-color: #1f1f1f; color: #ffffff; "
            "border: 1px solid #5d5d5d; border-radius: 4px; padding: 8px; }"
        )
        self._results_text.setPlainText("Select a .txt file to begin.")
        results_layout.addWidget(self._results_text)
        content_row.addWidget(results_group, 1)

        graph_group = QGroupBox("Load-Depth Plot")
        graph_layout = QVBoxLayout(graph_group)
        self._figure = Figure(figsize=(8, 5), tight_layout=True)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        graph_layout.addWidget(self._canvas)
        content_row.addWidget(graph_group, 2)

        self._layout.addLayout(content_row, 1)

    def _select_file(self):
        start_dir = self._default_data_directory()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nanoindentation Data File",
            str(start_dir),
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        self._selected_file = Path(file_path)
        self._file_label.setText(str(self._selected_file))
        self._update_buttons()
        self._results_text.setPlainText("Ready. Choose Run Detection for the algorithm or Run Model for machine learning.")
        self._draw_empty_plot("Ready to analyze selected file")

    @property
    def model_busy(self):
        return self._model_thread is not None

    def _update_buttons(self):
        self._select_file_button.setEnabled(not self.model_busy)
        self._run_button.setEnabled(not self.model_busy and self._selected_file is not None)
        self._create_model_button.setEnabled(not self.model_busy)
        self._run_model_button.setEnabled(
            not self.model_busy and self._selected_file is not None and self._model is not None)

    def _start_model_work(self, operation, success):
        self._model_thread = QThread(self)
        self._model_worker = ModelWorker(operation)
        self._model_worker.moveToThread(self._model_thread)
        self._model_thread.started.connect(self._model_worker.run)
        self._model_worker.succeeded.connect(success)
        self._model_worker.failed.connect(self._model_failed)
        self._model_worker.finished.connect(self._model_thread.quit)
        self._model_worker.finished.connect(self._model_worker.deleteLater)
        self._model_thread.finished.connect(self._model_work_finished)
        self._model_thread.finished.connect(self._model_thread.deleteLater)
        self._update_buttons()
        self._model_thread.start()

    def _model_work_finished(self):
        self._model_thread = None
        self._model_worker = None
        self._update_buttons()

    def _model_failed(self, message):
        self._model_label.setText("Model operation failed. See the error below.")
        self._show_error("Model error", message)

    def _create_model(self):
        if self.model_busy:
            return
        self._model_label.setText("Training normalized shape model and evaluating held-out curves…")
        self._results_text.setPlainText(
            "Scanning all training text files and matching Excel load/depth labels…\n"
            "Invalid files and curves without matching annotations will be skipped.")
        self._start_model_work(lambda: (popin_ml.train(), popin_ml.load_model()), self._model_created)

    def _model_created(self, result):
        report, self._model = result
        test = report["test"]
        self._model_label.setText("Normalized shape model saved. Select a file, then choose Run Detection or Run Model.")
        self._results_text.setPlainText(
            f"Shape model trained from {report['annotation_count']} matched annotations.\n"
            f"Text files scanned: {report.get('scanned_files', report['labeled_curves'])}\n"
            f"Eligible labeled curves: {report['labeled_curves']}\n"
            f"Files skipped: {len(report.get('skipped_files', []))}\n"
            f"Unmatched Excel annotations skipped: {report.get('unmatched_annotation_count', 0)}\n"
            "Features: normalized local curve shape; absolute load/depth coordinates excluded.\n"
            f"Training curves: {len(report['split_files']['train'])}\n"
            f"Held-out test curves: {len(report['split_files']['test'])}\n"
            f"Event precision: {test['precision']:.1%}\n"
            f"Event recall: {test['recall']:.1%}\n"
            f"F1: {test['f1']:.3f} (within ±5 measurements)\n\n"
            f"Detection score cutoff: {report['threshold']:.3f} (chosen on calibration curves)\n\n"
            f"Saved model: {popin_ml.DEFAULT_MODEL}\n"
            "The model reloads when the application reopens.\n"
            "Select a text file to predict its pop-in candidates.\n\n"
            + "\n".join(f"Skipped {row['file']}: {row['reason']}" for row in report.get('skipped_files', [])))

    def _run_model(self):
        if self.model_busy or self._selected_file is None or self._model is None:
            return
        file_path, model = self._selected_file, self._model
        def operation():
            curve = popin_ml.load_curve(file_path)
            return file_path, curve, popin_ml.predict(curve, model)
        self._model_label.setText("Predicting pop-in locations…")
        self._start_model_work(operation, self._display_model_results)

    def _display_model_results(self, result):
        file_path, curve, events = result
        self._model_label.setText("Model ready. Prediction complete.")
        lines = [f"File: {file_path.name}", "Method: Machine learning (normalized shape)",
                 f"Data points: {len(curve)}", f"Pop-in candidates: {len(events)}",
                 "Indices are zero-based numeric measurements.",
                 "Scores are classifier votes, not calibrated probabilities.", ""]
        for number, event in enumerate(events, 1):
            lines.extend([f"Candidate {number}: data point {event['index']}",
                          f"Depth: {event['depth_nm']:.5f} nm",
                          f"Load: {event['load_uN']:.5f} uN",
                          f"Time: {event['time_s']:.6f} s",
                          f"Score: {event['score']:.3f}", ""])
        if not events:
            lines.append("No pop-in candidates exceed the learned threshold.")
        self._results_text.setPlainText("\n".join(lines))
        loading = popin_ml.loading(curve)
        self._draw_popin_plot(file_path, loading[:, 0], loading[:, 1], events)

    def _run_detection(self):
        if self.model_busy or self._selected_file is None:
            return

        try:
            result = analyze_file(self._selected_file)
        except InvalidDataError as error:
            self._show_error("Data error", str(error))
            return
        except (OSError, UnicodeError) as error:
            self._show_error("File error", str(error))
            return
        except pd.errors.ParserError as error:
            self._show_error("File format error", str(error))
            return
        except Exception as error:
            self._show_error("Unexpected error", f"{type(error).__name__}: {error}")
            return

        self._display_results(result)
        self._draw_result_plot(result)

    def _display_results(self, result):
        loading = result["loading"]
        pop_index = result["pop_index"]
        threshold = result["threshold"]
        file_path = result["file_path"]

        lines = [
            f"File: {file_path.name}",
            "Method: Threshold algorithm",
            f"Data points: {len(result['data'])}",
            f"Loading points: {len(loading)}",
            f"Maximum load index: {int(loading['Load_uN'].idxmax())}",
            f"Maximum load: {loading['Load_uN'].max():.3f} uN",
            f"Pop-in threshold: {threshold:.6f} nm",
            f"Pop-in candidates: {result['candidate_count']}",
        ]

        if pop_index is None:
            lines.extend(["", "No pop-in candidates exceeded the threshold."])
        else:
            pop = loading.loc[pop_index]
            previous = loading.loc[pop_index - 1]
            lines.extend(
                [
                    "",
                    "First pop-in candidate detected",
                    f"Data point: {pop_index}",
                    f"Depth before pop-in: {previous['Depth_nm']:.3f} nm",
                    f"Depth after pop-in: {pop['Depth_nm']:.3f} nm",
                    f"Depth jump: {pop['dDepth_nm']:.3f} nm",
                    f"Load: {pop['Load_uN']:.3f} uN",
                    f"Load change: {pop['dLoad_uN']:.3f} uN",
                    f"Time: {pop['Time_s']:.6f} s",
                    f"dDepth/dLoad: {pop['dDepth_dLoad']:.4f}",
                ]
            )

        self._results_text.setPlainText("\n".join(lines))

    def _draw_result_plot(self, result):
        loading = result["loading"]
        pop_index = result["pop_index"]
        events = []
        if pop_index is not None:
            pop = loading.loc[pop_index]
            events.append({"depth_nm": pop["Depth_nm"], "load_uN": pop["Load_uN"]})
        self._draw_popin_plot(result["file_path"], loading["Depth_nm"], loading["Load_uN"], events)

    def _draw_popin_plot(self, file_path, depth, load, events):
        """Use one loading curve, scale, and style for either detector."""
        ax = self._prepare_axis()
        ax.plot(depth, load, color="#5dade2", linewidth=1.0, label="Loading Curve")
        # Fix limits from the curve alone so candidate locations cannot change
        # the scale when switching methods, including when no event is found.
        ax.margins(x=0.05, y=0.05)
        ax.set_xlim(ax.get_xlim())
        ax.set_ylim(ax.get_ylim())
        if events:
            ax.scatter([e["depth_nm"] for e in events], [e["load_uN"] for e in events],
                       color="#ff5c5c", s=80, zorder=5, label="Pop-in Candidates")
            for number, event in enumerate(events, 1):
                ax.annotate(str(number), (event["depth_nm"], event["load_uN"]),
                            xytext=(6, 8), textcoords="offset points", color="#ffffff")
        ax.set_xlabel("Depth (nm)", color="#ffffff")
        ax.set_ylabel("Load (uN)", color="#ffffff")
        ax.set_title(f"Pop-in Detection: {file_path.name}", color="#ffffff")
        self._style_axis(ax)
        self._canvas.draw_idle()

    def _draw_empty_plot(self, message):
        ax = self._prepare_axis()
        ax.text(
            0.5,
            0.5,
            message,
            color="#ffffff",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        self._style_axis(ax, show_legend=False)
        self._canvas.draw_idle()

    def _prepare_axis(self):
        self._figure.clear()
        self._figure.patch.set_facecolor("#2b2b2b")
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#2b2b2b")
        return ax

    def _style_axis(self, ax, show_legend=True):
        ax.grid(True, color="#555555", alpha=0.45)
        ax.tick_params(colors="#ffffff")
        for spine in ax.spines.values():
            spine.set_color("#9a9a9a")

        if show_legend:
            legend = ax.legend(loc="upper left")
            if legend is not None:
                legend.get_frame().set_facecolor("#3d3d3d")
                legend.get_frame().set_edgecolor("#5d5d5d")
                for text in legend.get_texts():
                    text.set_color("#ffffff")

    def _show_error(self, title, message):
        self._results_text.setPlainText(f"{title}\n\n{message}")
        self._draw_empty_plot("No graph available")

    def _default_data_directory(self):
        try:
            project_root = Path(__file__).resolve().parents[3]
        except IndexError:
            return Path.home()

        data_dir = project_root / "data" / "Pop-in data"
        if data_dir.is_dir():
            return data_dir

        return Path.home()
