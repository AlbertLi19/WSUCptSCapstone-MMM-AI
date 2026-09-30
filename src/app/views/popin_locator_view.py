from pathlib import Path

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt
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


class PopInLocatorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_file = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)

        self._init_ui()
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
        button_row.addStretch()
        controls_layout.addLayout(button_row)

        self._file_label = QLabel("No file selected")
        self._file_label.setWordWrap(True)
        controls_layout.addWidget(self._file_label)
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
        self._run_button.setEnabled(True)
        self._results_text.setPlainText("Ready to run pop-in detection.")
        self._draw_empty_plot("Ready to analyze selected file")

    def _run_detection(self):
        if self._selected_file is None:
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
        file_path = result["file_path"]

        ax = self._prepare_axis()
        ax.plot(
            loading["Depth_nm"],
            loading["Load_uN"],
            color="#5dade2",
            linewidth=1.0,
            label="Loading Curve",
        )

        if pop_index is not None:
            pop = loading.loc[pop_index]
            ax.scatter(
                pop["Depth_nm"],
                pop["Load_uN"],
                color="#ff5c5c",
                s=80,
                label="First Pop-in Candidate",
                zorder=5,
            )
            ax.annotate(
                "First Pop-in Candidate",
                (pop["Depth_nm"], pop["Load_uN"]),
                xytext=(20, -35),
                textcoords="offset points",
                color="#ffffff",
                arrowprops={"arrowstyle": "->", "color": "#ff5c5c"},
            )

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
            legend = ax.legend()
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
