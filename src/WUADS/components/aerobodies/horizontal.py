from src.WUADS.components.aerobodies.wing import Wing
import numpy as np


class Horizontal(Wing):
    """
    Class containing all methods and parameters related to Horizontal stabilizers.
    Subclass of wing, has all the same variables.
    """
    weight_averages = [.2, .4, .4]  # [Raymer, Torenbeek, NASA] - weighted averages used for weight estimation
    def __init__(self, params):
        """
        Initializes horizontal stabilizer component

        params: <dict> list of parameters to edit
        """
        super().__init__(params)
        self.Q = 1.1

    def raymer_weight(self, aircraft, wdg):
        """
        Set horizontal stabilizer weight using Raymer method.

        :param object aircraft: <aircraft object> aircraft which the horizontal stabilizer belongs to
        :param int wdg: gross takeoff weight

        :return: Raymer weight (lbs)
        :rtype: float
        """
        if aircraft.aircraft_type == 'transport':
            if self.control_surface_ratio == 1.0:
                kuht = 1.143
            else:
                kuht = 1.0

            lt = (self.xle + .25 * self.cr) - \
                 (aircraft.aero_components['Main Wing'].xle + .25 * aircraft.aero_components['Main Wing'].cr)

            a = .0379 * kuht * (1 + .5 * aircraft.aero_components['Fuselage'].width / self.span) ** -.25
            b = wdg ** .639 * aircraft.ultimate_load ** .1 * self.area ** .75 * lt ** -1
            c = (.3 * lt) ** .704 * np.cos(self.sweep) ** -1 * self.aspect_ratio ** .166
            d = (1 + self.control_surface_ratio) ** .1

            self.weight_raymer = a * b * c * d
            return self.weight_raymer

        elif aircraft.aircraft_type == 'general_aviation':
            a = .016 * (aircraft.ultimate_load * wdg) ** .414
            b = aircraft.cruise_conditions.q ** .168 * self.area ** .896
            c = ((100 * self.tc) / np.cos(self.sweep)) ** -.12
            d = (self.aspect_ratio / (np.cos(self.sweep) ** 2)) ** .043
            e = self.taper ** -.02
            self.weight_raymer = a * b * c * d * e
            return self.weight_raymer



    def torenbeek_weight(self, aircraft, wdg):
        """
        Set horizontal stabilizer weight using Torenbeek Method.

        :param object aircraft: <object aircraft>  aircraft which the horizontal stabilizer belongs to
        :param int wdg: takeoff gross weight (lbs)

        :return: Torenbeek weight (lbs)
        :rtype: float
        """
        if aircraft.aircraft_type == 'transport':
            kh = 1.1

            dive_speed = aircraft.cruise_conditions.v * .592484
            a = 1.1 * self.area * kh
            b = 3.81
            c = self.area ** .2 * dive_speed
            d = 1000
            e = np.cos(self.sweep_mid) ** .5
            f = d * e

            self.weight_torenbeek = a * (b * (c / f) - .287)
        # elif aircraft.aircraft_type == 'general_aviation':
        #     a = aircraft.aero_components['Vertical Stabilizer'].area + self.area
        #     self.weight_torenbeek = .04 * (aircraft.ultimate_load * a ** 2) ** .75
        return self.weight_torenbeek

    def nasa_weight(self, aircraft, wdg):
        """
        Calculates horizontal stablilizer weight using NASA FLOPS method.

        :param: object aircraft: <aircraft object> aircraft which the horizontal stabilizer belongs to
        :param: int wdg: takeoff gross weight (lbs)

        :return: NASA FLOPS weight (lbs)
        :rtype: float
        """
        q = aircraft.cruise_conditions.q # 1481.35 * aircraft.mission.mach * aircraft.flight_conditions.delta # cruise dynamic pressure

        if aircraft.aircraft_type == 'transport':
            self.weight_nasa = .53 * self.area * wdg ** .2 * (self.taper + .5)
            return self.weight_nasa
        elif aircraft.aircraft_type == 'general_aviation':
             # cruise dynamic pressure
            self.weight_nasa = .016 * self.area ** .873 * (aircraft.ultimate_load * wdg) ** .414 * q ** .122
            return self.weight_nasa

    def set_wave_drag(self, aircraft):
        """
        Set the wave drag to zero.

        :param object aircraft: <aircraft object> aircraft which the horizontal stabilizer belongs to.
        :return: 0
        :rtype: int
        """
        self.cdw = 0
        return 0