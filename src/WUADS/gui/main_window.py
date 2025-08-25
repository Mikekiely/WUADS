from PySide6.QtWidgets import QWidget, QMainWindow, QHBoxLayout, QFileDialog
from .toolbox.toolbox_main import ToolBox
from ..aircraft import Aircraft
from .graphics import graphics

# git is working


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    """ Main Window for WUADS """

    def __init__(self, aircraft):
        super().__init__()
        self.setWindowTitle("WUADS")
        self.aircraft = aircraft
        self.initiate_window()

    def initiate_window(self):
        # Initiate widgets and organize layout
        self.resize(1000, 800)

        # Add Toolbox
        layout = QHBoxLayout()
        self.toolbox = ToolBox(self)
        layout.addWidget(self.toolbox, 1)

        # Add graphics window
        self.graphics = graphics(self)
        self.toolbox.component_changed.connect(self.graphics.update_component)
        self.toolbox.component_selected.connect(self.graphics.handleComponentSelected)
        self.toolbox.component_renamed.connect(self.graphics.handleComponentRenamed)
        self.graphics.plot_aircraft(self.aircraft)
        layout.addWidget(self.graphics, 3)

        # Set layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Menus
        menu = self.menuBar()
        # File Menu
        file_menu = menu.addMenu('&File')
        load_aircraft = file_menu.addAction('Load')
        load_aircraft.triggered.connect(self.load_config)

        save_aircraft = file_menu.addAction('Save')
        save_aircraft.triggered.connect(self.save_config)

        file_menu.addAction('Close')

    def load_config(self, *args):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("*.yml *.yaml")
        file_dialog.exec()
        config_file = file_dialog.selectedFiles()
        self.aircraft = Aircraft(str(config_file[0]))
        self.initiate_window()

    def save_config(self, *args):
        file_dialog = QFileDialog.getSaveFileName(
            parent=self,
            caption='Save Aircraft Configuration File',
            filter='*.yml *.yaml'
        )
        file_name = file_dialog[0]
        self.aircraft.write_config_file(file_name)
