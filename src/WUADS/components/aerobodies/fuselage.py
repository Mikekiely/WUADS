from ..component import PhysicalComponent
import numpy as np


class Fuselage(PhysicalComponent):
    """
    Class containing all methods and variables for fuselage.
    Used for ellipse shaped main fuselages.
    """

    def __init__(self, params):
        """
        Initializes fuselage with given parameters.

        :param <dict> params: list of parameters to edit
        """
        # Default Values
        self.length = 0          # Length Tip to Nose (ft)
        self.width = 0           # Width (ft)
        self.height = 0          # Height (ft)
        self.a_max = 0           # Cross-sectional area at thickest point (ft^2)
        self.diameter = 0        # Average Diameter (Ft)
        self.fineness_ratio = 0  # Form Factor
        self.s_wet = 0


        self.Q = 1.1             # Interference Factor - Landing gear and wing correction
        self.laminar_percent = .05  # Laminar flow percentage
        self.fuse_mounted_lg = True  # Whether the landing gear is mounted

        self.weight_averages = [.5, 0, .5]  # [Raymer, Torenbeek, NASA] - weighted averages used for weight estimation


        super().__init__(params)

        # Calculate class variables
        self.diameter = .5 * (self.width + self.height)
        self.a_max = .25 * np.pi * self.diameter ** 2
        if self.diameter == 0 or self.length == 0:
            return

        self.fineness_ratio = self.length / self.diameter
        f = self.fineness_ratio
        # Torenbeek 1988 wetted area estimation
        self.s_wet = np.pi * self.diameter * self.length * (1 - 2 / f) ** (2 / 3) * (1 + 1 / (f ** 2))

    def parasite_drag(self, flight_conditions, sref):
        """
        Calculates fuselage drag coefficient using method from gotten et. al.
        https://doi.org/10.2514/1.C036032

        :param flight_conditions: flight conditions object at cruise
        :param float sref: aircraft reference area
        """
        if self.diameter == 0 or self.length == 0:
            self.cd0 = 0
            self.cdw = 0
            return 0


        l_char = self.length
        d = self.diameter
        w = self.width
        cs1 = -.825885 * (d / w) ** .411795 + 4.0001
        cs2 = -.340977 * (d / w) ** 7.54327 - 2.27920
        cs3 = -.013846 * (d / w) ** 1.34253 + 1.11029
        form_factor = cs1 * (l_char / d) ** cs2 + cs3

        re = flight_conditions.rho * flight_conditions.velocity * l_char / flight_conditions.mu
        cf = (1 / (3.46 * np.log10(re) - 5.6)) ** 2
        if sref == 0:
            return
        self.cd0 = cf * form_factor * self.Q * self.s_wet / sref

    def set_weight(self, aircraft, wdg):
        if self.length == 0 or self.diameter == 0:
            self.weight = 0
            return 0
        else:
            # if aircraft.aircraft_type == 'general_aviation':
            #     self.weight_averages = [0, 0, 1]
            # super().set_weight(aircraft, wdg)
            self.weight = self.nasa_weight(aircraft, wdg)
            self.set_cg()
            return self.weight

    def raymer_weight(self, aircraft, wdg):
        """
        Calculates fuselage weight using raymer method

        :param object aircraft: <aircraft object> aircraft which the fuselage belongs to
        :param int wdg: takeoff gross weight (lbs)

        :return: Raymer weight (lbs)
        :rtype: float
        """
        if aircraft.aircraft_type == 'transport':
            bw = aircraft.aero_components['Main Wing'].span
            tw = aircraft.aero_components['Main Wing'].taper
            sweepw = aircraft.aero_components['Main Wing'].sweep

            if 'kdoor' in self.params:
                kdoor = self.params['kdoor']
            else:
                kdoor = 1.06

            if self.fuse_mounted_lg:
                klg = 1.12
            else:
                klg = 1.0

            kws = .75 * ((1 + 2 * tw) / (1 + tw)) * (bw * np.tan(sweepw / self.length))
            self.weight_raymer = 0.328 * kdoor * klg * (
                        wdg * aircraft.ultimate_load) ** .5 * self.length ** .25 * \
                                 self.s_wet ** .302 * (1 + kws) ** .04 * (self.fineness_ratio) ** .1

            return self.weight_raymer

        elif aircraft.aircraft_type == 'general_aviation':

            tail_name = None
            for name, comp in aircraft.aero_components.items():
                if comp.component_type == 'horizontal':
                    tail_name = name

            if not tail_name:
                lt = (self.xle + self.length) - (aircraft.aero_components['Main Wing'].xle + .25 * aircraft.aero_components['Main Wing'].cr)
            else:
                lt = (aircraft.aero_components[tail_name].xle + .25 * aircraft.aero_components[tail_name].cr) - \
                     (aircraft.aero_components['Main Wing'].xle + .25 * aircraft.aero_components['Main Wing'].cr)

            Wpress = 0
            a = .052 * self.s_wet ** 1.086
            b = (aircraft.ultimate_load * wdg) **.414 * lt ** -.051
            c = (self.fineness_ratio) ** -.072
            d = aircraft.cruise_conditions.q ** .241
            self.weight_raymer = a * b * c * d + Wpress

            return self.weight_raymer

    def torenbeek_weight(self, aircraft, wdg):
        """
        Calculates fuselage weight using Torenbeek method.

        :param: object aircraft: <aircraft object> aircraft which the fuselage belongs to
        :param: int wdg: takeoff gross weight (lbs)

        :return: Torenbeek weight (lbs)
        :rtype: float
        """

        # Adjust constants from inputs
        kf = 1
        if self.fuse_mounted_lg:
            kf *= 1.07

        if 'pressurized_fuse' in self.params:
            if self.params['pressurized_fuse']:
                kf *= 1.08
        else:
            kf *= 1.08

        if 'cargo_floor' in self.params:
            if self.params['cargo_floor']:
                kf *= 1.1

        # estimates tail ac as the end of the fuselage, should be fairly accurate except for unconventional
        # configurations
        acw = aircraft.aero_components['Main Wing'].xle + .25 * aircraft.aero_components['Main Wing'].cr
        lh = self.length - acw

        # TODO Figure out how to implement divespeed
        dive_speed = aircraft.cruise_conditions.v * .592484
        self.weight_torenbeek = .021 * kf * ((dive_speed * lh) / (self.width + self.height)) ** .5 * self.s_wet ** 1.2
        return self.weight_torenbeek

    def nasa_weight(self, aircraft, wdg):
        """
        Calculates fuselage weight using NASA FLOPS method.

        :param: object aircraft: <aircraft object> aircraft which the fuselage belongs to.
        :param: int wdg: takeoff gross weight (lbs)

        :return: NASA FLOPS weight (lbs)
        :rtype: float
        """
        if aircraft.aircraft_type == 'transport':
            # number of fuselage mounted engines
            n_fuse_en = 0
            for comp in aircraft.aero_components.values():
                if comp.component_type == 'Nacelle' and comp.attachment == self.title:
                    if comp.yle == 0:
                        n_fuse_en += 1
                    else:
                        n_fuse_en += 2

            if 'cargo_floor' in self.params and self.params['cargo_floor']:
                cargf = 1.0
            else:
                cargf = 0

            self.weight_nasa = 1.35 * (self.length * self.height) ** 1.28 * (1 + .05 * n_fuse_en) * \
                               (1 + .38 * cargf) * 1

        elif aircraft.aircraft_type == 'general_aviation':
            a = .052 * self.s_wet ** 1.086
            b =(aircraft.ultimate_load * wdg) ** .177
            c = aircraft.cruise_conditions.q ** .241
            self.weight_nasa =  a * b * c



        return self.weight_nasa

    def set_cg(self):
        """
        Sets center of gravity and moments of inertia for fuselage.
        """
        self.cg = [self.length * .45 + self.xle, 0, 0]
        super().set_cg()

    def update(self, variable, value):
        """
        Allows for modifying a specific fuselage property (such as `width` or `height`)
        and recalculates derived attributes like `diameter` based on the updated value.

        :param str variable: The name of the fuselage property to be updated (e.g., 'width', 'height').
        :param float value: The new value to set for the specified property.
        :param maintain_aspect_ratio: Indicates whether to maintain the aspect ratio between `width` and `height`.
        """
        super().update(variable, value)
        self.diameter = .5 * (self.width + self.height)