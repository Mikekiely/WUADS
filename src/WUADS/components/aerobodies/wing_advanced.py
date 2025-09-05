from .wing import Wing
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Wing_advanced(Wing):


    def __init__(self, params):
        # Default Values
        self.title = ''
        self.sweep = 0  # c/4 sweep (rad)
        self.sweep_location = .25  # location of the sweep definition (as a percentage of the chord)
        self.sweep_deg = 0  # c/4 sweep (Deg)
        self.sweep_le = 0  # Leading edge sweep (rad)
        self.sweep_mid = 0  # c/2 sweep (rad)
        self.sweep_te = 0  # Trailing edge sweep (rad)
        self.sweep_quarter_chord = None
        self.area = 0  # Planform surface area (ft^2)
        self.aero_body = True
        self.span = 0  # Wingspan (ft)
        self.cref = 0  # Mean Aerodynamic Chord (ft)
        self.airfoil = ''
        self.aspect_ratio = 0  # Aspect Ratio
        self.taper = 0  # Taper Ratio
        self.cr = 0  # Root Chord
        self.ct = 0  # Tip Chord
        self.Q = 1  # interference factor
        self.laminar_percent = .1  # Percentage of laminar flow
        self.dihedral = 0  # Dihedral angle (rad)
        self.dihedral_deg = 0  # Dihedral angle (deg)
        self.tc = .12  # Airfoil Thickness (At Root)
        self.hc = .008  # Camber
        self.weight_averages = [.8, .2, 0]  # [Raymer, Torenbeek, NASA]
        # self.weight_averages = [.15, .85, 0]
        self.control_surface_ratio = .1
        self.cd0 = 0
        self.laminar_percent = .05
        self.winglet = {}
        self.xc = .35  # x value at mean camber line
        self.avl_sections = []
        self.xle = 0
        self.yle = 0
        self.zle = 0
        super()._load_variables(params)

        self.params = {}
        self.definition_type = "Sections"
        self.avl_sections = []
        self.twist = []
        self.airfoil = []
        self.component_type = 'Wing_Advanced'
        self.sections = []
        self.params = params
        self.component_type = self.__class__.__name__
        for variable_name, variable_value in params.items():
            if hasattr(self, variable_name.lower()):
                setattr(self, variable_name.lower(), variable_value)
        self.create_sections()

    def create_sections(self):
        # Create Sections
        self.sections = []
        first_section = True

        i = 1
        for section_params in self.params['sections']:
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
            section.title = f'section__{i}'
            i += 1
            self.sections.append(section)

        # set variables
        self.span = 0
        self.area = 0
        self.cref = 0
        self.s_wet = 0
        for sec in self.sections:
            self.span += sec.span
            self.area += sec.area
            self.cref += sec.cref * sec.area
            self.s_wet += sec.s_wet
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



        if 'airfoils' in self.params:
            self.airfoil = []
            self.twist = []
            for af in self.params['airfoils'].values():
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

        self.avl_sections = [[self.xle, self.yle, self.zle, self.cr, self.twist[0]]]
        i = 1
        for sec in self.sections[1:]:
            self.avl_sections.append([sec.xle, sec.yle, sec.zle, sec.cr, self.twist[i]])
            i += 1
        self.avl_sections.append([self.sections[-1].xle_tip, self.sections[-1].yle_tip, self.sections[-1].zle_tip, self.ct, self.twist[-1]])

    def set_variables(self):
        # Set variables
        for variable_name, variable_value in self.params.items():
            if hasattr(self, variable_name.lower()) and variable_name.lower() != 'sections':
                setattr(self, variable_name.lower(), variable_value)

    def update(self, variable, value, **kwargs):
        section = kwargs.get('section', None)

        if variable in self.params:
            self.params[variable] = value
        else:
            value = float(value)
            if variable == 'span':
                variable = 'length'
                value = value / 2

            if section is not None:
                sec = self.params['sections'][int(section)]
                if variable in sec.keys():
                    sec[variable] = value
            else:
                self.params[variable] = value

        self.__init__(self.params)





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
            if 'length' in self.input_params:
                self.input_params['span'] = self.input_params['length'] * 2
                self.length = self.input_params['length']
            else:
                self.length = self.input_params['span'] / 2
            super().__init__(self.input_params)

        self.xle_tip = self.xle + self.length * np.tan(self.sweep_le)
        self.yle_tip = self.yle + self.length
        self.zle_tip = self.zle + self.length * np.tan(self.dihedral)