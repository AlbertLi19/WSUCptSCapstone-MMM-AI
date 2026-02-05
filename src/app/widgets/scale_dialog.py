from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QHBoxLayout

class ScaleDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Set Scale")

        # Create layout
        layout = QVBoxLayout()

        # Add label for unit selection
        unit_label = QLabel("Select unit:")
        layout.addWidget(unit_label)

        # Combo box for selecting unit
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Microns", "Nanometers", "Milimeters"])
        layout.addWidget(self.unit_combo)

        # Add label for numerical value selection
        value_label = QLabel("Enter the length:")
        layout.addWidget(value_label)

        # Spin box for selecting the value
        self.value_spinbox = QSpinBox()
        self.value_spinbox.setRange(1, 1000000)
        layout.addWidget(self.value_spinbox)

        # Add OK and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set dialog layout
        self.setLayout(layout)

    def get_scale_data(self):
        """Returns the selected unit and value as a tuple (unit, value)."""
        selected_unit = self.unit_combo.currentText()
        selected_value = self.value_spinbox.value()
        return selected_unit, selected_value
