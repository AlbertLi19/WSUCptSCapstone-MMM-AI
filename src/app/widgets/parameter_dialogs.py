from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout, QComboBox, QStackedWidget, QFormLayout
    
class MinParticleAreaDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Set Min. Particle Area")

        # Create layout
        layout = QVBoxLayout()

        # Add label for numerical value selection
        value_label = QLabel("Enter the minimum particle area:")
        layout.addWidget(value_label)

        # Spin box for selecting the value
        self.value_spinbox = QSpinBox()
        self.value_spinbox.setRange(0, 100)
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

    def get_min_particle_area(self):
        selected_value = self.value_spinbox.value()
        return selected_value
    
class FootprintTypeDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Select Footprint Type")

        # Create layout
        layout = QVBoxLayout()

        # Add label for numerical value selection
        value_label = QLabel("Footprint Type:")
        layout.addWidget(value_label)

        # Combo box for selecting the value
        self.value_combobox = QComboBox()
        self.value_combobox.addItems(['Disk', 'Ellipse'])
        self.value_combobox.currentIndexChanged.connect(self.update_stack)
        layout.addWidget(self.value_combobox)

        # Changable menu for other variables
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        #Disk variables
        self._dr_widget = QWidget()
        self._dr_form = QFormLayout()
        self._dr_widget.setLayout(self._dr_form)
        self._dr_edit = QSpinBox()
        self._dr_edit.setValue(1)
        self._dr_edit.setRange(1,10)
        self._dr_form.addRow('Disk Radius:', self._dr_edit)
        self._stack.addWidget(self._dr_widget)

        #Ellipse variables
        self._ellipse_widget = QWidget()
        self._ellipse_form = QFormLayout()
        self._ellipse_widget.setLayout(self._ellipse_form)
        self._ew_edit = QSpinBox()
        self._ew_edit.setValue(5)
        self._ellipse_form.addRow('Ellipse Width:', self._ew_edit)
        self._eh_edit = QSpinBox()
        self._eh_edit.setValue(3)
        self._ellipse_form.addRow('Ellipse Height:', self._eh_edit)
        self._stack.addWidget(self._ellipse_widget)

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

    def update_stack(self):
        if self.value_combobox.currentIndex() == 0:
            self._stack.setCurrentIndex(0)
        else:
            self._stack.setCurrentIndex(1)

    def get_footprint_type(self):
        footprint_num = self.value_combobox.currentIndex()
        footprint_name = self.value_combobox.currentText()
        disk_radius = self._dr_edit.value()
        ellipse_width = self._ew_edit.value()
        ellipse_height = self._eh_edit.value()
        return footprint_num, footprint_name, disk_radius, ellipse_width, ellipse_height

class ThresholdTypeDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Select Threshold Type")

        # Create layout
        layout = QVBoxLayout()

        type_label = QLabel("Threshold Type:")
        layout.addWidget(type_label)

        self.value_combobox = QComboBox()
        self.value_combobox.addItems(['Global','Adaptive Mean','Adaptive Gaussian',"Otsu's"])
        self.value_combobox.currentIndexChanged.connect(self.update_stack)
        layout.addWidget(self.value_combobox)

        # Changable menu for other variables
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        #Global variables
        self._global_widget = QWidget()
        self._global_form = QFormLayout()
        self._global_widget.setLayout(self._global_form)
        self._it_edit = QSpinBox()
        self._it_edit.setRange(0,255)
        self._it_edit.setValue(127)
        self._global_form.addRow("Intensity Threshold:",self._it_edit)
        self._stack.addWidget(self._global_widget)

        #Adaptive variables
        self._adaptive_widget = QWidget()
        self._adaptive_form = QFormLayout()
        self._adaptive_widget.setLayout(self._adaptive_form)
        self._blocksize_edit = QSpinBox()
        self._blocksize_edit.setRange(1,100)
        self._blocksize_edit.setValue(11)
        self._c_edit = QSpinBox()
        self._c_edit.setRange(1,100)
        self._c_edit.setValue(2)
        self._adaptive_form.addRow("Block Size:",self._blocksize_edit)
        self._adaptive_form.addRow("C",self._c_edit)
        self._stack.addWidget(self._adaptive_widget)

        #Empty widget (no variables)
        self._stack.addWidget(QWidget())

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

    def update_stack(self):
        if self.value_combobox.currentIndex() == 0:
            self._stack.setCurrentIndex(0)
        elif self.value_combobox.currentIndex() == 1 or self.value_combobox.currentIndex() == 2:
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(2)

    def get_threshold_type(self):
        thresh_num = self.value_combobox.currentIndex()
        thresh_name = self.value_combobox.currentText()
        intensity_threshold = self._it_edit.value()
        block_size = self._blocksize_edit.value()
        c = self._c_edit.value()
        return thresh_num, thresh_name, intensity_threshold, block_size, c
    
class BlurTypeDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setFont(parent.font())
        self.setWindowTitle("Select Blur Type")

        # Create layout
        layout = QVBoxLayout()

        # Add label for numerical value selection
        value_label = QLabel("Blur Type:")
        layout.addWidget(value_label)

        # Combo box for selecting the value
        self.value_combobox = QComboBox()
        self.value_combobox.addItems(['Averaging','Gaussian','Median', 'Bilateral Filtering'])
        self.value_combobox.currentIndexChanged.connect(self.update_stack)
        layout.addWidget(self.value_combobox)

        # Changable menu for other variables
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Smooth kernel size variable
        self._sk_widget = QWidget()
        self._sk_form = QFormLayout()
        self._sk_widget.setLayout(self._sk_form)
        self._sk_edit = QSpinBox()
        self._sk_edit.setSingleStep(2)
        self._sk_edit.setRange(1,99)
        self._sk_edit.setValue(5)
        self._sk_form.addRow('Smooth Kernel Size:', self._sk_edit)
        self._stack.addWidget(self._sk_widget)

        # Bilateral filtering variables
        self._bf_widget = QWidget()
        self._bf_form = QFormLayout()
        self._bf_widget.setLayout(self._bf_form)
        self._d_edit = QSpinBox()
        self._d_edit.setValue(9)
        self._bf_form.addRow('d:', self._d_edit)
        self._sc_edit = QSpinBox()
        self._sc_edit.setValue(75)
        self._bf_form.addRow('Sigma Colo:', self._sc_edit)
        self._ss_edit = QSpinBox()
        self._ss_edit.setValue(75)
        self._bf_form.addRow('Sigma Space', self._ss_edit)
        self._stack.addWidget(self._bf_widget)

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

    def update_stack(self):
        index = self.value_combobox.currentIndex()
        if  index >= 0 and index <= 2:
            self._stack.setCurrentIndex(0)
        else:
            self._stack.setCurrentIndex(1)

    def get_blur_type(self):
        blur_num = self.value_combobox.currentIndex()
        blur_name = self.value_combobox.currentText()
        smooth_kernel_size = self._sk_edit.value()
        if smooth_kernel_size % 2 == 0: #smooth kernel size cannot be even
            smooth_kernel_size += 1
        d = self._d_edit.value()
        sigma_color = self._sc_edit.value()
        sigma_space = self._ss_edit.value()
        return blur_num, blur_name, smooth_kernel_size, d, sigma_color, sigma_space