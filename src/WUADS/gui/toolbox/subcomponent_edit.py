from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QWidget, QDialogButtonBox
from WUADS.components.component import Component

subcomponent_types = {'Nose Landing Gear': 'nose_landing_gear',
                      'Main Landing Gear': 'main_landing_gear',
                      'Air Conditioning': 'air_conditioning' ,
                      'Anti Icing': 'anti_ice',
                      "Auxiliary Power Unit (APU)": 'apu',
                      'Avionics': 'avionics',
                      'Electronics': 'electronics',
                      'Flight Controls': 'flight_controls',
                      'Furnishings': 'furnishings',
                      'Hydraulics': 'hydraulics',
                      'Instruments': 'instruments'}

class subcomponent_edit(QDialog):

    component_info = {'Nose Landing Gear': {'Number of Wheels': 'n_nose_wheels'},
                      'Main Landing Gear': {'Number of Wheels': 'n_main_wheels'},
                      'Air Conditioning': {},
                      'Anti Icing': {},
                      "Auxiliary Power Unit (APU)": {},
                      'Avionics': {'Uninstalled Avionics Weight': 'w_avionics'},
                      'Electronics': {},
                      'Flight Controls': {},
                      'Furnishings': {},
                      'Hydraulics': {},
                      'Instruments': {}}

    cg = [0.0, 0.0, 0.0]

    def __init__(self, component, parent):
        # Initiate Window
        super().__init__(parent)
        self.setWindowTitle('Subsystem Edit')
        self.aircraft = parent.parent.aircraft
        self.title = subcomponent_types[component]
        if self.title in self.aircraft.subsystems.components:
            self.component = self.aircraft.subsystems.components[self.title]
            self.cg = self.component.cg
        else:
            fuse = self.aircraft.aero_components['Fuselage']
            self.cg = cg_default(self.title, fuse)

        # Create Layout
        self.layout = QVBoxLayout()

        # Title Display
        self.layout.addWidget(QLabel('Subsystem Component'))
        self.title_display = QLineEdit()
        self.title_display.setText(component)
        self.title_display.setReadOnly(True)
        self.layout.addWidget(self.title_display)

        # form layout
        form = QFormLayout(self)
        form_widget = QWidget()
        form_widget.setLayout(form)
        self.layout.addWidget(form_widget)

        self.x_edit = QLineEdit()
        self.x_edit.setText(str(self.cg[0]))
        form.addRow(QLabel('X'), self.x_edit)
        self.y_edit = QLineEdit()
        self.y_edit.setText(str(self.cg[1]))
        form.addRow(QLabel('Y'), self.y_edit)
        self.z_edit = QLineEdit()
        self.z_edit.setText(str(self.cg[2]))
        form.addRow(QLabel('Z'), self.z_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        # Set Layout
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setLayout(self.layout)

    def accept(self):

        if not self.validate_input():
            return
        self.cg = [float(self.x_edit.text()), float(self.y_edit.text()), float(self.z_edit.text())]
        self.aircraft.subsystems.components[self.title] = Component({'title': self.title, 'cg': self.cg})
        self.aircraft.set_weight()
        super().accept()


    def validate_input(self):
        # Validate
        valid = True
        try:
            x = float(self.x_edit.text())
        except ValueError:
            self.x_edit.setStyleSheet("border: 1px solid red;")
            valid = False
        try:
            y = float(self.y_edit.text())
        except ValueError:
            self.y_edit.setStyleSheet("border: 1px solid red;")
            valid = False
        try:
            z = float(self.z_edit.text())
        except ValueError:
            self.z_edit.setStyleSheet("border: 1px solid red;")
            valid = False
        return valid

def cg_default(component, fuse):
    r = fuse.height / 2
    l = fuse.length
    component_cg = {'nose_landing_gear': [15, 0, -6],
                        'main_landing_gear': [69.3, 0, -6],
                        'air_conditioning': [62, 0, 0],
                        'anti_ice': [67, 0, 0],
                        'apu': [121, 0, 0],
                        'avionics': [9, 0, 0],
                        'electronics': [12, 0, 0],
                        'flight_controls': [0, 0, 0],
                        'furnishings': [56, 0, 0],
                        'hydraulics': [62, 0, 0],
                        'instruments': [9, 0, 0],
                      }
    cg = component_cg[component]
    cg[0] *= l / 123.31
    cg[1] *= r / 13.17
    cg[2] *= r / 13.17

    return cg
