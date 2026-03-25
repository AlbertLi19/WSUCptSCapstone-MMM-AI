from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QHBoxLayout, QDoubleSpinBox

# choose NEW manual or old click scale method dialog
class ScaleMethodDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Select Scale Method")

        layout = QVBoxLayout()

        label = QLabel("Select scale input method:")
        layout.addWidget(label)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["Measure on Image", "Enter Manually"])
        layout.addWidget(self.method_combo)

        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_method(self):
        return self.method_combo.currentText()

# old click scale dialog, slightly changed to accept double spinboxes
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
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setDecimals(4)
        self.value_spinbox.setRange(0.0001, 1000000.0)
        self.value_spinbox.setValue(1.0)
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

# new manual entry dialog
class ManualScaleDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Set Scale Manually")

        layout = QVBoxLayout()

        unit_label = QLabel("Select unit:")
        layout.addWidget(unit_label)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Microns", "Nanometers", "Milimeters"])
        layout.addWidget(self.unit_combo)

        value_label = QLabel("Enter the length in your units:")
        layout.addWidget(value_label)

        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setDecimals(4)
        self.value_spinbox.setRange(0.0001, 1000000.0)
        self.value_spinbox.setValue(1.0)
        layout.addWidget(self.value_spinbox)

        pixel_label = QLabel("Enter the equivalent length in pixels:")
        layout.addWidget(pixel_label)

        self.pixel_length_spinbox = QDoubleSpinBox()
        self.pixel_length_spinbox.setDecimals(4)
        self.pixel_length_spinbox.setRange(0.0001, 1000000.0)
        self.pixel_length_spinbox.setValue(1.0)
        layout.addWidget(self.pixel_length_spinbox)

        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_manual_scale_data(self):
        return (
            self.unit_combo.currentText(),
            self.value_spinbox.value(),
            self.pixel_length_spinbox.value()
        )