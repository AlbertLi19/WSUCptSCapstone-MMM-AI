from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QPushButton, QGroupBox, QFrame)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import comparison_scripts.kl_divergence as compare_fns
import os
import json
import numpy as np
from comparison_scripts import kl_divergence
from widgets import SelectAnalysisData, InvalidComparisonDialog

PDF_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'PDF Images')

class ComparisonView(QWidget):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        # Our parent is the main view class
        self.main_view = parent
        self._controller = controller

        # Create layout for the comparison view
        self._comparison_layout = QVBoxLayout()
        self.setLayout(self._comparison_layout)
        
        self.kl_divergence = None
        self.wasserstein_distance = None
        self.mean_difference = None
        self.std_dev_difference = None
        self.custom_divergence_score = None

        self.p_samples = None
        self.q_samples = None

        self.p_name = "Not Selected"
        self.q_name = "Not Selected"

        self.comparision_data = None

         # Initalize the UI Components
        self._init_UI()

    """
    Initialize the UI components for the comparison view.
    """
    def _init_UI(self):
        self._populate_comparison()

    """
    This view allows users to compare different segmentation results side by side.
    """
    def _populate_comparison(self):
        """Add comparison instructions to the comparison tab."""
        # Create a scroll area to ensure all content is accessible
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
        """)
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #2b2b2b;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Comparison title
        comp_title = QLabel("Segmentation Comparison Analysis")
        comp_title.setFont(QFont('Arial', 18, QFont.Bold))
        comp_title.setAlignment(Qt.AlignCenter)
        comp_title.setStyleSheet("color: #ffffff; padding: 10px;")
        content_layout.addWidget(comp_title)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        content_layout.addWidget(separator)
        
        # Instructions Group
        instructions_group = QGroupBox("Instructions")
        instructions_group.setFont(QFont('Arial', 11, QFont.Bold))
        instructions_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 2px solid #5d5d5d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        instructions_layout = QVBoxLayout()
        instructions_layout.setSpacing(8)
        
        comp_instructions = QLabel(
            "1. Click 'Load Data' to import segmentation result files for comparison\n"
            "2. Loaded results will appear in the selection list\n"
            "3. Select two datasets you wish to compare\n"
            "4. Click 'Run Comparison' to analyze the differences\n"
            "5. Review the calculated metrics below\n"
            "6. Optionally save comparison snapshots for future reference"
        )
        comp_instructions.setFont(QFont('Arial', 10))
        comp_instructions.setWordWrap(True)
        comp_instructions.setStyleSheet("padding: 10px; background-color: #3d3d3d; border-radius: 5px; color: #ffffff;")
        instructions_layout.addWidget(comp_instructions)
        instructions_group.setLayout(instructions_layout)
        content_layout.addWidget(instructions_group)

        # Action Buttons Group
        actions_group = QGroupBox("Actions")
        actions_group.setFont(QFont('Arial', 11, QFont.Bold))
        actions_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 2px solid #5d5d5d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        # Load Data button
        self.load_data_button = QPushButton("📁 Load Data")
        self.load_data_button.setFont(QFont('Arial', 10))
        self.load_data_button.setMinimumHeight(40)
        self.load_data_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.load_data_button.clicked.connect(self.load_data)

        actions_layout.addWidget(self.load_data_button)

        # add text showing user what they are comparing
        self.compare_text = QLabel(f"Comparing: {self.p_name}  ➔  {self.q_name}")
        self.compare_text.setFont(QFont('Arial', 10))
        self.compare_text.setWordWrap(True)
        self.compare_text.setStyleSheet("padding: 10px; background-color: #3d3d3d; border-radius: 5px; color: #ffffff;")
        instructions_layout.addWidget(self.compare_text)
        self.switch_button = QPushButton("Switch Datasets 🔁")
        self.switch_button.setFont(QFont('Arial', 10))
        self.switch_button.setMinimumHeight(40)
        self.switch_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        actions_layout.addWidget(self.switch_button)
        
        actions_group.setLayout(actions_layout)
        content_layout.addWidget(actions_group)
        self.switch_button.clicked.connect(self.swap_p_and_q)


        # Compare button
        self.compare_button = QPushButton("🔍 Run Comparison")
        self.compare_button.setFont(QFont('Arial', 10))
        self.compare_button.setMinimumHeight(40)
        self.compare_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        actions_layout.addWidget(self.compare_button)
        
        actions_group.setLayout(actions_layout)
        content_layout.addWidget(actions_group)
        self.compare_button.clicked.connect(self.run_comparison)

        # Results Group
        results_group = QGroupBox("Comparison Metrics")
        results_group.setFont(QFont('Arial', 11, QFont.Bold))
        results_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 2px solid #5d5d5d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        results_layout = QVBoxLayout()
        results_layout.setSpacing(12)
        
        # Create styled metric labels
        metrics_style = """
            QLabel {
                background-color: #3d3d3d;
                border: 1px solid #5d5d5d;
                border-radius: 5px;
                padding: 12px;
                font-size: 11pt;
                color: #ffffff;
            }
        """
        
        self.kl_divergence_label = QLabel("📊 KL Divergence: -")
        self.kl_divergence_label.setStyleSheet(metrics_style)
        results_layout.addWidget(self.kl_divergence_label)

        self.wasserstein_distance_label = QLabel("📏 Wasserstein Distance: -")
        self.wasserstein_distance_label.setStyleSheet(metrics_style)
        results_layout.addWidget(self.wasserstein_distance_label)

        self.mean_difference_label = QLabel("Mean Difference: -")
        self.mean_difference_label.setStyleSheet(metrics_style)
        results_layout.addWidget(self.mean_difference_label)

        self.std_dev_difference_label = QLabel("Standard Deviation Difference: -")
        self.std_dev_difference_label.setStyleSheet(metrics_style)
        results_layout.addWidget(self.std_dev_difference_label)

        self.custom_divergence_score_label = QLabel("Custom Divergence Score: -")
        self.custom_divergence_score_label.setStyleSheet(metrics_style)
        results_layout.addWidget(self.custom_divergence_score_label)
        
        results_group.setLayout(results_layout)
        content_layout.addWidget(results_group)
        
        # Add stretch to push everything to the top
        content_layout.addStretch()

        # Set the scroll area widget
        scroll.setWidget(content_widget)
        self._comparison_layout.addWidget(scroll)

    def run_comparison(self):
       
        """Run the comparison metrics on the provided JSON PDFs."""
        if self.p_samples is None or self.q_samples is None:
            dialog = InvalidComparisonDialog(self)
            dialog.exec()
            return
        
        def load_p():
            with open(self.p_samples, "r") as f:
                return json.load(f)
            
        def load_q():
            with open(self.q_samples, "r") as f:
                return json.load(f)
        
        try:
            fit1 = load_p()
            fit2 = load_q()
        except Exception as e:
            print(f"Error loading comparison files: {e}")
            return

        # Extract PDFs
        p_pdf = np.array(fit1["Size"]["pdf"])
        q_pdf = np.array(fit2["Size"]["pdf"])

        # Extract x-values
        p_x = np.array(fit1["Size"]["x"])
        q_x = np.array(fit2["Size"]["x"])

        # Interpolate q_pdf onto p_x (safe even if already aligned)
        from scipy.interpolate import interp1d
        # Use bounds_error=False and fill_value=0.0 to handle range mismatches safely
        q_interp_func = interp1d(q_x, q_pdf, kind='linear', bounds_error=False, fill_value=0.0)
        q_pdf_aligned = q_interp_func(p_x)
        
        # Ensure no negative values from interpolation
        q_pdf_aligned = np.maximum(q_pdf_aligned, 0)

        # Normalize PDFs to sum to 1 (treat as discrete probabilities over p_x)
        p_sum = np.sum(p_pdf)
        q_sum = np.sum(q_pdf_aligned)
        
        if p_sum == 0 or q_sum == 0:
            print("Error: One of the PDFs sums to zero.")
            return

        p_probs = p_pdf / p_sum
        q_probs = q_pdf_aligned / q_sum

        # 1. KL Divergence
        # Add epsilon to avoid log(0) or division by zero
        epsilon = 1e-10
        q_probs_safe = q_probs + epsilon
        # Renormalize after adding epsilon isn't strictly necessary for the ratio but good practice if we treated it as a new distribution
        # Here we just want to avoid division by zero.
        
        # KL = sum(P * log(P / Q))
        # Only compute where p_probs > 0 to avoid 0 * log(0)
        mask = p_probs > 0
        kl = np.sum(p_probs[mask] * np.log(p_probs[mask] / q_probs_safe[mask]))

        # 2. Wasserstein Distance
        # Scipy's wasserstein_distance handles weights.
        wasser = kl_divergence.wasserstein_distance(
            p_x, p_x, u_weights=p_probs, v_weights=q_probs
        )
        emd = wasser

        # 3. Parametric Difference (Mean and Std Dev of the distributions)
        def get_mean_std(x, weights):
            mean = np.average(x, weights=weights)
            variance = np.average((x - mean)**2, weights=weights)
            return mean, np.sqrt(variance)

        p_mean, p_std = get_mean_std(p_x, p_probs)
        q_mean, q_std = get_mean_std(p_x, q_probs)

        mean_diff = np.abs(p_mean - q_mean)
        std_diff = np.abs(p_std - q_std)

        # Custom weighted divergence
        lambda_kl = 1.0
        lambda_w = 1.0
        lambda_param = 0.5
        param_diff = mean_diff + std_diff
        custom_score = lambda_kl * kl + lambda_w * wasser + lambda_param * param_diff

        # Save results in self
        self.kl_divergence = kl
        self.wasserstein_distance = wasser
        self.emd_distance = emd
        self.mean_difference = mean_diff
        self.std_dev_difference = std_diff
        self.custom_divergence_score = custom_score

        # Update UI labels
        self.update_metric_labels()

        # Return metrics dictionary
        return {
            "kl_divergence": kl,
            "wasserstein_distance": wasser,
            "emd_distance": emd,
            "mean_difference": mean_diff,
            "std_dev_difference": std_diff,
            "custom_score": custom_score,
        }
    
    def update_metric_labels(self):
        """Update the metric labels with current values."""
        self.kl_divergence_label.setText(
            f"📊 KL Divergence: {self.kl_divergence:.6f}" if self.kl_divergence is not None else "📊 KL Divergence: -"
        )
        self.wasserstein_distance_label.setText(
            f"📏 Wasserstein Distance: {self.wasserstein_distance:.6f}" if self.wasserstein_distance is not None else "📏 Wasserstein Distance: -"
        )
        self.mean_difference_label.setText(
            f"📈 Mean Difference: {self.mean_difference:.6f}" if self.mean_difference is not None else "📈 Mean Difference: -"
        )
        self.std_dev_difference_label.setText(
            f"📉 Standard Deviation Difference: {self.std_dev_difference:.6f}" if self.std_dev_difference is not None else "📉 Standard Deviation Difference: -"
        )
        self.custom_divergence_score_label.setText(
            f"⭐ Custom Divergence Score: {self.custom_divergence_score:.6f}" if self.custom_divergence_score is not None else "⭐ Custom Divergence Score: -"
        )

    def load_data(self):
        """Load segmentation result files for comparison."""
        analysis_data_selector = SelectAnalysisData(self)
        analysis_data_selector.exec()
        self.comparision_data = analysis_data_selector.get_selected_paths()

        if len(self.comparision_data) < 2:
            self.comparision_data = None
            return
            # display error saying that the user needs to select 2 files
        self.p_samples = self.comparision_data[0]
        self.q_samples = self.comparision_data[1]

        self.p_name = os.path.basename(self.p_samples)
        self.q_name = os.path.basename(self.q_samples)
        self._update_text()


    def swap_p_and_q(self):
        self.p_samples, self.q_samples = self.q_samples, self.p_samples
        self.p_name, self.q_name = self.q_name, self.p_name
        self._update_text()

    def _update_text(self):
        self.compare_text.setText(f"Comparing: {self.p_name}  ➔  {self.q_name}")

        

