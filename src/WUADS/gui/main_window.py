from PySide6.QtWidgets import QWidget, QMainWindow, QHBoxLayout, QFileDialog
from .toolbox.toolbox_main import ToolBox
from ..aircraft import Aircraft
from .graphics import graphics


class MainWindow(QMainWindow):
    """ Main Window for WUADS """

    class MainWindow(QMainWindow):
        """ Main Window for WUADS """

        def __init__(self, aircraft):
            super().__init__()
            self.setWindowTitle("WUADS")
            self.resize(1000, 800)

            self.aircraft = aircraft
            self.toolbox = None
            self.graphics = None

            # build menus once
            self._init_menus()

            # build first layout
            self.initiate_window()

        def _init_menus(self):
            """Menus are only created once"""
            menu = self.menuBar()
            file_menu = menu.addMenu('&File')

            load_aircraft = file_menu.addAction('Load')
            load_aircraft.triggered.connect(self.load_config)

            save_aircraft = file_menu.addAction('Save')
            save_aircraft.triggered.connect(self.save_config)

            file_menu.addAction('Close')

        def initiate_window(self):
            """(Re)builds the central widget with toolbox + graphics"""

            # clear the old central widget if it exists
            old_widget = self.centralWidget()
            if old_widget is not None:
                self.setCentralWidget(None)
                old_widget.deleteLater()
                self.toolbox = None
                self.graphics = None

            # rebuild
            layout = QHBoxLayout()

            from toolbox import ToolBox  # make sure this is your toolbox
            from graphics import graphics  # and your graphics

            self.toolbox = ToolBox(self)
            layout.addWidget(self.toolbox, 1)

            self.graphics = graphics(self)
            layout.addWidget(self.graphics, 3)

            # rewire signals
            self.toolbox.component_changed.connect(self.graphics.update_component)
            self.toolbox.component_selected.connect(self.graphics.handleComponentSelected)
            self.toolbox.component_renamed.connect(self.graphics.handleComponentRenamed)

            # draw new aircraft
            self.graphics.plot_aircraft(self.aircraft)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            print("✅ New toolbox:", id(self.toolbox))
            print("✅ New graphics:", id(self.graphics))

        def load_config(self, *args):
            """Reload configuration + rebuild UI"""
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("*.yml *.yaml")
            if file_dialog.exec():
                config_file = file_dialog.selectedFiles()
                if config_file:
                    from aircraft import Aircraft
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
