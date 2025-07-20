import math
import os

from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFileDialog, \
    QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout
from PySide6.QtCore import Signal, Qt


class propulsion_input(QWidget):

    n_engines_changed = Signal(int)

    titles = {"n_engines": "Number of Engines",
              "thrust_sea_level": "Maximum Thrust at \nSea Level (lbs)",
              "sfc_sea_level": "Specific Fuel Consumption \nSea Level (/hr)",
              "thrust_cruise": "Maximum Thrust at \nCruise (lbs)",
              "sfc_cruise": "Specific Fuel Consumption \nCruise (/hr)"}

    def __init__(self, parent):
        self.parent = parent
        self.aircraft = parent.parent.aircraft
        self.prop = self.aircraft.propulsion

        super().__init__(parent)
        form = QFormLayout(self)
        self.form_layout = form
        self.setLayout(form)
        prop_type = self.prop.engine_type

        propulsion_type_select = QComboBox(self)
        propulsion_type_select.addItem('Turbofan')
        propulsion_type_select.addItem('Propeller')
        if prop_type == 'propeller':
            propulsion_type_select.setCurrentIndex(1)

        # TODO add some handling here that adjusts the rest of the inputs

        form.addRow(QLabel('Engine Type'), propulsion_type_select)
        self.populate_form_layout(prop_type)

    def populate_form_layout(self, engine_type):

        form = self.form_layout
        self.input_fields = {}
        print(engine_type)
        if engine_type.lower() == 'turbofan':
            # Add file save
            self.file_input = QLineEdit(self.prop.engine_data_file)
            self.browse_button = QPushButton("Browse")
            self.browse_button.clicked.connect(self.open_engine_data_file)
            # self.browse_button.setFixedWidth(80)
            layout = QVBoxLayout()
            layout.addWidget(self.file_input)
            layout.addWidget(self.browse_button)
            layout.setContentsMargins(0, 0, 0, 0)
            form.addRow("Input Data File:", layout)

            for var in self.titles.keys():
                self.input_fields[var] = QLineEdit()
                form.addRow(QLabel(self.titles[var]), self.input_fields[var])
                if getattr(self.prop, var):
                    self.input_fields[var].setText(str(getattr(self.prop, var)))

            # Handle changing the number of engines
            self.input_fields['n_engines'].editingFinished.connect(self.handle_n_engines_changed)

            # Add accept button
            generate_table = QPushButton('Generate engine performance tables')
            generate_table.clicked.connect(self.generate_engine_performance)
            form.addRow(generate_table)

            # Add reset button
            reset_engine = QPushButton('Reset engine parameters')
            reset_engine.clicked.connect(self.reset_engine)
            form.addRow(reset_engine)

    def open_engine_data_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            self.file_input.setText(file_path)
            self.handle_data_file_changed()

    def handle_data_file_changed(self):
        data_file = self.file_input.text()
        print(data_file)
        if os.path.exists(data_file):
            self.file_input.setStyleSheet("")
            self.prop.load_data_file(data_file)
        else:
            self.file_input.setStyleSheet("border: 1px solid red;")

    def handle_n_engines_changed(self):

        ac = self.parent.parent.aircraft
        n_engines_old = ac.n_engines
        # Validate Input
        self.input_fields['n_engines'].setStyleSheet("")
        try:
            n_engines = int(self.input_fields['n_engines'].text())
            ac.n_engines = n_engines
        except ValueError:
            self.input_fields['n_engines'].setStyleSheet("border: 1px solid red;")
            return

        n_stations_old = math.ceil(n_engines_old/2)
        n_stations_new = math.ceil(n_engines/2)
        if n_stations_old != n_stations_new:
            self.n_engines_changed.emit(n_engines)

        print(f'olds: {n_stations_old}, new: {n_stations_new}')

    def reset_engine(self):
        for item in self.input_fields.values():
            item.setText('')

    # TODO fix bug that doesn't let you reset engine data
    def generate_engine_performance(self):
        # Validates input data, generates engine performance table, displays table

        # Validate input
        if not self.validate_input():
            return

        # Generates engine data
        variables = {"n_engines": 2,
                     "thrust_sea_level": None,
                     "sfc_sea_level": None,
                     "thrust_cruise": None,
                     "sfc_cruise": None}

        # Check if inputs are blank
        for item in variables.keys():
            if not self.input_fields[item].text().strip() == '':
                variables[item] = float(self.input_fields[item].text())

        # Generate engine
        if self.prop.engine_type == 'turbofan':
            kwargs = {
                'thrust_sea_level': variables['thrust_sea_level'],
                'thrust_cruise': variables['thrust_cruise'],
                'sfc_sea_level': variables['sfc_sea_level'],
                'sfc_cruise': variables['sfc_cruise'],
                'engine_type': 'turbofan'
            }

        engine = self.aircraft.generate_propulsion(n_engines=variables['n_engines'], **kwargs)

        # Create Dialogue with tables for thrust and sfc
        engine_display = QDialog()
        engine_display.setWindowTitle("Engine Performance Data")

        thrust_table = QTableWidget()
        thrust_table.setRowCount(len(engine.altitude_ref))
        thrust_table.setColumnCount(len(engine.mach_ref))

        thrust_table.setHorizontalHeaderLabels([str(x) for x in engine.mach_ref])
        thrust_table.setVerticalHeaderLabels([str(x) for x in engine.altitude_ref])
        for row in range(len(engine.altitude_ref)):
            for col in range(len(engine.mach_ref)):
                thrust_table.setItem(row, col, QTableWidgetItem(str(engine.thrust_input[row][col])))

        sfc_table = QTableWidget()
        sfc_table.setRowCount(len(engine.altitude_ref))
        sfc_table.setColumnCount(len(engine.mach_ref))

        sfc_table.setHorizontalHeaderLabels([str(x) for x in engine.mach_ref])
        sfc_table.setVerticalHeaderLabels([str(x) for x in engine.altitude_ref])
        for row in range(len(engine.altitude_ref)):
            for col in range(len(engine.mach_ref)):
                sfc_table.setItem(row, col, QTableWidgetItem(str(engine.sfc_input[row][col])))

        main_layout = QVBoxLayout()

        thrust_label = QLabel("Maximum Thrust (lbs)")
        thrust_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        thrust_label.setAlignment(Qt.AlignCenter)
        # main_layout.addWidget(thrust_label)

        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()
        v_layout.addStretch()
        v_layout.addWidget(thrust_label)
        h_layout.addWidget(QLabel("Altitude (ft)"))
        mach_label = QLabel('Mach Number')
        mach_label.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(mach_label)
        v_layout.addWidget(thrust_table)
        # v_layout.addStretch()
        h_layout.addLayout(v_layout)
        # h_layout.addStretch()
        main_layout.addLayout(h_layout)


        sfc_label = QLabel("Specific Fuel Consumption (hr^-1)")
        sfc_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        sfc_label.setAlignment(Qt.AlignCenter)

        h_layout_sfc = QHBoxLayout()
        v_layout_sfc = QVBoxLayout()
        v_layout_sfc.addWidget(sfc_label)
        h_layout_sfc.addWidget(QLabel("Altitude (ft)"))
        mach_label_sfc = QLabel('Mach Number')
        mach_label_sfc.setAlignment(Qt.AlignCenter)
        v_layout_sfc.addWidget(mach_label_sfc)
        v_layout_sfc.addWidget(sfc_table)
        h_layout_sfc.addLayout(v_layout_sfc)
        main_layout.addLayout(h_layout_sfc)

        # Add buttons on bottom
        # Create the three buttons
        save_button = QPushButton("Save Engine Data")

        # Connect actions
        save_button.clicked.connect(self.save_engine_file)
        # exit_button.clicked.connect(self.reject)

        # Create horizontal layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # pushes buttons to the right
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

        main_layout.addStretch()

        engine_display.setLayout(main_layout)
        engine_display.resize(1200, 700)
        engine_display.exec()

    def save_engine_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Engine Data File",
            "data.xlsx",  # default file name
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return  # user cancelled

            # Ensure file ends with .xlsx
        if not file_path.endswith(".xlsx"):
            file_path += ".xlsx"
        self.prop.write_data_file(file_path)


    def validate_input(self):
        validated = True

        for item in self.input_fields.values():
            try:
                float(item.text())
                item.setStyleSheet("")
            except ValueError:
                if not item.text().strip() == '':
                    item.setStyleSheet("border: 1px solid red;")
                    validated = False
                else:
                    item = None
        return validated


