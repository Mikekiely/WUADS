from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox


class useful_load_edit(QDialog):
    """
    Handles useful load info
    """

    variables = {'pilots': 'Number',
                 'flight_attendants': 'Number',
                 'passengers': 'Number',
                 'fuel': 'Weight',
                 'cargo': 'Weight'}

    def __init__(self, parent, load_type):
        self.parent = parent
        super().__init__(parent)
        self.setWindowTitle('Useful Load Edit')

        form = QFormLayout()
        self.setLayout(form)

        type_edit = QLineEdit()
        type_edit.setText(load_type)
        type_edit.setReadOnly(True)
        form.addRow(QLabel('Load Type'), type_edit)

        self.variable = self.variables[load_type]
        self.var_edit = QLineEdit()
        form.addRow(QLabel(self.variable), self.var_edit)
        if self.variable == 'Weight':
            self.variable = 'w_' + load_type
        else:
            self.variable = 'n_' + load_type
        val = str(getattr(parent.parent.aircraft.useful_load, self.variable))
        self.var_edit.setText(val)


        self.cg_var = 'cg_' + load_type
        cg_variable = getattr(parent.parent.aircraft.useful_load, self.cg_var)
        self.x_edit = QLineEdit()
        self.x_edit.setText(str(cg_variable[0]))
        x_label = QLabel('X cg')
        x_label.setToolTip('X coordinate at the center of gravity (Ft)')
        form.addRow(x_label, self.x_edit)

        self.y_edit = QLineEdit()
        self.y_edit.setText(str(cg_variable[1]))
        y_label = QLabel('Y cg')
        y_label.setToolTip('Y coordinate at the center of gravity (Ft)')
        form.addRow(y_label, self.y_edit)

        self.z_edit = QLineEdit()
        self.z_edit.setText(str(cg_variable[2]))
        z_label = QLabel('Z cg')
        z_label.setToolTip('Z coordinate at the center of gravity (Ft)')
        form.addRow(z_label, self.z_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addWidget(buttons)

    def accept(self):
        # Validate input
        if not self.validate_input():
            return

        cg = [float(self.x_edit.text()), float(self.y_edit.text()), float(self.z_edit.text())]
        var = float(self.var_edit.text())
        setattr(self.parent.parent.aircraft.useful_load, self.cg_var, cg)
        setattr(self.parent.parent.aircraft.useful_load, self.variable, var)

        if hasattr(self.parent.parent.aircraft.mission, self.variable):
            setattr(self.parent.parent.aircraft.mission, self.variable, var)

        self.parent.parent.aircraft.set_weight()
        super().accept()

    def validate_input(self):
        inputs = [self.var_edit, self.x_edit, self.y_edit, self.z_edit]
        valid = True
        for item in inputs:
            try:
                float(item.text())
                item.setStyleSheet("")
            except ValueError:
                item.setStyleSheet("border: 1px solid red;")
                valid = False

        return valid