import logging
from ..component import PhysicalComponent
import numpy as np


class Wing(PhysicalComponent):
    """
    Class containing all the variables and method used for a wing component.

    Also serves as the superclass for horizontal and vertical stabilizer.
    """

    def __init__(self, params):
        """
        Initializes the wing with given parameters
        :param dict params: <dict> list of parameters to edit
        """

        self.load_default_values()

        super().__init__(params)
        self.create_geometry(params)


    def create_geometry(self, params):
        self._load_variables(params)
        # Check if wing is well-defined
        vars_taper = ['xle', 'yle', 'zle', 'area', 'span', 'sweep', 'dihedral', 'taper']
        vars_chord = ['xle', 'yle', 'zle', 'span', 'cr', 'ct', 'sweep', 'dihedral']
        if all(key in params for key in vars_taper):
            # Wing is defined by taper ratio, define root and tip chord lengths
            cr = 2 * self.area / (self.span * (1 + self.taper))
            self.cr = cr
            ct = cr * self.taper
            self.ct = ct
        elif all(key in params for key in vars_chord):
            # Wing is defined by chord lengths
            ct = self.ct
            cr = self.cr
            area = .5 * (ct + cr) * self.span
            self.area = area
            self.taper = ct / cr
        else:
            logging.warning(" Wing is not well defined")

        # Calculate class variables
        b = self.span / 2
        t = self.taper
        self.cref = cr * (2 / 3) * ((1 + t + t ** 2) / (1 + t))
        self.aspect_ratio = self.span ** 2 / self.area
        xle = self.xle
        yle = self.yle
        zle = self.zle

        self.set_sweep_angle()
        self.dihedral_deg = self.dihedral
        self.dihedral = np.deg2rad(self.dihedral)

        # Create sections used for AVL Analysis
        self.avl_sections = [[xle, yle, zle, self.cr, 0],
                             [(xle + cr / 4) + b * np.tan(self.sweep) - self.ct / 4, b + yle, zle + b * \
                          np.tan(self.dihedral), ct, 0]]

        # Add winglet if exists
        winglet = params.get('winglet', None)
        if winglet is not None:
            section1 = self.avl_sections[1]
            sweep = winglet['sweep']
            height = winglet['height']
            dihedral = winglet['dihedral']
            ct_wl = winglet['ct']
            self.avl_sections.append([section1[0] + np.tan(sweep) * height, section1[1] + height / np.tan(dihedral), section1[2] + height, ct_wl, 0])

        # Set wetted surface area (Torenbeek - advanced aircraft design)
        kq = 0.95
        Qw = kq * self.tc * self.area * np.sqrt(self.area / self.aspect_ratio) / np.sqrt(1 + t)
        self.s_wet = (2 + .5 * self.tc) * (Qw * np.sqrt(self.aspect_ratio * (1 + t)) / (kq * self.tc)) ** (2 / 3)

        # Set airfoils and twist

    def load_default_values(self):
        # Defualt Values
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
        self.Q = 1   # interference factor
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

    def parasite_drag(self, flight_conditions, sref, aircraft):
        """
        Sets Wing parasite drag coefficient using Raymer Method

        :param flight_conditions: <flight_conditions object> flight conditions at cruise
        :param float sref: reference area for aircraft
        """

        tc = self.tc
        xc = self.xc
        mach = flight_conditions.mach
        sweep = self.sweep_quarter_chord
        l_char = self.cref

        # From Raymer
        form_factor = ((1 + tc * .6 / xc + 100 * tc ** 4) * (1.34 * mach ** .18 * (np.cos(sweep)) ** .28))
        # TODO Add shevell method
        super().parasite_drag(form_factor, l_char, flight_conditions, sref)

    def set_wave_drag(self, aircraft):
        """
        Set wave drag for the wing
        Uses methods from Gur and Mason
        https://doi.org/10.2514/1.47557

        :param object aircraft: aircraft object which this wing belongs to.

        :return: Wave drag for the wing
        :rtype: int
        """
        # split wing into strips
        n_strips = 20
        chords = np.linspace(self.cr, self.ct, n_strips+1)
        dy = .5 * self.span / n_strips
        rho = aircraft.cruise_conditions.rho
        v = aircraft.cruise_conditions.velocity
        m = aircraft.cruise_conditions.mach
        if m < .5 or aircraft.sref == 0:
            return 0

        # Eliptical lift distribution equations
        lift = aircraft.weight_takeoff * .99
        gamma_0 = lift / (.25 * np.pi * v * rho * self.span)
        y_dist = np.linspace(self.yle, self.yle + self.span/2, n_strips)

        cdw = 0
        for i in range(n_strips):
            cr_i = chords[i]
            ct_i = chords[i+1]
            c = .5 * (cr_i + ct_i)
            area = .5 * (cr_i + ct_i) * dy

            # Elliptical lift dist
            gamma = gamma_0 * np.sqrt(1 - (2 * (y_dist[i] - self.yle) / self.span) ** 2)
            lprime = rho * v * gamma
            cl = lprime / (.5 * rho * v ** 2 * c)
            # Find the drag divergence number
            ka = .95        # TODO make an input to change the airfoil type
            cos = np.cos(self.sweep_mid)
            mdd = (ka - cl / (10 * cos ** 2) - self.tc / cos) / cos
            mcr = mdd - .1077217

            # Set section wave drag coefficient if applicable
            if m > mcr:
                cdw += 20 * (m - mcr) ** 4 * (area / aircraft.sref)

        self.cdw = cdw
        return cdw

    def raymer_weight(self, aircraft, wdg):
        """
        Calculate wing weight using Raymer's method

        :param aircraft: <aircraft object> aircraft which the wing component belongs to
        :param float wdg: design gross weight of aircraft

        :return: Raymer weight
        :rtype: float
        """
        if aircraft.aircraft_type == 'transport':
            scsw = self.control_surface_ratio * self.area
            self.weight_raymer = .0051 * (
                        wdg * aircraft.ultimate_load) ** .557 * self.area ** .649 * self.aspect_ratio ** .5 \
                                 * self.tc ** -.4 * (1 + self.taper) ** .1 * np.cos(self.sweep_quarter_chord) ** -1 * scsw ** .1
        elif aircraft.aircraft_type == 'general_aviation':
            W_fw = aircraft.w_fuel # weight of fuel in wing
            a = .036 * self.area ** .758 * W_fw ** .0035
            b = (self.aspect_ratio / (np.cos(self.sweep))**2 ) ** .6
            c = aircraft.cruise_conditions.q ** .006 * self.taper ** .04
            d = ((100 * self.tc) / (np.cos(self.sweep)))**-.3
            e =  (aircraft.ultimate_load * wdg) ** .49

            self.weight_raymer = a * b * c * d * e

        return self.weight_raymer

    def torenbeek_weight(self, aircraft, wdg):
        """
        Calculate wing weight using Torenbeek method

        :param object aircraft: <object aircraft>  aircraft which the wing belongs to
        :param int wdg: takeoff gross weight (lbs)

        :return: Torenbeek weight (lbs)
        :rtype: float
        """
        # only works for transport aircraft
        sweep = self.sweep_mid
        wmzf = wdg - aircraft.mission.w_fuel

        a = .0017 * wmzf * (self.span / np.cos(sweep)) ** .75
        b = 1 + (6.3 * np.cos(sweep) / self.span) ** .5
        c = aircraft.ultimate_load ** .55
        d = (self.span * self.area / (self.cr * self.tc * wmzf * np.cos(sweep))) ** .3
        self.weight_torenbeek = a * b * c * d
        return self.weight_torenbeek

    # NASA estimation method doesn't work for this

    def set_cg(self):
        """
        Sets center of gravity and moments of inertia for wing
        """
        a = self.ct
        b = self.cr
        semi_span = self.span * .5
        c = semi_span * np.tan(self.sweep_le)
        dihedral = self.dihedral

        self.cg = [self.xle + (2*a*c + a**2 + c*b + a*b + b**2) / (3*(a+b)),
                   self.yle + (semi_span * (2*a+b) / (3*(a+b))),
                   self.zle + (semi_span * (2*a+b) / (3*(a+b)))*np.tan(dihedral)]

        super().set_cg()

    def update(self, variable, value, **kwargs):
        """
        Updates the wing parameters. Note the whole aircraft will need to be re-evaulated to determine weights and drag

        :param string variable: name of variable to be updated
        :param value: value to update the variable to
        :param boolean maintain_aspect_ratio: if set to true and the area is altered, the span will be altered to maintain the current
                                   aspect ratio
        """
        maintain_aspect_ratio = kwargs.get('maintain_aspect_ratio', True)

        vars_taper = ['xle', 'yle', 'zle', 'area', 'span', 'sweep', 'dihedral', 'taper']
        vars_chord = ['xle', 'yle', 'zle', 'span', 'cr', 'ct', 'sweep', 'dihedral']
        if (variable == 'area' or variable == 'taper') and all(key in self.params for key in vars_chord):
            self.params.pop('cr')
            self.params.pop('ct')
            self.params['area'] = self.area
            self.params['taper'] = self.ct / self.cr
            return

        # Update span to maintain aspect ratio if applicable
        if maintain_aspect_ratio and variable == 'area':
            self.params['span'] = np.sqrt(self.aspect_ratio * value)
        if maintain_aspect_ratio and variable == 'span':
            self.params['area'] = value ** 2 / self.aspect_ratio

        variable = variable.lower().strip()

        self.params[variable] = value
        self.__init__(self.params)

    def set_sweep_angle(self, sweep=None, sweep_location=None):
        """
        Sets the sweep angle of the wing
        :param sweep: sweep angle in degrees
        :param sweep_location: percentage of the chord at which the sweep is defined (0 for leading edge, .25 for quarter chord, etc.)
        :return:
        """
        if not sweep:
            sweep = self.sweep
        if not sweep_location:
            sweep_location = self.sweep_location

        self.sweep_location = sweep_location
        self.sweep_deg = sweep
        self.sweep = np.deg2rad(self.sweep)

        xle = self.xle
        x_root = xle + sweep_location * self.cr
        b = self.span / 2
        x_tip = x_root + b * np.tan(self.sweep)
        xle_tip = x_tip - sweep_location * self.ct
        self.sweep_le = np.arctan((xle_tip - xle) / b)
        self.sweep_quarter_chord = np.arctan(((xle_tip + .25 * self.ct) - (xle + .25 * self.cr)) / b)
        self.sweep_mid = np.arctan(((xle_tip + .5 * self.ct) - (xle + .5 * self.cr)) / b)
        self.sweep_te = np.arctan(((xle_tip + self.ct) - (xle + self.cr)) / b)

