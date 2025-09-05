import logging
import numpy as np

logger = logging.getLogger(__name__)

class Component:
    """
    Super Class for all components

    Contains all relevant component information such as weight, parasite drag, etc.

    All methods may be overriden by specific component classes
    """

    params = {}  # Input parameters, used to edit the component later
    title = ""  # Name of component
    component_type = ""  # Component class type

    weight = 0.0  # Overall weight

    cg = [0, 0, 0]  # Center of gravity (x, y, z)
    inertia = [0, 0, 0]  # Moments of inertia (ix, iy, iz)
    aero_body = False

    def __init__(self, params):
        """
        Initializes component and sets all input parameters

        Parameters:
        :param <dict> params: list of parameters to edit.
        """

        self.params = params
        self.component_type = self.__class__.__name__
        for variable_name, variable_value in params.items():
            if hasattr(self, variable_name.lower()):
                setattr(self, variable_name.lower(), variable_value)

    def update(self, variable, value, **kwargs):
        """
        Updates specified parameters in component.
        Note the whole aircraft will need to be re-evaluated to determine weights and drag.

        Parameters:
        :param <str> variable: name of variable to be updated
        :param float value: value to update the variable to

        Returns:
        :return weight: Overall weight.
        :rtype: int
        """
        if hasattr(self, variable):
            setattr(self, variable, value)
        else:
            logging.warning(f'Variable {variable} not found found in list of variables for component {self.__class__}')
        if hasattr(self.params, variable):
            setattr(self.params, variable, value)

    def set_weight(self, aircraft, wdg):
        self.weight = 0
        return self.weight

    def set_cg(self, cg=None):
        """
        Sets center of gravity and moments of inertia for component.

        :param float cg: center of gravity.
        """
        self.cg = cg
        if self.cg:
            self.inertia = [self.weight * x for x in cg]

    def cross_sectional_area(self, aircraft, x):
        pass


class PhysicalComponent(Component):
    """
    Component which effects aerodynamic performance of the aircraft
    """
    # Default Values
    avl_sections = []  # Sections to input into AVL
    attachment = ""  # What component is this attached to, eg. nacelle attached to wing
    cd0 = 0.0  # Parasite drag coefficient
    cdw = 0.0  # Wave drag coefficient
    xle = 0.0  # Leading edge x coordinate
    yle = 0.0  # Leading edge y coordinate
    zle = 0.0  # Leading edge z coordinate

    laminar_percent = 0.1  # Percentage experiencing laminar flow
    Q = 1.0  # Interference factor (for parasite drag)
    s_wet = 0  # Wetted Surface area

    weight_raymer = 0.0  # Weight using Raymer estimation method
    weight_torenbeek = 0.0  # Weight using Torenbeek method
    weight_nasa = 0  # Weight using NASA FLOPS Method
    weight_averages = [1 / 3, 1 / 3, 1 / 3]  # [Raymer, Torenbeek, NASA] - weighted averages used for weight estimation

    def __init__(self, params):
        """
        Initializes the physical_component with the given parameters.

        :param <dict> params: list of parameters to edit
        """
        super().__init__(params)

    def parasite_drag(self, form_factor, l_char, flight_conditions, sref):
        """
        Computes the Parasitic Drag Coefficient using Raymer's method.

        :param float form_factor: Adjusts for component shape effects on drag.
        :param float l_char: Characteristic length of the component.
        :param object flight_conditions: Contains rho (air density), v (velocity), mu (Air dynamic viscosity), and mac (mach number)
        :param float sref: Reference area
        """
        # Parasite drag calculation - From Raymer
        # L is the characteristic length
        rho = flight_conditions.rho
        v = flight_conditions.velocity
        mu = flight_conditions.mu
        mach = flight_conditions.mach
        Re = rho * v * l_char / mu
        cflam = 1.328 / np.sqrt(Re)
        cfturb = .455 / (np.log10(Re) ** 2.58 * (1 + .144 * mach ** 2) ** .65)
        cf = self.laminar_percent * cflam + (1 - self.laminar_percent) * cfturb
        # cf = .0055
        if sref == 0:
            return 0
        else:
            self.cd0 = cf * form_factor * self.Q * self.s_wet / sref

    def set_wave_drag(self, aircraft):
        """
        Sets the wave drag to zero.

        :param object aircraft: Aircraft for which the wave drag is set.

        :return: Zero
        :rtype: int
        """
        self.cdw = 0
        return 0

    def set_weight(self, aircraft, wdg):
        """
        Sets the weight of the component to the weighted averages of the Raymer, Torenbeek and Nasa weight calculations.
        :param object aircraft: Aircraft to which the component belongs to.
        :param int wdg: takeoff Gross Weight.
        :return: Weight of the component.
        :rtype: int
        """
        # exclude torenbeek method for general_aviation aircrafts
        if aircraft.aircraft_type == 'general_aviation':
            self.weight_averages = [.5, 0, .5]

        self.weight = self.raymer_weight(aircraft, wdg) * self.weight_averages[0] + \
                      self.torenbeek_weight(aircraft, wdg) * self.weight_averages[1] + \
                      self.nasa_weight(aircraft, wdg) * self.weight_averages[2]
        self.set_cg()

        return self.weight

    def raymer_weight(self, aircraft, wdg):
        """
        Sets the Raymer weight of the component to zero.

        :param object aircraft: Aircraft to which the component belongs
        :param int wdg: Takeoff gross weight.

        :return: 0
        :rtype: int
        """
        return 0

    def torenbeek_weight(self, aircraft, wdg):
        """"
        Sets the Torenbeek weight of the component to zero.

        :param object aircraft: Aircraft to which the component belongs
        :param int wdg: Takeoff gross weight.

        :return: 0
        :rtype: int
        """
        return 0

    def nasa_weight(self, aircraft, wdg):
        """
        Sets the NASA weight of the component to zero.

        :param object aircraft: Aircraft to which the component belongs
        :param int wdg: Takeoff gross weight.

        :return: 0
        :rtype: int
        """
        return 0

    def set_cg(self):
        """
        Updates the center of gravity of the component.

        """
        super().set_cg(self.cg)