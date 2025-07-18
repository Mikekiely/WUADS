from WUADS.components.aerobodies.wing import Wing
import numpy as np


class Vertical(Wing):
    """
    Class containing all methods and parameters related to Vertical stabilizers.

    Subclass of wing, has all the same variables.
    """
    weight_averages = [.2, .4, .4] # [Raymer, Torenbeek, NASA] - weighted averages used for weight estimation
    def __init__(self, params):
        """
        Initialize vertical stabilizer with input parameters.

        params: <dict> list of parameters to edit
        """
        super().__init__(params)

        # Set sections for AVL and other class parameters
        self.sections = [[self.xle, self.yle, self.zle, self.cr, 0],
                         [(self.xle + self.cr / 4) + self.span * np.tan(self.sweep) - self.ct / 4, self.yle, self.zle + self.span, self.ct, 0]]
        xle_tip = self.xle + self.span * np.tan(self.sweep) - .25 * self.ct
        self.sweep_le = np.arctan((xle_tip - self.xle) / self.span)
        self.Q = 1.1

    def raymer_weight(self, aircraft, wdg):
        """
        Set vertical stabilizer weight using Raymer method.

        :param object aircraft: aircraft object which this nacelle belongs to
        :param int wdg: gross takeoff weight

        :return: Raymer weight (lbs)
        :rtype: float
        """
        # Set method parameters
        ht = 0
        for comp in aircraft.aero_components.values():
            if comp.component_type == 'Horizontal':
                if comp.zle > (aircraft.aero_components['Fuselage'].height / 2):
                    ht = 1
        if aircraft.aircraft_type == 'transport':
            lt = (self.xle + .25 * self.cr) - \
                 (aircraft.aero_components['Main Wing'].xle + .25 * aircraft.aero_components['Main Wing'].cr)

            self.weight_raymer = .0026 * (
                        1 + ht) ** .225 * wdg ** .556 * aircraft.ultimate_load ** .536 * lt ** -.5 * \
                                 self.area ** .5 * lt ** .875 * np.cos(self.sweep) ** -1 * self.aspect_ratio ** .35 \
                                 * self.tc ** -.5
            return self.weight_raymer
        elif aircraft.aircraft_type == 'general_aviation':
            a = .073 * (1 + .2 * ht) * (aircraft.ultimate_load * wdg) ** .376
            b = aircraft.cruise_conditions.q ** .122 * self.area ** .873
            c = ((100 * self.tc) / np.cos(self.sweep)) ** -.49
            d = (self.aspect_ratio / (np.cos(self.sweep) ** 2)) ** .357
            e = self.taper ** .039

            self.weight_raymer = a * b * c * d * e
            return self.weight_raymer



    def torenbeek_weight(self, aircraft, wdg):
        """
        Set vertical stabilizer weight using Torenbeek Method.

        :param object aircraft: <object aircraft>  aircraft which the horizontal stabilizer belongs to
        :param int wdg: takeoff gross weight (lbs)

        :return: Torenbeek weight (lbs)
        :rtype: float
        """
        # check if horizontal is mounted on vertical
        horiz = False
        for comp in aircraft.aero_components.values():
            if comp.component_type == 'Horizontal':
                if comp.zle > (aircraft.aero_components['Fuselage'].height / 2):
                    horiz = True
                    horiz_comp = comp
                break

        if horiz:
            kv = 1 + .15 * ((horiz_comp.area * horiz_comp.zle) / (self.area * self.span))
        else:
            kv = 1

        dive_speed = aircraft.cruise_conditions.v * .592484
        a = kv * self.area * 3.81
        b = (self.area ** .2 * dive_speed) / (1000 * np.cos(self.sweep_mid) ** .5)
        self.weight_torenbeek = a * b ** -.281
        return self.weight_torenbeek

    def nasa_weight(self, aircraft, wdg):
        """
        Set vertical stablilizer weight using NASA FLOPS method.

        :param: object aircraft: <aircraft object> aircraft which the horizontal stabilizer belongs to
        :param: int wdg: takeoff gross weight (lbs)

        :return: NASA FLOPS weight (lbs)
        :rtype: float
        """
        ht = 0
        for comp in aircraft.aero_components.values():
            if comp.component_type == 'Horizontal':
                if comp.zle > (aircraft.aero_components['Fuselage'].height / 2):
                    ht = 1
        if aircraft.aircraft_type == 'transport':
            if self.yle == 0 and self.dihedral_deg == 90:
                n_vert = 1
            else:
                n_vert = 2
            self.weight_nasa = .32 * wdg ** .3 * (self.taper + .5) * n_vert ** .7 * self.area ** .85
            return self.weight_nasa
        elif aircraft.aircraft_type == 'general_aviation':
            Csweep = np.cos(self.sweep)
            a = .073 * (1 + .2 * ht) * (aircraft.ultimate_load * wdg) ** .376
            b = aircraft.cruise_conditions.q ** .122 * self.area ** .873
            c = (self.aspect_ratio / (Csweep ** 2)) ** .357
            d = ((100 * self.tc)/ Csweep) ** .49
            self.weight_nasa = a * b * (c / d)
            return self.weight_nasa

    def set_cg(self):
        """
        Sets center of gravity and moments of inertia for vertical stabilizer
        """
        a = self.ct
        b = self.cr
        semi_span = self.span * .5
        c = semi_span * np.tan(self.sweep_le)
        dihedral = self.dihedral

        self.cg = [self.xle + (2 * a * c + a ** 2 + c * b + a * b + b ** 2) / (3 * (a + b)),
                   self.yle,
                   self.zle + (semi_span * (2 * a + b) / (3 * (a + b)))]

        self.inertia = [x * self.weight for x in self.cg]

    def set_wave_drag(self, aircraft):
        """
        Set the wave drag of the vertical stabilizer to zero.

        :param object aircraft: <aircraft object> aircraft which the horizontal stabilizer belongs to
        :return: 0
        :rytpe: int
        """
        self.cdw = 0
        return 0