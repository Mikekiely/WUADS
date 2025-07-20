# TODO Fuel CG
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QLabel, QCheckBox


class aircraft_info(QWidget):
    """
    General aircraft info toolbox
    Use to set
    """

    variable_names = {'Title': 'title',
                      'Design Range': 'design_range',
                      'Cruise Altitude': 'altitude',
                      'Cruise Mach': 'mach',
                      'Maximum Mach': 'max_mach',
                      'Ultimate Load': 'ultimate_load',
                      'Fuel Density': 'rho_fuel'
                      }

    input_types = {'Title': str,
                   'Design Range': float,
                   'Cruise Altitude': float,
                   'Cruise Mach': float,
                   'Maximum Mach': float,
                   'Ultimate Load': float,
                   'Fuel Density': float
                   }

    tool_tips = {'Title': 'Airplane Title',
                   'Design Range': 'Target design range (nmi)',
                   'Cruise Altitude': 'Altitude at cruise (Ft)',
                   'Cruise Mach': 'Mach number at cruise',
                   'Maximum Mach': 'Maximum mach number (~1.05-1.1 time the cruise Mach if unsure)',
                   'Ultimate Load': 'Ultimate load factor (~4.5 if you are unsure)',
                   'Fuel Density': 'Density of the fuel (lbs/gal)'}

    input_fields = {}

    def __init__(self, parent):
        super().__init__(parent)
        self.aircraft = parent.parent.aircraft
        form = QFormLayout(self)
        self.setLayout(form)

        for item in self.variable_names.keys():
            line_edit = QLineEdit()

            if hasattr(self.aircraft, self.variable_names[item]):
                val = str(getattr(self.aircraft, self.variable_names[item]))
            elif hasattr(self.aircraft.mission, self.variable_names[item]):
                val = str(getattr(self.aircraft.mission, self.variable_names[item]))
            else:
                val = ''
            line_edit.textChanged.connect(lambda text, var=item: self.text_changed(var, text))
            line_edit.setText(val)
            self.input_fields[item] = line_edit
            label = QLabel(item)
            label.setToolTip(self.tool_tips[item])
            form.addRow(label, line_edit)

        # Add lock component weights Checkbox
        self.checkbox = QCheckBox('Lock Component Weights')
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.checkbox_toggled)
        form.addRow(self.checkbox)
        # self.checkbox = QCheckBox()

    def checkbox_toggled(self, state):
        self.aircraft.lock_component_weights = state == 2

    def text_changed(self, var, text):
        var_name = self.variable_names[var]

        # Validate Input
        try:
            val = self.input_types[var](text)
            self.input_fields[var].setStyleSheet("")

            # Set Value
            if hasattr(self.aircraft, var_name):
                setattr(self.aircraft, var_name, val)
            elif hasattr(self.aircraft.mission, var_name):
                setattr(self.aircraft.mission, var_name, val)

        except ValueError:
            self.input_fields[var].setStyleSheet("border: 1px solid red;")
        except KeyError:
            pass
