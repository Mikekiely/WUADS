import os

from PySide6.QtWidgets import QListWidget, QFileDialog, QDialog, QVBoxLayout, QTextEdit, QMessageBox
from WUADS.reports import weights_report, mission_profile_report

class analysis_list(QListWidget):

    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.addItems(['Weights Analysis', 'Mission Profile Analysis'])
        self.itemDoubleClicked.connect(self.handleItemSelected)

    def handleItemSelected(self, item):
        selection = item.text()
        if selection == 'Weights Analysis':
            self.generate_weights_report()
        if selection == 'Mission Profile Analysis':
            self.generate_mission_profile_analysis()

    def generate_weights_report(self):
        aircraft = self.parent.parent.aircraft

        file_dialog = QFileDialog(self)
        file_dialog.exec()
        filename = file_dialog.selectedFiles()[0]

        weights_report(aircraft, filename=filename)

        with open(filename, 'r') as file:
            report = file.read()

        report_popup = QDialog()
        report_popup.setWindowTitle('Weights Report')
        layout = QVBoxLayout(self)
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        report_popup.setLayout(layout)
        text_edit.setPlainText(report)
        report_popup.exec()

    def generate_mission_profile_analysis(self):
        aircraft = self.parent.parent.aircraft

        # Check if AVL is in the right folder
        wd = os.getcwd()
        if not os.path.exists(os.path.join(wd, 'avl.exe')):
            error = QMessageBox()
            error.setIcon(QMessageBox.Critical)
            error.setWindowTitle('Error')
            error.setText("Error: AVL file 'avl.exe' not found in current working directory")
            error.setInformativeText(f"Current working directory: {wd}")
            error.exec()
            return

        file_dialog = QFileDialog(self)
        file_dialog.exec()
        filename = file_dialog.selectedFiles()[0]
        aircraft.run_case()
        mission_profile_report(aircraft, filename=filename)

        with open(filename, 'r') as file:
            report = file.read()

        report_popup = QDialog()
        report_popup.setWindowTitle('Weights Report')
        layout = QVBoxLayout(self)
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        report_popup.setLayout(layout)
        text_edit.setPlainText(report)
        report_popup.exec()
