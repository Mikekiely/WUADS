import importlib
import sys
# from ruamel.yaml import YAML
import yaml

from .components.component import Component
from .components.subsystems import Subsystems
from .mission import Mission
from .components.usefulload import UsefulLoad
from .propulsion import turbofan, propeller
from .mission_segments import *
from .flight_conditions import FlightConditions
from .components.aerobodies.wing import Wing
from .components.aerobodies.fuselage import Fuselage
from .components.aerobodies.horizontal import Horizontal
from .components.aerobodies.vertical import Vertical
from .components.aerobodies.engine import Engine

AEROBODY_CLASSES = {
    "wing": Wing,
    "fuselage": Fuselage,
    "horizontal": Horizontal,
    "vertical": Vertical,
    "engine": Engine
}

import logging

# Set up basic config: terminal output only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

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
    cruise_conditions = {}  # Flight conditions at cruise
    sref = 0  # Reference Area (ft^2)
    cd0 = 0  # Parasite Drag coefficient
    cdw = 0  # Wave drag coefficient

    misc_components = {}  # Miscellaneous Components

    cg = [0, 0, 0]
    cg_empty = [0, 0, 0]
    inertia = [0, 0, 0]
    _n_engines = 2

    _lock_component_weights = False  # Locks component weights so editing the aircraft doesn't change them
    _h_cruise = 0  # Cruise Altitude
    _m_cruise = 0  # Cruise Mach number

    weight_takeoff = 0  # Takeoff Gross Weight (lbs)
    weight_empty = 0  # Empty weight, no fuel, no cargo, no crew
    weight_max = 0  # Max Takeoff weight
    weight_reference = 0  # Reference weight used to calculate component weights, typically the same as weight_max

    _w_cargo = 0  # Cargo weight
    _w_fuel = 0  # Fuel Weight
    _n_z = 0  # Ultimate load

    subsystems = []
    useful_load = None
    mission = None
    stability = None
    propulsion = None
    aircraft_type = 'transport'

    _output_dir = None
    _file_prefix = None

    def __init__(self, config_file, wdg_guess=100000):
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
        self.file_prefix = self.title
        if not self._output_dir:
            self.output_dir = os.path.join(os.getcwd(), f'./output/{self.file_prefix}')


    def load_config(self):
        """
        Reads input YAML file and initializes aircraft and declared components
        """

        self.mission = Mission(self)
        with open(self.input_file) as f:
            # yml = YAML(typ='safe', pure=True)
            # config = yml.load(f)
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
            self.useful_load = UsefulLoad(config.get("aircraft", {}))

            # Initialize defined aerodynamic components with given parameters
            for component_type, params in config.get("components", {}).items():
                component_class = AEROBODY_CLASSES.get(component_type.lower())
                if 'title' not in params:
                    params['title'] = component_type
                try:
                    self.aero_components[params['title']] = component_class(params)
                except TypeError:
                    logger.warning(f'Component type {component_type} not found, the valid component types are as follows: {AEROBODY_CLASSES.keys()}')

            # Set subsystem parameters for weight estimation
            subsystem_parameters = {}
            for parameter, value in config.get("subsystem_parameters", {}).items():
                subsystem_parameters[parameter] = value
            self.subsystems = Subsystems(subsystem_parameters)

            # general conditions set-up
            self.cruise_conditions = FlightConditions(self.h_cruise, self.mach_cruise)
            self.sref = self.aero_components['Main Wing'].area

            if not 'Main Wing' in self.aero_components:
                raise AttributeError('Main Wing component not declared')

            # Propulsion parameterse

            # try:
            propulsion_parameters = config.get("propulsion", {})

            self.cruise_conditions = FlightConditions(self.h_cruise, self.mach_cruise)
            self.sref = self.aero_components['Main Wing'].area
            self.propulsion = self.generate_propulsion(n_engines=self.n_engines,
                                                       **propulsion_parameters)

            mission_profile_params = config.get("mission_profile", None)
            self.mission.generate_mission_profile(mission_profile_params)

    def generate_propulsion(self, n_engines=None, set_engine=True, **kwargs):
        """
        Sets aircraft propulsion to a turbofan engine with specified values
        :param int n_engines:  Number of engines
        :param float thrust_sea_level:  Maximum available thrust at sea level
        :param float sfc_sea_level:  Specific fuel consumption at sea level
        :param float thrust_cruise:  Maximum available thrust at cruise
        :param sfc_cruise:  Specific fuel consumption at cruise
        """
        if not 'engine_type' in kwargs:
            logger.warn('Engine Type is not declared in propulsion parameters, defaulting to turbofan')
            engine_type = 'turbofan'
        else:
            engine_type = kwargs['engine_type']

        if n_engines:
            self.n_engines = n_engines

        if engine_type.lower() == 'turbofan':
            thrust_sea_level = kwargs.get('thrust_sea_level', None)
            thrust_cruise = kwargs.get('thrust_cruise', None)
            sfc_sea_level = kwargs.get('sfc_sea_level', None)
            sfc_cruise = kwargs.get('sfc_cruise', None)

            engine = turbofan(h_cruise=self.h_cruise,
                              mach_cruise=self.mach_cruise,
                              n_engines=self.n_engines,
                              thrust_sea_level=thrust_sea_level,
                              thrust_cruise=thrust_cruise,
                              sfc_sea_level=sfc_sea_level,
                              sfc_cruise=sfc_cruise)
        elif engine_type.lower() == 'propeller':
            horse_power = kwargs.get('horse_power', None)
            fuel_consumption_rate = kwargs.get('fuel_consumption_rate', None)
            if not horse_power:
                logger.warning('Please enter a base horsepower for propeller engine')
            if not fuel_consumption_rate:
                logger.warning('Please enter a fuel consumption rate for propeller engine')
            engine = propeller(
                n_engines=n_engines,
                horse_power=horse_power,
                fuel_consumption_rate=fuel_consumption_rate
            )


        if set_engine:
            self.propulsion = engine

        return engine

    def set_cd0(self):
        """
        Calculates each components parasite drag coefficient and sets the overall aircraft drag coefficient
        """
        # https://arc.aiaa.org/doi/abs/10.2514/1.47557

        cd0, cdw = self.get_cd0()
        self.cd0 = cd0
        self.cdw = cdw

    def get_cd0(self, height=None, mach=None):
        # https://arc.aiaa.org/doi/abs/10.2514/1.47557

        if height == None:
            height = self.h_cruise
        if mach == None:
            mach = self.mach_cruise

        cd0 = 0
        cdw = 0
        fc = FlightConditions(height, mach)
        for comp in self.aero_components.values():
            comp.parasite_drag(fc, self.sref)
            cd0 += comp.cd0
            cdw += comp.set_wave_drag(self)
        return cd0, cdw

    def set_weight(self, wdg_guess=None, fudge_factor=1.06):
        """
        Uses and iterative loop to set all component weights and overall weight

        Parameters: wdg_guess: Initial guess for gross design weight (lbs)
        fudge_factor: <float> Margin to multiply overall weight by. Good practice to leave at ~1.06 to account
                              for various un modelled weights
        """
        if not wdg_guess:
            wdg_guess = self.weight_takeoff
        self.weight_takeoff = 1
        margin = .00001
        # Start iterative loop
        max_iter = 100

        if self.lock_component_weights:
            wdg_guess = self.weight_max

        for i in range(max_iter):
            # Set structural component weights
            self.weight_takeoff = 0
            for comp in self.aero_components.values():
                self.weight_takeoff += comp.set_weight(self, wdg_guess)
                comp.set_cg()

            for comp in self.misc_components.values():
                self.weight_takeoff += comp.weight

            # Set subsystem Weights
            self.weight_takeoff += self.subsystems.set_subsystem_weights(self, wdg_guess)

            # Add fudge factor
            self.weight_takeoff *= fudge_factor

            # The current weight is the empty weight
            self.weight_empty = self.weight_takeoff
            # Add useful load
            self.useful_load.set_weight(self)
            self.weight_takeoff += self.useful_load.weight
            self.weight_empty += self.useful_load.w_pilots * 1.65 + self.useful_load.w_flight_attendants * 1.65

            # Check if converged
            if np.abs((wdg_guess - self.weight_takeoff) / self.weight_takeoff) < margin or self.lock_component_weights:
                break

            # adjust wdg guess
            wdg_guess = wdg_guess + (self.weight_takeoff - wdg_guess) * .75

        # Set moments of inertia and cg
        self.inertia = [0, 0, 0]
        for comp in self.aero_components.values():
            self.inertia = [i + ix for i, ix in zip(self.inertia, comp.inertia)]
        for comp in self.misc_components.values():
            self.inertia = [i + ix for i, ix in zip(self.inertia, comp.inertia)]

        if not self.lock_component_weights:
            self.weight_max = self.weight_takeoff

        self.inertia = [i + ix for i, ix in zip(self.inertia, self.subsystems.inertia)]
        # Set cg
        self.cg_empty = [i / (self.weight_empty / fudge_factor) for i in self.inertia]

        self.inertia = [i + ix for i, ix in zip(self.inertia, self.useful_load.inertia)]
        self.cg = [i / (self.weight_empty / fudge_factor + self.useful_load.weight) for i in self.inertia]

    def update_component(self, variables, maintain_aspect_ratio=False):
        """
        Updates component and recalculates weight and parasite drag

        Parameters:
            variables: List of variables to update, formatted as tuples with the following format (component, variable, value)
                      example:
                      [('Main Wing', 'Sweep', 25),
                       ('Horizontal', 'Area', 430),
                       ('Fuselage', 'Length', 120)]
            maintain_aspect_ratio: if set to true and the area is altered, the span will be altered to maintain the current
                                   aspect ratio
        """
        # cast variables to list if its just a single tuple
        if not isinstance(variables, list):
            variables = [variables]
        # Set variables
        for var in variables:
            title = var[0]
            variable = var[1]
            value = var[2]
            # Check if title is in aero components
            if title in self.aero_components:
                self.aero_components[title].update(variable, value, maintain_aspect_ratio=maintain_aspect_ratio)

        # Re-initialize the weights and drag
        self.sref = self.aero_components['Main Wing'].area
        self.set_weight()
        self.set_cd0()

    def add_component(self, component_type, params):
        """
        Adds component with a given set of parameters

        component_type: str
        params: dict
        """
        class_name = f"{component_type.capitalize()}"
        module_name = f"WUADS.components.aerobodies.{component_type.lower()}"  # TODO Make this so it can add a non physical component
        module = importlib.import_module(module_name)
        component_class = getattr(module, class_name)
        component = component_class(params)
        self.aero_components[component.title] = component_class(params)
        self.set_weight()
        self.set_cd0()

    def remove_component(self, component):
        """Removes a component and updates parameters"""
        # for key in self.aero_components.keys():
        #     if key.lower() == component.lower():
        #         component = key

        del self.aero_components[component]
        self.set_weight()
        self.set_cd0()

    def write_config_file(self, file_name=None):
        """ Write a .yaml file to save the aircraft's variables """

        if not file_name:
            file_name = os.path.join(self.output_dir, "aircraft.yaml")

        component_list = {}
        for comp in self.aero_components.values():
            params = {}
            for param in comp.params.keys():
                if hasattr(comp, param):
                    val = getattr(comp, param)
                    try:
                        val = float(val)
                    except:
                        pass

                    if param.startswith('sweep') or param.startswith('dihedral'):
                        val *= 180 / np.pi

                    params[param] = val

            component_list[comp.component_type] = params

        subcomp_list = {}
        for comp in self.subsystems.components.values():
            subcomp_list[comp.title] = [float(x) for x in comp.cg]

        subsystem_params = {'subsystems': subcomp_list,
                            'n_nose_wheels': self.subsystems.parameters['n_nose_wheels'],
                            'n_main_wheels': self.subsystems.parameters['n_main_wheels'],
                            'n_tanks': self.subsystems.parameters['n_tanks'],
                            'w_avionics': self.subsystems.parameters['w_avionics']
                            }

        propulsion_params = {'thrust_sea_level': self.propulsion.thrust_sea_level,
                             'thrust_cruise': self.propulsion.thrust_cruise,
                             'sfc_sea_level': self.propulsion.sfc_sea_level,
                             'sfc_cruise': self.propulsion.sfc_cruise}

        mission_profile_params = {}
        for seg in self.mission.mission_profile:
            seg_params = {}
            for item in seg.input_params:
                seg_params[item] = getattr(seg, item)
            mission_profile_params[seg.title] = seg_params

        data = {
            'aircraft': {
                'title': self.title,
                'altitude': self.h_cruise,
                'mach': self.mach_cruise,
                'max_mach': self.mission.max_mach,
                'ultimate_load': self.ultimate_load,
                'w_fuel': self.mission.w_fuel,
                'cg_fuel': self.useful_load.cg_fuel,
                'rho_fuel': self.mission.rho_fuel,
                'n_passengers': self.mission.n_passengers,
                'cg_passengers': self.useful_load.cg_passengers,
                'n_pilots': self.mission.n_pilots,
                'n_flight_attendants': self.mission.n_flight_attendants,
                'cg_crew': self.useful_load.cg_flight_attendants,
                'w_cargo': self.w_cargo,
                'cg_cargo': self.useful_load.cg_cargo,
                'design_range': self.mission.design_range,
                'n_engines': self.n_engines
            },
            'components': component_list,
            'subsystem_parameters': subsystem_params,
            'propulsion': propulsion_params,
            'mission_profile': mission_profile_params

        }

        if not file_name:
            file_name = self.input_file

        with open(file_name, 'w') as file:
            # yaml = YAML(typ='unsafe', pure=True)
            # yaml.default_flow_style = False
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)

    def add_misc_weight(self, title, weight, cg=None):
        """
        Adds a miscellaneous point weight to the aircraft, held in aircraft.misc_components

        :param title: <str> Title of the new component
        :param weight: <float> Weight of the component (lbs)
        :param cg: <[float, float, float]> Component center of gravity, [x, y, z]. Defaults to the cg of the plane if not entered
        """

        if not cg:
            cg = self.cg
        self.misc_components[title] = Component({'title': title, 'weight': weight, 'cg': cg})
        self.set_weight()

    @property
    def w_cargo(self):
        return self._w_cargo

    @w_cargo.setter
    def w_cargo(self, weight):
        """
        Updates the cargo weight of the aircraft to test out performance at different loading conditions
        :param cargo_weight: new cargo weight (lbs)
        """
        self._w_cargo = weight
        if self.weight_max > 0:
            self.useful_load.w_cargo = weight
            self.set_weight()

    @property
    def w_fuel(self):
        return self._w_fuel

    @w_fuel.setter
    def w_fuel(self, weight):
        self._w_fuel = weight
        if self.weight_max > 0:
            self.mission.w_fuel = weight
            self.useful_load.w_fuel = weight
            self.set_weight()

    @property
    def n_engines(self):
        return self._n_engines

    @n_engines.setter
    def n_engines(self, n):
        for comp in self.aero_components.values():
            if comp.component_type == 'Nacelle':
                comp.n_engines = n
        try:
            self.propulsion.n_engines = n
        except AttributeError:
            pass
        self._n_engines = n
        if self.weight_max > 0:
            self.set_weight()

    @property
    def lock_component_weights(self):
        return self._lock_component_weights

    @lock_component_weights.setter
    def lock_component_weights(self, x):
        if x:
            self.weight_max = self.weight_takeoff
        self._lock_component_weights = x

    @property
    def h_cruise(self):
        return self._h_cruise

    @h_cruise.setter
    def h_cruise(self, x):
        self._h_cruise = x
        self.mission.altitude = x
        self.cruise_conditions = FlightConditions(x, self.mach_cruise)
        self.set_cd0()

    @property
    def mach_cruise(self):
        return self._m_cruise

    @mach_cruise.setter
    def mach_cruise(self, x):
        self._m_cruise = x
        self.mission.mach = x
        self.cruise_conditions = FlightConditions(self.h_cruise, x)
        self.set_cd0()

    @property
    def ultimate_load(self):
        return self._n_z

    @ultimate_load.setter
    def ultimate_load(self, nz):
        self._n_z = nz
        if hasattr(self.mission, 'ultimate_load'):
            self.mission.ultimate_load = nz

    @property
    def output_dir(self):
        return self._output_dir

    @output_dir.setter
    def output_dir(self, directory: str):
        # Convert to absolute path (handles both absolute and relative)
        output_dire = os.path.abspath(directory.strip())

        # Create directory if it doesn't exist
        if not os.path.isdir(output_dire):
            try:
                os.makedirs(output_dire)
            except Exception as e:
                raise ValueError(f"Could not create directory: {e}")
        self._output_dir = output_dire

    @property
    def file_prefix(self):
        return self._file_prefix

    @file_prefix.setter
    def file_prefix(self, prefix):
        # check if there's invalid characters in the file prefix
        invalid_chars = r'<>:"/\\|?*'
        if any(char in prefix for char in invalid_chars):
            logger.error('file name contains invalid characters')
            sys.exit(1)
            return False

        # Reserved Windows filenames
        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))
        }
        name_upper = os.path.splitext(prefix)[0].upper()
        if name_upper in reserved_names:
            logger.error('file name is invalid')
            sys.exit(1)
            return False

        # Don't allow path separators
        if os.sep in prefix or (os.altsep and os.altsep in prefix):
            logger.error('file name is invalid, please do not use "/"')
            sys.exit(1)
            return False
        self._file_prefix = prefix
