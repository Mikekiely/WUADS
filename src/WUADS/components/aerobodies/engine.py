from WUADS.components.component import PhysicalComponent
import numpy as np


class Engine(PhysicalComponent):
    """
    Class containing all parameters and methods related to engine and nacelle component.

    Calculates the weight properties for engine, nacelle, and propulsion subcomponents
    Calculates drag contribution from nacelle
    """

    # Default Values
    aero_body = False
    length = 0          # Nacelle Length (ft)
    diameter = 0        # Nacelle Diameter (ft)
    ln = 4              # inlet to compressor face
    p2 = 30             # max static pressure at compressor face (15-50 psi)
    Wec = 3200          # Weight of
    Q = 1.3             # interference factor
    laminar_percent = .05
    pylon_mounted = True
    thrust_reversal = False
    weight_averages = [1, 0, 0]  # [Raymer, Torenbeek, NASA] - weighted averages used for weight estimation

    _n_engines = 2  # Number of engines
    w_engine = 0    # Weight of each engine
    engine_type = 'turbofan'        # 'Turbofan' or 'Propeller'

    weight_nacelle = 0
    weight_controls = 0
    weight_starter = 0
    weight_fuel_system = 0


    def __init__(self, params):
        """
                Initialize nacelle component and set input parameters.

                params: <dict> list of parameters to edit
                """
        super().__init__(params)
        # Find wetted surface area
        self.s_wet = np.pi * self.diameter * self.length

    def parasite_drag(self, flight_conditions, sref):
        """
        Set nacelle parasite drag using Raymer method.

        :param flight_conditions: flight conditions object at cruise.
        :param float sref: reference area for aircraft.
        """
        l_char = self.length
        f = self.length / self.diameter
        form_factor = 1 + .35/f * self.n_engines     # From Raymer

        super().parasite_drag(form_factor, l_char, flight_conditions, sref)

    def set_weight(self, aircraft, wdg):
        """
        Sets weight of nacelle including all subcomponents

        :param object aircraft: <aircraft object> aircraft which the fuselage belongs to
        :param int wdg: takeoff gross weight (lbs)

        :return: weight of the nacelle
        :rtype: int
        """

        self.weight = 0
        # Set nacelle weight
        self.weight += self.raymer_weight(aircraft, wdg)

        # Add additional turbofan components if required
        if self.engine_type == 'turbofan' or aircraft.aircraft_type == 'transport':
            # Set weight of engines
            self.weight += self.n_engines * self.w_engine
            # Set weight of engine controls
            self.weight += self.controls_weight(aircraft)
            # set weight of starters
            self.weight += self.starter_weight(aircraft)
        # Set weight of fuel systems
        self.weight += self.fuel_system_weight(aircraft)
        self.set_cg()
        return self.weight

    def set_cg(self):
        self.cg = [self.xle + self.length/2, self.yle, self.zle]
        self.inertia = [x * self.weight for x in self.cg]

    def raymer_weight(self, aircraft, wdg):
        """
        Calculates nacelle weight using Raymer method

        :param object aircraft: aircraft object which this nacelle belongs to
        :param int wdg: gross takeoff weight (lbs)

        :return: Raymer weight (lbs)
        :rtype: float
        """

        if self.engine_type == 'turbofan':
            if self.pylon_mounted:
                kng = 1.017
            else:
                kng = 1

            if self.engine_type == 'propeller':
                kp = 1.4
            else:
                kp = 1
            if self.thrust_reversal:
                ktr = 1.18
            else:
                ktr = 1

            wec = 2.331 * self.w_engine ** .901 * kp * ktr
            self.weight_raymer = .6724 * kng * self.length**.1 * self.diameter**.294 * aircraft.ultimate_load**.119 * \
                                  wec ** .611 * self.n_engines**.984 * self.s_wet ** .224
            self.weight_nacelle = self.weight_raymer
        elif self.engine_type == 'propeller':
            self.weight_raymer = self.w_engine ** .922 * self.n_engines
        return self.weight_raymer

    def controls_weight(self, aircraft):
        """
        Sets weight of engine controls

        :param object aircraft: aircraft object which this nacelle belongs to

        :return: weight of the controls (lbs)
        :rtype: int
        """
        if isinstance(self.xle, list):
            xle = sum(self.xle) / len(self.xle)
        else:
            xle = self.xle
        # Raymer method
        lec = aircraft.aero_components['Fuselage'].length - (xle + .5 * self.length)
        self.weight_controls = 5 * self.n_engines + .8 * lec
        return self.weight_controls

    def starter_weight(self, aircraft):
        """
        Calculates weight of engine starters.

        :param object aircraft: aircraft object which this nacelle belongs to

        :return: weight of the engine starters (lbs)
        :rtype: float
        """
        # Raymer method
        w_raymer = 49.19 * (self.n_engines * self.w_engine / 1000) ** .541

        # NASA method
        w_nasa = 11 * self.n_engines * aircraft.cruise_conditions.mach ** .32 * self.diameter

        self.weight_starter = .5 * (w_nasa + w_raymer)
        return self.weight_starter

    def fuel_system_weight(self, aircraft):
        """
        Calculates weight of the fuel system

        :param object aircraft: aircraft object which this nacelle belongs to.

        :return: weight of the fuel system (lbs)
        :rtype: float
        """
        vt = aircraft.mission.w_fuel / aircraft.mission.rho_fuel
        n_tank = aircraft.subsystems.parameters['n_tanks']

        if aircraft.aircraft_type == 'transport':
            # Raymer method
            w_raymer = 1.2025 * vt ** .606 * n_tank ** .5

            # Torenbeek method
            w_torenbeek = 80 * (self.n_engines + n_tank - 1) + 15 * n_tank ** .5 + vt ** .33
            # TODO fix all this to make it accessible to multiple nacelle configurations
            # NASA method
            w_nasa = 1.07 * aircraft.mission.w_fuel ** .58 * n_tank ** .43 * aircraft.cruise_conditions.mach ** .34

            self.weight_fuel_system = (w_nasa + w_raymer + w_torenbeek) / 3

        elif aircraft.aircraft_type == 'general_aviation':
            # Raymer method
            vi = vt  # holding vi/vt = 1 for now (this is the integral tank volume / the total fuel volume
            vi_vt = 1
            w_raymer = 2.49 * vt ** .726 * (1 / (1 + vi_vt)) ** .363 * n_tank ** .242 * self._n_engines ** .157
            # NASA method
            w_nasa = 1.07 * aircraft.mission.w_fuel * .58 * self._n_engines ** .43

            self.weight_fuel_system = (w_nasa + w_raymer)/2

        return self.weight_fuel_system

    @property
    def n_engines(self):
        return (self._n_engines)

    @n_engines.setter
    def n_engines(self, n):
        self._n_engines = n
        n_stations = np.ceil(n / 2).astype(int)

        def le_coords(coord):
            # Make sure coordinate is a list
            if not isinstance(coord, list):
                coord = [coord]
            # If there is only one coordinate, return just that number
            if n_stations == 1:
                return coord[0]
            # Default the recently created engines to 0
            while len(coord) < n_stations:
                coord.append(0)
            return coord

        self.xle = le_coords(self.xle)
        self.yle = le_coords(self.yle)
        if n == 1:
            self.yle = 0
        self.zle = le_coords(self.zle)