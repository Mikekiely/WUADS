from PySide6.QtCore import Signal, Slot, Qt

from PySide6.QtWidgets import (
    QToolBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
    QMenu,
    QMessageBox,
    QPushButton, QInputDialog, QDialog
)
from WUADS.gui.toolbox.aircraft_info import aircraft_info
from WUADS.gui.toolbox.component_edit import component_edit
from WUADS.gui.toolbox.mission_profile_edit import mission_profile_edit
from WUADS.gui.toolbox.propulsion_input import propulsion_input
from WUADS.gui.toolbox.subcomponent_edit import subcomponent_edit
from WUADS.gui.toolbox.useful_load_edit import useful_load_edit
from WUADS.gui.toolbox.analysis_list import analysis_list

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

useful_load_types = {'Passengers': 'passengers',
                      'Flight Attendants': 'flight_attendants',
                      'Pilots': 'pilots',
                      'Cargo': 'cargo',
                     'Fuel': 'fuel'}

mission_profile_types = {'Takeoff': 'takeoff',
                      'Climb': 'climb',
                      'Cruise': 'cruise',
                      'Descent': 'descent',
                        'Loiter': 'loiter',
                         'Weight Drop': "weight_drop",
                     'Landing': 'landing'}


class ToolBox(QToolBox):
    """
    Toolbox on the left side of the screen that controls all data input
    """

    component_changed = Signal(str)
    component_selected = Signal(str)
    component_removed = Signal(str)
    component_renamed = Signal(str, str)
    selected_component = ''

    # initiate all toolbox features
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.aircraft = parent.aircraft
        # Aircraft information
        label = QLabel()
        aircraft_input = aircraft_info(self)
        self.addItem(aircraft_input, "Aircraft Information")

        # Component list - double click to bring up popup to edit component
        self.component_list = QListWidget()
        for comp in parent.aircraft.aero_components.values():
            self.component_list.addItem(comp.title)
        self.addItem(self.component_list, "Components")
        self.component_list.itemDoubleClicked.connect(self.handleComponentDoubleClicked)
        self.component_list.itemClicked.connect(self.handleComponentClicked)

        # Useful Load List
        useful_load_container = QWidget()
        layout = QVBoxLayout()
        useful_load_container.setLayout(layout)
        self.useful_load_list = QListWidget()
        for item in useful_load_types.keys():
            self.useful_load_list.addItem(item)
        self.useful_load_list.itemDoubleClicked.connect(self.handleUsefulLoadClicked)
        layout.addWidget(self.useful_load_list)

        self.useful_load_reset = QPushButton('Set Useful Load to Default Values')
        self.useful_load_reset.clicked.connect(self.reset_useful_load)
        layout.addWidget(self.useful_load_reset)

        self.addItem(useful_load_container, "Useful Load")

        self.setup_mission_profile_section()

        # Subcomponent list
        self.subcomponent_container = QWidget(self)
        layout = QVBoxLayout()
        self.subcomponent_container.setLayout(layout)
        self.subcomponent_list = QListWidget()
        for comp in subcomponent_types.keys():
            item = QListWidgetItem(comp)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.subcomponent_list.addItem(item)
        self.subcomponent_list.itemChanged.connect(self.handleSubcomponentChecked)
        layout.addWidget(self.subcomponent_list)
        self.subsystem_reset = QPushButton('Set Subsystem Parameters to Default Values')
        self.subsystem_reset.clicked.connect(self.reset_subsystems)
        layout.addWidget(self.subsystem_reset)


        self.addItem(self.subcomponent_container, 'Subsystems')
        self.subcomponent_list.itemDoubleClicked.connect(self.handleSubcomponentSelected)


        self.propulsion = propulsion_input(self)
        self.propulsion.n_engines_changed.connect(self.handle_n_engines_changed)
        self.addItem(self.propulsion, 'Propulsion')

        self.analyses = analysis_list(self)
        self.addItem(self.analyses, "Analysis")

    # Tab 5: Mission Profile Section (new)
    def setup_mission_profile_section(self):
        mission_profile_container = QWidget()
        layout = QVBoxLayout()
        mission_profile_container.setLayout(layout)

        # List for mission profile
        self.mission_profile_list = QListWidget()
        for seg in self.aircraft.mission.mission_profile:
            self.mission_profile_list.addItem(seg.title)
        self.mission_profile_list.itemDoubleClicked.connect(self.handleMissionProfileClicked)
        layout.addWidget(self.mission_profile_list)

        # Reset button TODO: change this for mission profile stuff
        self.mission_profile_reset = QPushButton('Set Mission Profile to Default Values')
        self.mission_profile_reset.clicked.connect(self.reset_mission_profile)
        layout.addWidget(self.mission_profile_reset)

        self.addItem(mission_profile_container, "Mission Profile")

    # Creates a dialog box to input component characteristics
    def handleComponentDoubleClicked(self, item):

        pop = component_edit(item.text(), self)
        pop.component_changed.connect(self.component_changed)
        pop.title_changed.connect(self.handle_title_changed)
        pop.exec()

    def handleMissionProfileClicked(self, item):
        """Opens a pop-up dialog to edit the selected mission profile segment."""
        phase = item.text()
        popup = mission_profile_edit(self, phase)
        if popup.exec() == QDialog.Accepted:
            self.refresh_mission_profile_list()

    def refresh_mission_profile_list(self):
        self.mission_profile_list.clear()
        for seg in self.aircraft.mission.mission_profile:
            self.mission_profile_list.addItem(seg.title)

    def handleUsefulLoadClicked(self, item):
        popup = useful_load_edit(self, useful_load_types[item.text()])
        popup.exec()

    # Sends Signal to highlight selected Component
    @Slot(str)
    def handleComponentClicked(self, item):
        selected_component = item.text()
        # selected_component = self.component_list.selectedItems()[0].text()
        if selected_component == self.selected_component:
            self.component_list.clearSelection()
            selected_component = ''
        self.component_selected.emit(selected_component)
        self.selected_component = selected_component

    # Opens subcomponent dialogue
    def handleSubcomponentSelected(self, item):
        popup = subcomponent_edit(item.text(), self)
        popup.exec()

    # TODO Add functionality to this
    def handleSubcomponentChecked(self, item):
        if item.checkState() == Qt.Checked:
            title = subcomponent_types[item]


    # Sends Signal to change the title and update the component list
    @Slot(str, str)
    def handle_title_changed(self, old_title, new_title):
        if old_title:
            self.component_renamed.emit(old_title, new_title)
            # Find index in list to remove
            for index in range(self.component_list.count()):
                if self.component_list.item(index).text().lower() == old_title.lower():
                    self.component_list.item(index).setText(new_title)

    def contextMenuEvent(self, event):
        index = self.currentIndex()
        # Component List
        if index == 1:
            # Add component and Remove Component Options
            context_menu = QMenu(self)
            add_component = context_menu.addMenu("Add Component")
            add_component.addAction('Wing')
            add_component.addAction('Fuselage')
            add_component.addAction('Horizontal Stabilizer')
            add_component.addAction('Vertical Stabilizer')
            add_component.addAction('Nacelle')
            add_component.triggered.connect(self.handleAddComponent)

            remove_component = context_menu.addMenu("Remove Component")
            for comp in self.parent.aircraft.aero_components.keys():
                item = remove_component.addAction(comp)
                if comp.lower() == 'main wing' or comp.lower() == 'fuselage':
                    item.setEnabled(False)
            remove_component.triggered.connect(self.handleRemoveComponent)

            context_menu.exec(event.globalPos())

            # added
        elif index == 3:
            context_menu = QMenu(self)
            # add_segment = context_menu.addAction("Add Mission Profile Segment")
            # remove_segment = context_menu.addAction("Remove Selected Segment")
            #
            # add_segment.triggered.connect(self.handleAddMissionProfileSegment)
            # remove_segment.triggered.connect(self.handleRemoveMissionProfileSegment)
            #
            # context_menu.exec(event.globalPos())
            add_segment = context_menu.addMenu("Add Mission Profile Segment")
            for seg in mission_profile_types.keys():
                add_segment.addAction(seg)
            add_segment.triggered.connect(self.handleAddMissionProfileSegment)
            remove_segment = context_menu.addMenu("Remove Selected Segment")
            for seg in self.aircraft.mission.mission_profile:
                remove_segment.addAction(seg.title)
            remove_segment.triggered.connect(self.handleRemoveMissionProfileSegment)
            context_menu.exec(event.globalPos())

    def handleAddComponent(self, item):
        component = item.text().lower()
        if component == 'horizontal stabilizer':
            component = 'horizontal'
        if component == 'vertical stabilizer':
            component = 'vertical'
        pop = component_edit(component, self, new_component=True)
        pop.component_changed.connect(self.component_changed)
        pop.title_changed.connect(self.handle_title_changed)
        pop.exec()

    def handleRemoveComponent(self, item):
        component = item.text()

        def confirm_delete():
            msg = QMessageBox()
            msg.setWindowTitle('Confirm Delete')
            msg.setIcon(QMessageBox.Question)
            msg.setText(f'Are you sure you want to delete the component {component}')
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            result = msg.exec()
            return result == QMessageBox.Yes

        if confirm_delete():
            self.parent.aircraft.remove_component(component)
            self.component_changed.emit(component)

            # Find index in list to remove
            for index in range(self.component_list.count()):
                if self.component_list.item(index).text().lower() == component.lower():
                    self.component_list.takeItem(index)
                    return

    def handle_n_engines_changed(self, n_engines):
        pop = component_edit('Nacelle', self)
        pop.component_changed.connect(self.component_changed)
        pop.title_changed.connect(self.handle_title_changed)
        pop.exec()

    def handleAddMissionProfileSegment(self, item):
        segment_type = item.text().lower()

        popup = mission_profile_edit(self, segment_type.capitalize())
        if popup.exec() == QDialog.Accepted:
            self.refresh_mission_profile_list()


    def handleRemoveMissionProfileSegment(self):
        selected_item = self.mission_profile_list.currentItem()
        if selected_item:
            segment_name = selected_item.text()
            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete the mission profile segment '{segment_name}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                mission_profile_types.pop(segment_name, None)
                self.mission_profile_list.takeItem(self.mission_profile_list.row(selected_item))

    def reset_mission_profile(self):  # CHANGED
        confirm = QMessageBox()
        confirm.setWindowTitle('Confirm Mission Profile Reset')
        confirm.setIcon(QMessageBox.Question)
        confirm.setText('Are you sure you want to reset the mission profile to default values?')
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        confirmed = confirm.exec()

        if confirmed == QMessageBox.Yes:
            self.mission_profile_list.clear()
            for item in mission_profile_types.keys():
                self.mission_profile_list.addItem(item)

    def reset_subsystems(self):
        fuse = self.parent.aircraft.aero_components['Fuselage']

        confirm = QMessageBox()
        confirm.setWindowTitle('Confirm Subsystem Reset')
        confirm.setIcon(QMessageBox.Question)
        confirm.setText(f'Are you sure you want to reset the subsystems to default values')
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        confirmed = confirm.exec()

        if not confirmed:
            return

        for comp in self.parent.aircraft.subsystems.components.values():
            comp.cg = cg_default(comp.title, fuse)

        self.parent.aircraft.set_weight(self.parent.aircraft.weight_takeoff)

    def reset_useful_load(self):
        length = self.parent.aircraft.aero_components['Fuselage'].length

        confirm = QMessageBox()
        confirm.setWindowTitle('Confirm Subsystem Reset')
        confirm.setIcon(QMessageBox.Question)
        confirm.setText(f'Are you sure you want to reset the subsystems to default values')
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        confirmed = confirm.exec()

        if not confirmed:
            return

        useful_load = self.parent.aircraft.useful_load
        useful_load.cg_fuel = [65 * length / 123.3, 0 , 0]
        useful_load.cg_cargo = [54 * length / 123.3, 0, 0]
        useful_load.cg_passengers = [58 * length / 123.3, 0, 0]
        useful_load.cg_flight_attendants = [9 * length /123.3, 0, 0]
        useful_load.pilots = [9 * length /123.3, 0, 0]
        self.parent.aircraft.set_weight(self.parent.aircraft.weight_takeoff)

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