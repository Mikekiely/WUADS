from PySide6.QtWidgets import QLineEdit, QDialog, QFormLayout, QLabel, QCheckBox, QComboBox, QDialogButtonBox
#TODO: make sure these types actually line up
mission_profile_types = {'Takeoff': 'takeoff',
                      'Climb': 'climb',
                      'Cruise': 'cruise',
                      'Descent': 'descent',
                        'Loiter': 'loiter',
                         'Weight Drop': "weight_drop",
                     'Landing': 'landing'}

class mission_profile_edit(QDialog):
    """
    Handles mission profile info
    """


    variables = {
            'takeoff': {'thrust_setting': 'Thrust Setting', 'time': 'time (s)'},
            'climb': {'start_velocity': 'Start Velocity (knots)', 'end_velocity': 'End Velocity (knots)',
                      'start_altitude': 'Start Altitude (ft)', 'end_altitude': 'End Altitude (ft)',
                      'best_climb': 'Best Climb (Yes/No)'},
            'cruise': {'mach_number': 'Mach Number', 'altitude': 'Altitude (ft)', 'range_mode': 'Range Mode'},
            'descent': {'weight_fraction': 'Weight Fraction'},
            'loiter': {'Altitude', 'Time', 'Mach'},
            'landing': {'weight_fraction': 'Weight Fraction', 'reserve_fuel_fraction': 'Reserve Fuel Fraction'}
        }

    def __init__(self, parent, phase):
        self.parent = parent
        self.aircraft = parent.aircraft
        super().__init__(parent)
        self.setWindowTitle(f'Mission Profile Edit - {phase}')

        form = QFormLayout()
        self.setLayout(form)

        phase_edit = QLineEdit()
        phase_edit.setText(phase)
        phase_edit.setReadOnly(True)
        form.addRow(QLabel('Phase'), phase_edit)
        self.phase = phase
        self.fields = {}

        # Find the correct segment object from mission_profile
        segment_obj = None
        for segment in self.aircraft.mission.mission_profile:
            if segment.title == phase:
                segment_obj = segment
                self.segment = segment
                break

        if not segment_obj:
            print(f"Error: No mission segment found for phase '{phase}'")
            return

        # Dynamically create input fields based on segment type
        segment_type = segment_obj.segment_type
        for var, label in self.variables[segment_type].items():
            if var == 'best_climb':  # Boolean checkbox
                self.fields[var] = QCheckBox()
                self.fields[var].setChecked(getattr(segment_obj, var, False))
            elif var == 'range_mode':  # Dropdown menu
                self.fields[var] = QComboBox()
                self.fields[var].addItems(["Max Range","Custom Range"])
                self.fields[var].setCurrentText(getattr(segment_obj, var, "Max Range"))
            else:  # Standard numerical input
                self.fields[var] = QLineEdit()
                val = str(getattr(segment_obj, var, ""))
                self.fields[var].setText(val)

            form.addRow(QLabel(label), self.fields[var])

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addWidget(buttons)

    def accept(self):
        if not self.validate_input():
            return

        # Save values to mission profile
        for var in self.fields:
            if isinstance(self.fields[var], QCheckBox):
                value = self.fields[var].isChecked()
            elif isinstance(self.fields[var], QComboBox):
                value = self.fields[var].currentText()
            else:
                value = float(self.fields[var].text())

            setattr(self.segment, var, value)

            super().accept()  # Close the dialog (if applicable)

    def validate_input(self):
        valid = True
        for var, field in self.fields.items():
            if isinstance(field, QLineEdit):  # Validate numerical inputs
                try:
                    float(field.text())
                    field.setStyleSheet("")
                except ValueError:
                    field.setStyleSheet("border: 1px solid red;")
                    valid = False
        return valid