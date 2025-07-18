import yaml
import importlib
from src.WUADS.components.Component import component
from src.WUADS.components.Subsystems import subsystems
from src.WUADS.Mission import mission
from src.WUADS.components.Useful_Load import useful_load
from src.WUADS.propulsion import turbofan, turbofan_LH2, propeller
from src.WUADS.mission_profile import *
from src.WUADS.flight_conditions import FlightConditions


class Aircraft:
    """
    Class for whole aircraft analysis

    Contains variables and analyses for entire aircraft configuration with input components

    Parameters
    -   Config File: YAML file containing relevant component information for aircraft, see online tutorials for more information
    """

    # Default Values

    title = ''
    aero_components = {}
    cruise_conditions = {}      # Flight conditions at cruise
    sref = 0                    # Reference Area (ft^2)
    cd0 = 0                     # Parasite Drag coefficient
    cdw = 0                     # Wave drag coefficient

    misc_components = {}        # Miscellaneous Components

    cg = [0, 0, 0]
    cg_empty = [0, 0, 0]
    inertia = [0, 0, 0]
    _n_engines = 2

    _lock_component_weights = False  # Locks component weights so editing the aircraft doesn't change them
    _h_cruise = 0   # Cruise Altitude
    _m_cruise = 0   # Cruise Mach number

    weight_takeoff = 0          # Takeoff Gross Weight (lbs)
    weight_empty = 0            # Empty weight, no fuel, no cargo, no crew
    weight_max = 0              # Max Takeoff weight
    weight_reference = 0        # Reference weight used to calculate component weights, typically the same as weight_max

    _w_cargo = 0                # Cargo weight
    _w_fuel = 0                 # Fuel Weight
    _n_z = 0                    # Ultimate load

    subsystems = []
    useful_load = None
    mission = None
    stability = None
    propulsion = None
    aircraft_type = 'transport'

    def __init__(self, config_file, mission_profile=None
                 , wdg_guess=100000):
        """
        Initialize aircraft from config file
        Sets weight and parasite drag

        Parameters:
            config_file: aircraft input file in yaml format, see tutorials for further explanation
        """

        self.input_file = config_file
        self.load_config()
        self.set_weight(wdg_guess=wdg_guess)
        self.set_cd0()

    def load_config(self):
        """
        Reads input YAML file and initializes aircraft and declared components
        """
        with open(self.input_file) as f:
            config = yaml.safe_load(f)

            # Set all aircraft variables
            for variable_name, variable_value in config.get("aircraft", {}).items():
                if hasattr(self, variable_name.lower()):
                    setattr(self, variable_name.lower(), variable_value)
                elif hasattr(self.mission, variable_name.lower()):
                    setattr(self.mission, variable_name.lower(), variable_value)

                if variable_name.lower() == 'mach':
                    self._m_cruise = variable_value
                elif variable_name.lower() == 'altitude':
                    self._h_cruise = variable_value
                elif variable_name.lower() == 'ultimate_load':
                    self._n_z = variable_value

            # Set useful load weights
            self.useful_load = useful_load(config.get("aircraft", {}))

            # Initialize defined aerodynamic components with given parameters
            for component_type, params in config.get("components", {}).items():
                class_name = f"{component_type.capitalize()}"
                # try:
                # Retrieve the class of the declared component and initialize
                # TODO error exception on this (finish all component classes first)
                module_name = f"WUADS.components.aerobodies.{component_type.lower()}"
                module = importlib.import_module(module_name)

                component_class = getattr(module, class_name)
                component = component_class(params)
                component.title = component.title.title()
                self.aero_components[component.title] = component_class(params)
                # except Exception as e:
                #     print(e)
                #     print(f"Warning: Class for '{class_name}' not found, component ignored")

            # Set subsystem parameters for weight estimation
            subsystem_parameters = {}
            for parameter, value in config.get("subsystem_parameters", {}).items():
                subsystem_parameters[parameter] = value
            self.subsystems = subsystems(subsystem_parameters)

            # general conditions set-up
            self.cruise_conditions = FlightConditions(self.h_cruise, self.mach_cruise)
            self.sref = self.aero_components['Main Wing'].area
            self.mission = mission(config.get('aircraft'), aircraft=self)  # change this? mission(mission_profile)

            if not 'Main Wing' in self.aero_components:
                raise AttributeError('Main Wing component not declared')

            # Propulsion parameters
            propulsion_parameters = config.get("propulsion", {})

            engine_type = self.aero_components['Nacelle'].engine_type

            # try:
            if engine_type in ['turbofan', 'turbofan_LH2']:
                if 'thrust_sea_level' in propulsion_parameters:
                    thrust_sea_level = propulsion_parameters['thrust_sea_level']
                else:
                    thrust_sea_level = None

                if 'thrust_cruise' in propulsion_parameters:
                    thrust_cruise = propulsion_parameters['thrust_cruise']
                else:
                    thrust_cruise = None

                if 'sfc_sea_level' in propulsion_parameters:
                    sfc_sea_level = propulsion_parameters['sfc_sea_level']
                else:
                    sfc_sea_level = None

                if 'sfc_cruise' in propulsion_parameters:
                    sfc_cruise = propulsion_parameters['sfc_cruise']
                else:
                    sfc_cruise = None

                self.propulsion = self.generate_propulsion(
                    n_engines=self.n_engines,
                    thrust_cruise=thrust_cruise,
                    thrust_sea_level=thrust_sea_level,
                    sfc_sea_level=sfc_sea_level,
                    sfc_cruise=sfc_cruise,
                    engine_type=engine_type
                )

            elif engine_type == 'propeller':
                if 'horse_power' in propulsion_parameters:
                    horse_power = propulsion_parameters['horse_power']



                else:
                    horse_power = None

                if 'fuel_consumption_rate' in propulsion_parameters:
                    fuel_consumption_rate = propulsion_parameters['fuel_consumption_rate']
                else:
                    fuel_consumption_rate = None

                self.propulsion = self.generate_propulsion(
                    n_engines=self.n_engines,
                    horse_power=horse_power,
                    fuel_consumption_rate=fuel_consumption_rate,
                    engine_type=engine_type
                )
