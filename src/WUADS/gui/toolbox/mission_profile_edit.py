from PySide6.QtWidgets import QLineEdit, QDialog, QFormLayout, QLabel, QCheckBox, QComboBox, QDialogButtonBox
from PySide6.QtCore import Signal
from ...mission_segments import *

#TODO: make sure these types actually line up
mission_profile_types = {'Takeoff': 'takeoff',
                      'Climb': 'climb',
                      'Cruise': 'cruise',
                      'Descent': 'descent',
                        'Loiter': 'loiter',
                         'Weight Drop': "weight_drop",
                     'Landing': 'landing'}

mission_profile_classes = {'Takeoff': takeoff,
                           'Climb': climb,
                           'Cruise': cruise,
                           'Descent': descent,
                           'Loiter': loiter,
                           'Weight Drop': weight_drop,
                           'Landing': landing
                           }

class mission_profile_edit(QDialog):
    """
    Handles mission profile info
    """
    title_changed = Signal(str)

    variables = {
            'takeoff': {'thrust_setting': 'Thrust Setting', 'time': 'time (s)'},
            'climb': {'start_velocity': 'Start Velocity (ft/s)', 'end_velocity': 'End Velocity (ft/s)',
                      'start_altitude': 'Start Altitude (ft)', 'end_altitude': 'End Altitude (ft)'},
            'cruise': {'mach': 'Mach Number', 'altitude': 'Altitude (ft)', 'find_range': 'Find Range'},
            'descent': {'weight_fraction': 'Weight Fraction'},
            'loiter': {'altitude': 'Altitude', 'time': 'Time', 'mach': 'Mach'},
            'landing': {'weight_fraction': 'Weight Fraction', 'reserve_fuel_fraction': 'Reserve Fuel Fraction'}
        }
    create_segment = False
    index = 0

    def __init__(self, parent, phase):
        self.parent = parent
        self.aircraft = parent.aircraft
        super().__init__(parent)
        self.setWindowTitle(f'Mission Profile Edit - {phase}')

        form = QFormLayout()
        self.setLayout(form)

        phase_edit = QLineEdit()
        phase_edit.setText(phase)
        form.addRow(QLabel('Segment Title'), phase_edit)

        # Find the correct segment object from mission_profile
        segment_obj = None
        i = 0
        for segment in self.aircraft.mission.mission_profile:
            if segment.title == phase:
                self.index = i
                segment_obj = segment
                self.segment = segment
                seg_type = segment.segment_type
                break
            i += 1

        if not segment_obj:
            self.create_segment = True
            seg_type = mission_profile_types[phase]

        # Add a line for segment type
        line_edit = QLineEdit(seg_type.capitalize())
        line_edit.setReadOnly(True)
        form.addRow(QLabel('Segment Type'), line_edit)

        # index_edit
        self.index_edit = QLineEdit(str(self.index))
        form.addRow(QLabel('Index'), self.index_edit)

        self.phase = phase
        self.fields = {}
        self.fields['title'] = phase_edit

        # Dynamically create input fields based on segment type
        for var, label in self.variables[seg_type].items():
            if var == 'set_range':  # Dropdown menu
                self.fields[var] = QCheckBox()
                if not self.create_segment:
                    self.fields[var].setChecked(segment_obj.find_range)
            else:  # Standard numerical input
                self.fields[var] = QLineEdit()
                if not self.create_segment:
                    val = str(getattr(segment_obj, var, ""))
                else:
                    val = None
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
        input_params = {}
        for var in self.fields:
            if isinstance(self.fields[var], QCheckBox):
                value = self.fields[var].isChecked()
            elif isinstance(self.fields[var], QComboBox):
                value = self.fields[var].currentText()
            else:
                if var == 'title':
                    value = self.fields[var].text()
                else:
                    value = float(self.fields[var].text())
            if not self.create_segment:
                setattr(self.segment, var, value)
            else:
                input_params[var] = value

        if self.create_segment:
            seg_class = mission_profile_classes[self.phase]
            seg = seg_class(**input_params)
            self.aircraft.mission.mission_profile.insert(self.index, seg)
        else:
            if float(self.index_edit.text()) != self.index:
                item = self.aircraft.mission.mission_profile.pop(self.index)
                self.aircraft.mission.mission_profile.insert(int(self.index_edit.text()), item)

        super().accept()  # Close the dialog (if applicable)

    def validate_input(self):
        valid = True
        for var, field in self.fields.items():
            if isinstance(field, QLineEdit):  # Validate numerical inputs
                if var == 'title':
                    try:
                        str(field.text())
                        field.setText(field.text())
                    except ValueError:
                        field.setStyleSheet("border: 1px solid red;")
                        valid = False
                else:
                    try:
                        float(field.text())
                        field.setStyleSheet("")
                    except ValueError:
                        field.setStyleSheet("border: 1px solid red;")
                        valid = False

        try:
            int(self.index_edit.text())
        except ValueError:
            self.index_edit.setStyleSheet("border: 1px solid red;")
            valid = False

        return valid