from WUADS.components.aerobodies.wing import Wing
import warnings
import numpy as np

class Wing_advanced(Wing):
    input_params = {}
    definition_type = "Sections"
    _avl_sections = []
    twist = []
    airfoil = []
    component_type = 'wing_advanced'
    sections = []

    def __init__(self, params):
        self.input_params = params
        self.create_sections()

    def create_sections(self):
        # Create Sections
        first_section = True

        for section_name, section_params in self.input_params['sections'].items():
            if first_section:
                section_params["xle"] = self.xle
                section_params["yle"] = self.yle
                section_params["zle"] = self.zle
                first_section = False
            else:
                section_params["xle"] = self.sections[-1].xle_tip
                section_params["yle"] = self.sections[-1].yle_tip
                section_params["zle"] = self.sections[-1].zle_tip
                section_params["cr"] = self.sections[-1].ct

            section = wing_section(section_params)
            section.title = section_name
            self.sections.append(section)

        # set variables
        self.span = 0
        self.area = 0
        self.cref = 0
        for sec in self.sections:
            self.span += sec.span * 2
            self.area += sec.area * 2
            self.cref += sec.cref * sec.area * 2
        self.cref *= 1 / self.area
        self.taper = self.sections[-1].ct / self.sections[0].cr
        self.aspect_ratio = self.span**2 / self.area
        self.cr = self.sections[0].cr
        self.ct = self.sections[-1].ct
        self.xle = self.sections[0].xle
        self.yle = self.sections[0].yle
        self.zle = self.sections[0].zle
        self.dihedral = np.arctan((self.sections[-1].zle_tip - self.zle) / (self.span*.5))
        self.sweep_location = 0

        self.sweep = np.arctan((self.sections[-1].xle_tip - self.sections[0].xle)/ (self.span/2))
        self.sweep = np.rad2deg(self.sweep)
        self.set_sweep_angle(self.sweep, self.sweep_location)


        if 'airfoils' in self.input_params:
            self.airfoil = []
            self.twist = []
            for af in self.input_params['airfoils'].values():
                self.twist.append(af['twist'])
                self.airfoil.append(af['airfoil'])

        # Define avl sections
        if not self.twist:
            self.twist = [0] * (len(self.sections) + 1)
        if not self.airfoil:
            self.airfoil = [None] * (len(self.sections) + 1)

        while len(self.airfoil) < len(self.sections):
            self.airfoil.append(self.airfoil[-1])
        while len(self.twist) < len(self.sections):
            self.twist.append(self.twist[-1])

        self._avl_sections = [[self.xle, self.yle, self.zle, self.cr, self.twist[0]]]
        i = 1
        for sec in self.sections[1:]:
            self._avl_sections.append([sec.xle, sec.yle, sec.zle, sec.cr, self.twist[i]])
            i += 1
        self._avl_sections.append([self.sections[-1].xle_tip, self.sections[-1].yle_tip, self.sections[-1].zle_tip, self.ct, self.twist[-1]])


    def set_variables(self):
        # Set variables
        for variable_name, variable_value in self.input_params.items():
            if hasattr(self, variable_name.lower()) and variable_name.lower() != 'sections':
                setattr(self, variable_name.lower(), variable_value)

class wing_section(Wing):
    input_params = {}

    cr = 0
    ct = 0
    span = 0
    sweep = 0
    sweep_le = 0
    sweep_te = 0
    sweep_location = .25
    dihedral = 0

    xle = 0
    yle = 0
    zle = 0
    xle_tip = 0
    yle_tip = 0
    zle_tip = 0

    area = 0
    taper = 0

    def __init__(self, params):
        self.input_params = params
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param.lower(), value)
        self.define_geometry()

    def define_geometry(self):
        params_1 = ['sweep_le', 'sweep_te', 'cr', 'span']   # Defined by leading edge and trailing edge sweep angles
        params_2 = ['cr', 'ct', 'span', 'sweep']            # Defined by root and tip chord

        if all (key in self.input_params for key in params_1):
            # section is defined by leading edge and trailing edge sweep angles
            dy = self.span
            dx_le = self.span * np.sin(np.radians(self.sweep_le))
            dx_te = self.span * np.sin(np.radians(self.sweep_te))
            self.ct = self.cr - dx_le + dx_te
            self.taper = self.ct / self.cr
            self.xle_tip = self.xle + dx_le
            self.area = .5 * self.span * (self.ct + self.cr)
        else:
            # self.input_params['span'] *= 2
            super().__init__(self.input_params)

        self.xle_tip = self.xle + self.span * np.tan(self.sweep_le)
        self.yle_tip = self.yle + self.span
        self.zle_tip = self.zle + self.span * np.tan(self.dihedral)