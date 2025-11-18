import logging

from .component import Component
from .aerobodies.wing import Wing
import numpy as np
logger = logging.getLogger(__name__)

# Contains component classes for all various subsystems
class Subsystems:


    def __init__(self, params):
        """
        Initializes all declared subsystems and sets parameters

        :param <dict> params: list of parameters to edit
        """
        """
            Contains weight properties for all supported subsystems
            """
        self.weight = 0
        self.cg = 0
        self.inertia = [0, 0, 0]

        self.parameters = {}
        self.components = {}
        self.parameters = params
        for name, cg in params['subsystems'].items():
            self.components[name] = Component({'title': name, 'cg': cg})

        # TODO take this out
        if not 'w_avionics' in self.parameters:
            self.parameters['w_avionics'] = 1200

    def set_subsystem_weights(self, aircraft, wdg):
        """
        Calculates weight, cg, and moments of inertia for all subsystems

        :param object aircraft: the aircraft which the weight, cg, and inertia calculations are done.

        :return weight of subsystems
        :rtype float
        """
        self.weight = 0
        self.inertia = [0, 0, 0]
        # Generate all components
        for name, comp in self.components.items():
            name = name.lower()

            if hasattr(self, name) and callable((getattr(self, name))):
                fun = getattr(self, name)
                self.weight += fun(aircraft, wdg, comp)
            else:
                logging.warning(f'Subsystem {name} does not exist')

            # Set inertia value, add to overall inertia
            comp.inertia = [comp.weight * x for x in comp.cg]
            self.inertia = [i1 + i2 for i1, i2 in zip(self.inertia, comp.inertia)]
        self.cg = [i / self.weight for i in self.inertia]
        return self.weight

    def nose_landing_gear(self, aircraft, wdg, comp):
        """
        Calculates weight of nose landing gear

        :param object aircraft: aircraft which the nose landing gear belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for nose landing gear.

        :return component weight
        :rtype float

        """
        params = self.parameters

        if 'w_nose_landing_gear' in params:
            comp.weight = params['w_nose_landing_gear']
        else:
            if aircraft.aircraft_type == 'transport':
                params = self.parameters
                # Raymer method (transport)
                if 'knp' in params:
                    knp = params['knp']
                else:
                    knp = 1
                w_raymer = .032 * knp * wdg ** .646 * aircraft.ultimate_load ** .2 * comp.cg[0] ** .5 * \
                           params['n_nose_wheels']

                # Torenbeek method (transport)
                if aircraft.aero_components['Main Wing'].zle > 0:
                    kgr = 1.08
                else:
                    kgr = 1.0
                ag = 25
                bg = 0
                cg = .0024
                dg = 0
                w_torenbeek = kgr * (ag + bg * wdg ** .75 + cg * wdg + dg * wdg ** 1.5)

                comp.weight = .5 * (w_raymer + w_torenbeek)

            elif aircraft.aircraft_type == 'general_aviation':
                # Raymer
                w_raymer = .125 * (aircraft.ultimate_load * wdg) ** .566 * (comp.cg[0] / 12) ** .845
                # Torenbeek
                # if aircraft.aero_components['Main Wing'].zle > 0:
                #     kgr = 1.08
                # else:
                #     kgr = 1.0
                # ag = 25
                # bg = 0
                # cg = .0024
                # dg = 0
                # w_torenbeek = kgr * (ag + bg * wdg ** .75 + cg * wdg + dg * wdg ** 1.5)
                comp.weight = w_raymer  #* .2 + w_torenbeek * .8

        comp.inertia = [comp.weight * x for x in comp.cg]

        self.components[comp.title] = comp
        return comp.weight

    def main_landing_gear(self, aircraft, wdg, comp):
        """
        Sets main landing gear weight

        :param object aircraft: aircraft which the main landing gear belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for main landing gear.

        :return component weight
        :rtype float
        """
        params = self.parameters

        if 'w_main_landing_gear' in params:
            comp.weight = params['w_main_landing_gear']
        else:
            if aircraft.aircraft_type == 'transport':
                # Torenbeek method
                if aircraft.aero_components['Main Wing'].zle > 0:
                    kgr = 1.08
                else:
                    kgr = 1.0
                ag = 20
                bg = .1
                cg = .019
                dg = 0
                w_torenbeek = kgr * (ag + bg * wdg ** .75 + cg * wdg + dg * wdg ** 1.5)
                comp.weight = w_torenbeek

            elif aircraft.aircraft_type == 'general_aviation':
                ultimate_load_landing = aircraft.ultimate_load
                w_mlg = wdg  # landing weight
                length_mlg = comp.cg[0] # landing gear length (fix?)
                # raymer method
                w_raymer = .095 * (ultimate_load_landing * w_mlg) ** .768 * (length_mlg / 12) ** .409
                # NASA method
                w_nasa = .0117 * w_mlg ** .95 * length_mlg

               # torenbeek (need to make sure constants are correct)
                #if aircraft.aero_components['Main Wing'].zle > 0:
                #     kgr = 1.08
                # else:
                #     kgr = 1.0
                # ag = 20
                # bg = .1
                # cg = .019
                # dg = 0
                # w_torenbeek = kgr * (ag + bg * wdg ** .75 + cg * wdg + dg * wdg ** 1.5)
                # print(w_torenbeek)
                #comp.weight = (w_raymer* .2 + w_nasa * .2 + w_torenbeek * .6)
                #comp.weight =( w_raymer + w_nasa ) / 2
                comp.weight = w_raymer

        comp.inertia = [comp.weight * x for x in comp.cg]

        return comp.weight

    def air_conditioning(self, aircraft, wdg, comp):
        """
        Calculates weight of air conditioning
        """
        # Uses nasa flops method (same for general and transport)

        if 'w_air_conditioning' in self.parameters:
            comp.weight = self.parameters['w_air_conditioning']
        else:

            if 'Fuselage' in aircraft.aero_components.keys():
                l = aircraft.aero_components['Fuselage'].length
                w = aircraft.aero_components['Fuselage'].width
                h = aircraft.aero_components['Fuselage'].height

                w_nasa = 3.2 * (l * w * h) ** .6 + (9 * aircraft.mission.n_passengers ** .83) * aircraft.mission.max_mach + \
                         .075 * self.parameters['w_avionics']
                comp.weight = w_nasa

            if aircraft.aircraft_type == 'general_aviation':
                 #Raymer method (experimental)
                 w_raymer = .7 * (.265 * wdg ** .52 * aircraft.mission.n_passengers ** .68 * self.parameters['w_avionics'] ** .17 * aircraft.mission.max_mach ** .08)

                 comp.weight = .5 * (w_raymer + w_nasa)

        comp.inertia = [comp.weight * x for x in comp.cg]

        return comp.weight

    def anti_ice(self, aircraft, wdg, comp):
        """
        Calculate weight of anti ice components

        :param object aircraft: aircraft which the anti-ice gear belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for anit-ice gear.

        :return component weight
        :rtype float
        """
        if 'w_anti_ice' in self.parameters:
            comp.weight = self.parameters['w_anti_ice']
        else:
            # Raymer method
            w_raymer = .002 * wdg

            # find nacelle group
            for compon in aircraft.aero_components.values():
                if compon.component_type == 'Nacelle':
                    nacelle = compon

            try:
                d = nacelle.diameter * 3 / 5
            except:
                return 0

            # Nasa flops method
            b = aircraft.aero_components['Main Wing'].span
            sweep = aircraft.aero_components['Main Wing'].sweep
            l = aircraft.aero_components['Fuselage'].length
            w_nasa = b / np.cos(sweep) + (3.8 * d * aircraft.n_engines * 3) + 1.5 * l

            comp.weight = .5 * (w_nasa + w_raymer)
        return comp.weight

    def apu(self, aircraft, wdg, comp):
        """
        Calculate auxiliary power unit weight using torenbeek and nasa methods.

        :param object aircraft: aircraft  which the apu belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the apu.

        :return component weight
        :rtype float
        """
        if 'w_apu' in self.parameters:
            comp.weight = self.parameters['w_apu']
        else:

            if aircraft.aircraft_type == 'transport':
                # Torenbeek method
                w_torenbeek = .009 * wdg

                # nasa flops method
                d = aircraft.aero_components['Fuselage'].diameter
                l = aircraft.aero_components['Fuselage'].length
                w_nasa = 54 * (d * l) ** .3 + 5.4 * aircraft.mission.n_passengers ** .9

                comp.weight = .5 * (w_nasa + w_torenbeek)
            else:
                comp.weight = 0
                return 0

        return comp.weight


    def avionics(self, aircraft, wdg, comp):
        """
        Set avionics weight using raymer, torenbeek, and nasa methods

        :param object aircraft: aircraft which the avionics belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the avionics.

        :return component weight
        :rtype float
        """

        if 'w_avionics' in self.parameters:
            comp.weight = self.parameters['w_avionics']
        else:
            if aircraft.aircraft_type == 'transport':
                # Raymer method
                w_raymer = 1.73 * self.parameters['w_avionics'] ** .983

                # Torenbeek method
                w_torenbeek = .575 * (wdg - aircraft.mission.w_fuel) ** .556 * aircraft.mission.design_range ** .25

                # nasa method
                d = aircraft.aero_components['Fuselage'].diameter
                l = aircraft.aero_components['Fuselage'].length
                w_nasa = 15.8 * aircraft.mission.design_range ** .1 * aircraft.mission.n_pilots ** .7 * (l * d) ** .43

                comp.weight = (w_nasa + w_torenbeek + w_raymer) / 3


            elif aircraft.aircraft_type == 'general_aviation':
                # Raymer method
                w_raymer = 2.117 * self.parameters['w_avionics'] ** .933

                # # nasa method (same as transport)
                # d = aircraft.aero_components['Fuselage'].diameter
                # l = aircraft.aero_components['Fuselage'].length
                # w_nasa = 15.8 * aircraft.mission.design_range ** .1 * aircraft.mission.n_pilots ** .7 * (l * d) ** .43
                #comp.weight = (w_raymer + w_nasa) / 2
                comp.weight = w_raymer


        return comp.weight

    def electronics(self, aircraft, wdg, comp):
        """
        Calculates weight of all electronics on aircraft

        :param object aircraft: aircraft which the electronic belong to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the electronics.

        :return component weight
        :rtype float
        """

        if 'w_electronics' in self.parameters:
            comp.weight = self.parameters['w_electronics']
        else:
            # Only uses nasa method (same for both general aviation and transport aircrafts)
            if aircraft.aircraft_type == 'transport':
                d = aircraft.aero_components['Fuselage'].diameter
                l = aircraft.aero_components['Fuselage'].length
                nflcr = aircraft.mission.n_pilots + aircraft.mission.n_flight_attendants
                npass = aircraft.mission.n_passengers
                w_nasa = 92 * l ** .4 * d ** .14 * aircraft.n_engines ** .69 * (1 + .044 * nflcr + .0015 * npass)
                comp.weight = w_nasa

            elif aircraft.aircraft_type == 'general_aviation':
                # raymer
                w_avionics = self.parameters['w_avionics']
                w_fs = aircraft.aero_components['Nacelle'].weight_fuel_system
                comp.weight = 12.57 * (w_fs + w_avionics)**.51
        return comp.weight

    def flight_controls(self, aircraft, wdg, comp):
        """
        Calculates weight of flight controls.

        :param object aircraft: aircraft which the flight controls belong to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the flight controls.

        :return component weight
        :rtype float
        """
        if 'w_flight_controls' in self.parameters:
            comp.weight = self.parameters['w_flight_controls']
        else:
            scs = 0 # Control surface area
            scs_i = 0   # used to find center of gravity
            for compon in aircraft.aero_components.values():
                if hasattr(compon, 'area') and hasattr(compon, 'control_surface_ratio'):
                    scs += compon.area * compon.control_surface_ratio
                    scs_i += compon.area * compon.control_surface_ratio * \
                             (compon.xle + .25* compon.span * np.tan(compon.sweep))

            if scs > 0:
                comp.cg = [scs_i / scs, 0, 0]
            else:
                comp.cg = [0, 0, 0]

            # Raymer is innacurate
            # Torenbeek method (only factors in for transport aircrafts)
            w_torenbeek = .64 * wdg ** (2/3)

            # Nasa method

            if aircraft.aircraft_type == 'transport':
                w_nasa = 1.1 * aircraft.mach_cruise ** .52 * scs ** .6 * wdg ** .32
                comp.weight = .5 * (w_nasa + w_torenbeek)
            elif aircraft.aircraft_type == 'general_aviation':
                t0 = 519  # Rankine constant
                L = 0.003575  # temp lapse rate (R/ft)
                R = 1716.5  # Gas Constant
                t = t0 - L * aircraft.h_cruise
                theta = t / t0
                delta = theta ** (32.2 / (L * R))
                q_dive = 1481.35 * delta * aircraft.mission.max_mach ** 2
                w_nasa = .404 * aircraft.aero_components['Main Wing'].area ** .317 * (wdg / 1000) ** .602 * aircraft.ultimate_load ** .525 * q_dive ** .345
                comp.weight = w_nasa


        return comp.weight

    def furnishings(self, aircraft, wdg, comp):
        """
        Calculates weight of all miscellaneous furnishings.

        :param object aircraft: aircraft which the furnishings belongs to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the furnishings.

        :return component weight
        :rtype float
        """

        if 'w_furnishings' in self.parameters:
            comp.weight = self.parameters['w_furnishings']
        else:
            if aircraft.aircraft_type == 'transport':
                # Only using nasa, raymer and torenbeek are both complex and inacurate (nasa is same for transport and gen. av.)
                nflcr = aircraft.mission.n_pilots = aircraft.mission.n_flight_attendants
                npass = aircraft.mission.n_passengers
                w = aircraft.aero_components['Fuselage'].width
                d = aircraft.aero_components['Fuselage'].diameter
                xlp = aircraft.aero_components['Fuselage'].length * 80 / 125
                comp.weight = 127 * nflcr + 44 * npass + 2.6 * xlp * (w + d)
            elif aircraft.aircraft_type == 'general_aviation':
                comp.weight = .0582 * wdg - 65
        return comp.weight

    def hydraulics(self, aircraft, wdg, comp):
        """
        Calculates weight of hydraulics.

        :param object aircraft: aircraft which the hydraulics belong to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the hydraulics.

        :return component weight
        :rtype float
        """

        if 'w_hydraulics' in self.parameters:
            comp.weight = self.parameters['w_hydraulics']
        else:
            # Raymer is bad for this one

            # Torenbeek method
            w_torenbeek = .012 * wdg

            # nasa method
            d = aircraft.aero_components['Fuselage'].diameter
            l = aircraft.aero_components['Fuselage'].length

            b = aircraft.aero_components['Main Wing'].span
            s = aircraft.aero_components['Main Wing'].area

            mach = aircraft.cruise_conditions.mach

            n_fuse_engine = 0
            n_wing_engine = 0
            for compo in aircraft.aero_components.values():
                if compo.component_type == 'Nacelle':
                    if compo.attachment == 'Main Wing':
                        n_wing_engine += 2
                    elif compo.attachment == 'Fuselage':
                        n_fuse_engine += 2

            w_nasa = .57 * ((d * l) + (.27 * s)) * (1 + .03 * n_wing_engine + .05 * n_fuse_engine) * mach ** .33

            comp.weight = .5 * (w_nasa + w_torenbeek)

            # this is what was here before but im not sure where I got it from
            # elif aircraft.aircraft_type == 'general_aviation':
            #     s_w = aircraft.aero_components['Main Wing'].area
            #     s_vt = aircraft.aero_components['Vertical Stabilizer'].area
            #     s_ht = aircraft.aero_components['Horizontal Stabilizer'].area
            #     h_tc = aircraft.aero_components['Horizontal Stabilizer'].tc
            #
            #     w_nasa = .6053 * (s_w + 1.44 * (s_ht/(2 + .387 * h_tc)+ s_vt))
            #
            #     comp.weight = w_nasa

        return comp.weight

    def instruments(self, aircraft, wdg, comp):
        """
        Calculates instruments weights.

        :param object aircraft: aircraft which the instruments belong to.
        :param int wdg: takeoff gross weight (lbs)
        :param object comp: component object for the instruments.

        :return component weight
        :rtype float
        """
        if 'w_instruments' in self.parameters:
            comp.weight = self.parameters['w_instruments']
        else:
            # Raymer method
            kr = 1.0
            ktp = 1.0
            l = aircraft.aero_components['Fuselage'].length
            d = aircraft.aero_components['Fuselage'].diameter
            b = aircraft.aero_components['Main Wing'].span
            nflcr = aircraft.mission.n_pilots
            nen = aircraft.n_engines
            w_raymer = 4.509 * kr * ktp * nflcr ** .541 * nen * (l + b) ** .5

            # torenbeek method
            w_torenbeek = nflcr * (15 + .032 * (wdg / 1000)) + nen * (5 + .006 * (wdg / 1000))

            # nasa method
            mach = aircraft.cruise_conditions.mach
            w_nasa = .48 * (l * d) ** .57 * mach ** .5 * (10 + 2.5 * nflcr + nen)

            if aircraft.aircraft_type == 'transport':
                comp.weight = (w_nasa + w_torenbeek + w_raymer) / 3
            elif aircraft.aircraft_type == 'general_aviation':
                comp.weight = w_nasa

        return comp.weight