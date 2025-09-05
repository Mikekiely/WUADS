from PySide6.QtWidgets import QLineEdit, QLabel, QDialogButtonBox, QWidget, QDialog, QVBoxLayout, QComboBox, \
    QFormLayout, QHBoxLayout
from PySide6.QtCore import Signal

class component_edit(QDialog):
    """ Pop up dialog to edit component parameters"""

    component_info = {"wing": ["Span", "Area", "Taper", "Sweep", "Sweep_location", "Dihedral"],
                      "fuselage": ["Length", "Width", "Height"],
                      "horizontal": ["Span", "Area", "Taper", "Sweep", "Dihedral"],
                      "vertical": ["Span", "Area", "Taper", "Sweep", "Dihedral"],
                      "nacelle": ["Length", "Diameter", "w_engine"]}

    tool_tips = {
        "span": "Tip to tip span (ft)",
        "area": "Total planform area (ft^2)",
        "taper": "Taper ratio, tip chord/root chord",
        "sweep": "Quarter chord sweep angle (deg)",
        "sweep_location": "Location of the sweep angle as a percentage of the chord",
        "dihedral": "Dihedral angle (deg)",
        "length": "Component total length (ft)",
        "width": "Component width in the y direction at thickest point (Ft)",
        "height": "Component height in the z direction at thickest point (Ft)",
        "diameter": "Component diameter at thickest point (Ft)",
        "xle": "X value at component leading edge (ft)",
        "yle": "Y value at component leading edge (ft)",
        "zle": "Z value at component leading edge (ft)",
        "w_engine": "Engine Weight (lbs)"
    }

    variable_labels = {
        "taper": "Taper ratio",
        "ct": "Tip Chord",
        "cr": "Root Chord"
    }

    common_parameters = ['Xle', 'Yle', 'Zle']
    for comp, param in component_info.items():
        param.extend(common_parameters)
    component_changed = Signal(str)
    title_changed = Signal(str, str)
    custom_component = False

    def __init__(self, component, parent, new_component=False):
        # Set Variables, itialize
        self.new_component = new_component
        # TODO Make "Maintain Aspect Ratio" feature
        self.component = component
        self.title = component
        self.changed_variables = {}
        super().__init__(parent)
        self.setWindowTitle("Component Edit")
        aircraft = parent.parent.aircraft
        self.aircraft = aircraft
        if new_component:
            component_type = component.lower()
        else:
            component_type = aircraft.aero_components[component].component_type.lower()
        self.component_type = component_type
        self.layout = QVBoxLayout()

        # Component Type Select
        self.layout.addWidget(QLabel('Component Type'))
        component_type_select = QComboBox()
        component_type_select.setEnabled(False)
        component_type_select.addItems(['Fuselage', 'Wing', 'Horizontal', 'Vertical', 'Nacelle', 'Custom'])
        component_type_select.setCurrentText(component_type.capitalize())
        self.layout.addWidget(component_type_select)

        # Title Edit
        self.layout.addWidget(QLabel('Title'))
        title_edit = QLineEdit()
        if not new_component:
            title_edit.setText(str(component.capitalize()))
        title_edit.textChanged.connect(self.handle_title_changed)
        if component.lower() == 'main wing':
            title_edit.setReadOnly(True)
        self.title_edit = title_edit
        self.layout.addWidget(title_edit)

        # Form for all component info
        form = QFormLayout(self)
        form_widget = QWidget()
        form_widget.setLayout(form)

        # Add all component specific information
        self.input_fields = {}
        self.multi_fields = {}
        self.multi_field_values = {}

        if new_component:
            fields = self.component_info[component]
        else:
            fields = aircraft.aero_components[component].params.keys()
            if component not in self.input_fields.keys():
                self.custom_component = True

        for item in fields:
            item = item.lower()
            if item == 'title':
                continue
            # Get Value
            try:
                if new_component:
                    val = ''
                else:
                    val = getattr(aircraft.aero_components[component], item.lower())
                    if item == 'sweep' or item.startswith('dihedral'):
                        val *= 180 / 3.14159
                        val = round(val, 2)
            except KeyError:
                val = ''

            # Set label and tooltips
            if item in self.variable_labels.keys():
                label = QLabel(self.variable_labels[item])
            else:
                label = QLabel(item.title())

            try:
                label.setToolTip(self.tool_tips[item])
            except KeyError:
                pass

            if isinstance(val, list):
                container = QWidget()
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                line_edits = []
                for v in val:
                    line_edit = QLineEdit(str(v))
                    line_edit.textChanged.connect(lambda _, var=item: self.multi_field_changed(var))
                    layout.addWidget(line_edit)
                    line_edits.append(line_edit)
                self.multi_fields[item] = line_edits
                self.multi_field_values[item] = val

                form.addRow(label, container)
            else:
                line_edit = QLineEdit()
                line_edit.setText(str(val))
                line_edit.textChanged.connect(lambda text, var=item: self.text_changed(var, text))
                form.addRow(label, line_edit)
                self.input_fields[item] = line_edit

        self.layout.addWidget(form_widget)

        # Ok and Cancel Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        widget = QWidget()
        widget.setLayout(self.layout)

        self.setLayout(self.layout)

    # Stores each changed variable
    def text_changed(self, var, text):
        if hasattr(self.changed_variables, var):
            try:
                self.changed_variables[var] = float(text)
                self.input_fields[var].setStyleSheet("")
            except:
                self.input_fields[var].setStyleSheet("border: 1px solid red;")
        else:
            try:
                self.changed_variables[var] = float(text)
                self.input_fields[var].setStyleSheet("")
            except:
                self.input_fields[var].setStyleSheet("border: 1px solid red;")

    def multi_field_changed(self, item):
        # validate input
        value = []
        for line in self.multi_fields[item]:
            text = line.text().strip()
            try:
                value.append(float(text))
                line.setStyleSheet("")
            except ValueError:
                line.setStyleSheet("border: 1px solid red;")
                validated = False

        # value = [line.text() for line in self.multi_fields[item]]
        self.multi_field_values[item] = value

    def handle_title_changed(self, title):
        self.title = title
        self.changed_variables['title'] = title

    # Closes popup and edits component parameters, signals parent to update graphics
    def accept(self):
        if not self.validate_input():
            return

        for key, value in self.multi_field_values.items():
            self.changed_variables[key] = value
        arg = []
        for key in self.changed_variables.keys():
            if not key == 'title':
                arg.append((self.component, key.lower(), self.changed_variables[key]))

        if arg:
            if not self.new_component:
                self.aircraft.update_component(arg)
                self.component_changed.emit(self.component)
            else:
                params = {}
                for line in arg:
                    params[line[1]] = line[2]
                params['title'] = self.title
                self.aircraft.add_component(self.component_type, params)
                self.component_changed.emit(self.title)
                self.title_changed.emit('', self.title)
                super().accept()
                return
        else:
            self.component_changed.emit(self.component)

        if 'title' in self.changed_variables:
            title = self.title
            self.aircraft.aero_components[title] = self.aircraft.aero_components[self.component]
            self.aircraft.aero_components.pop(self.component)
            self.aircraft.update_component([(title, 'title', title)])
            self.title_changed.emit(self.component, self.title)
        super().accept()

    def validate_input(self):
        validated = True
        for label, line_edit in self.input_fields.items():
            text = line_edit.text().strip()
            if not text:
                line_edit.setStyleSheet("border: 1px solid red;")
            try:
                if label == 'title' or label == 'component_type' or label == 'attachment' or label == 'definition_type':
                    str(text)
                else:
                    float(text)
                line_edit.setStyleSheet("")
            except ValueError:
                line_edit.setStyleSheet("border: 1px solid red;")
                validated = False

        if 'title' in self.changed_variables and self.new_component:

            if self.changed_variables['title'] in self.aircraft.aero_components:
                self.title_edit.setStyleSheet("border: 1px solid red;")
                validated = False

        return validated