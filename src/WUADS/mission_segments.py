import os
import subprocess

from .flight_conditions import FlightConditions
from .avl_run import run_AVL, AVL_input, import_coefficients
import numpy as np
import sys

class MissionSegment:
    """
    Base class for all mission_rae2822 segments.
    """
    segment_type = ''
    range = 0
    altitude = 0
    mach = 0
    thrust = 0
    sfc = 0
    velocity = 0
    cl = 0
    cd = 0
    cd0 = 0
    cdw = 0

    fuel_burnt = 0
    weight_fraction = 0
    time = 0
    lift_to_drag = 0
    find_range = False
    run_sim = False
    flight_conditions = []

    wi = 0
    wn = 0

    power_required = 0
    power_required_kw = 0
    input_params = []


    def __init__(self):
        pass

    def breguet_range(self, aircraft, wi):
        return 0, 0, 0, 0, 0


class takeoff(MissionSegment):
    thrust_setting = 100
    input_params = ['thrust_setting', 'time', 'title']

    def __init__(self, thrust_setting=100, time=0, title='takeoff', **kwargs):
        self.title = title
        super().__init__()
        self.time = time * 60
        self.thrust_setting = thrust_setting
        self.segment_type = 'takeoff'

    def breguet_range(self, aircraft, wi=None, wn=None):
        # SFC = fuelflow/thrust
        thrust = self.thrust_setting * aircraft.propulsion.max_thrust
        self.sfc, self.max_thrust = aircraft.propulsion.analyze_performance(
                self.altitude, self.mach, self.thrust
            )
        sfc = self.sfc
        fuel_flow = sfc * thrust  # Lbs / hr
        self.fuel_burnt = fuel_flow * self.time/3600
        self.weight_fraction = (wi - self.fuel_burnt) / wi
        self.thrust = thrust
        self.sfc = sfc
        self.fuel_flow = fuel_flow
        self.wi = wi
        self.wn = wi * self.weight_fraction

class climb(MissionSegment):
    start_velocity = 0
    end_velocity = 0
    start_altitude = 0
    end_altitude = 0
    divisions = 1
    best_climb = False
    power_available = 0
    rate_of_climb = 0
    max_thrust = 0
    K = 0
    input_params = ['start_velocity', 'end_velocity', 'start_altitude', 'end_altitude', 'title']

    def __init__(self, title='climb', start_velocity=0, end_velocity=0, start_altitude=0, end_altitude=0, **kwargs):
        super().__init__()
        self.title = title
        self.__dict__.update(kwargs)
        self.start_velocity = start_velocity
        self.end_velocity = end_velocity
        self.start_altitude = start_altitude
        self.end_altitude = end_altitude
        self.divisions = 1
        self.segment_type='climb'

        self.velocity = .293 * start_velocity + .707 * end_velocity
        self.altitude = .5*(start_altitude + end_altitude)
        fc = FlightConditions(self.altitude, 0)

        self.mach = self.velocity / fc.a
        fc = FlightConditions(self.altitude, self.mach)
        self.flight_conditions = fc

    def breguet_range(self, aircraft, wi=None, wn=None):
        cd0, cdw = aircraft.get_cd0(self.altitude, self.mach)
        self.cd0 = cd0

        if wi:
            weight = wi
        else:
            weight = wn

        if self.run_sim:
            AVL_input(aircraft, aircraft.weight_takeoff, mach=self.mach)
            run_AVL(self.flight_conditions, aircraft, cd0=cd0, cdw=cdw)

            self.cl, self.cd = import_coefficients(aircraft, self)
        else:
            self.cl = aircraft.weight_takeoff / (self.flight_conditions.q * aircraft.sref)* 1.3
            a = aircraft.aero_components['Main Wing'].aspect_ratio
            sweep = aircraft.aero_components['Main Wing'].sweep_le
            if (sweep * 180 / np.pi) > 30:
                e = 4.61 * (1 - .045 * a ** .68) * np.cos(sweep) ** .15 - 3.1
            else:
                e = 1.78 * (1 - .045 * a ** .68) - .64
            cdi = self.cl**2 / (np.pi * a * e)
            self.cd = cd0 + cdi

        self.lift_to_drag = self.cl / self.cd

        K = (self.cd - cd0) / self.cl ** 2
        self.K = K

        g = 32.1
        q = self.flight_conditions.q
        sref = aircraft.sref
        D = self.cd * q * sref
        self.thrust = D
        delta_he = (self.end_altitude + 1 / (2 * g) * self.end_velocity ** 2) - (1 / (2 * g) * self.start_velocity ** 2)

        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.altitude, self.flight_conditions.mach, self.thrust)

        self.max_thrust = max_thrust
        self.weight_fraction = np.exp(
        -(self.sfc / 3600) * delta_he / (self.velocity * (1 - D / max_thrust)))
        climb_angle = np.arcsin(max_thrust / weight - D / weight)
        rate_of_climb = self.velocity * np.sin(climb_angle)
        self.rate_of_climb = rate_of_climb
        self.time = (self.end_altitude - self.start_altitude) / rate_of_climb
        self.range = self.velocity * self.time / 6076.12
        self.fuel_burnt = self.sfc * D * self.time
        self.fuel_burnt = self.max_thrust * self.sfc * self.time

        if wn:
            wi = wn / self.weight_fraction
        else:
            wn = wi * self.weight_fraction

        self.wi = wi
        self.wn = wn
        self.fuel_burnt = self.wi - self.wn


class cruise(MissionSegment):
    wn = 0
    range = None
    input_params = ['mach', 'altitude', 'title', 'find_range', 'range']

    def __init__(self, mach=0, altitude=0, title='cruise', find_range=True, range=None, **kwargs):
        self.title = title
        super().__init__()
        self.mach = mach
        self.altitude = altitude
        self.find_range = find_range
        if find_range:
            self.range = range
            if hasattr(self.input_params, 'range'):
                self.input_params.remove('range')
        else:
            self.range = range
        self.run_sim = True
        fc = FlightConditions(self.altitude, self.mach)
        self.flight_conditions = fc
        self.velocity = fc.velocity
        self.segment_type = 'cruise'

    def breguet_range(self, aircraft, wn=None, wi=None):
        # determines the fuel burnt during a set range cruise segment

        self.flight_conditions = aircraft.cruise_conditions

        self.cd0, self.cdw = aircraft.get_cd0(self.altitude, self.mach)
        if self.range is None:
            sys.exit('Please input a desired range or set find_range to true')
            logger.error('Please input a desired range or set find_range to true')

        if wi:
            self.wi = wi
            weight = wi
        elif wn:
            self.wn = wn
            weight = wn

        AVL_input(aircraft, weight)
        run_AVL(self.flight_conditions, aircraft)
        self.cl, self.cd = import_coefficients(aircraft, self)
        self.lift_to_drag = self.cl / self.cd
        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.flight_conditions.altitude,
                                                                      self.flight_conditions.mach,
                                                                      self.thrust)

        range_feet = self.range * 6076.12
        self.weight_fraction = np.exp(-range_feet * self.sfc / 3600 / (self.flight_conditions.velocity * self.lift_to_drag))
        if wi:
            self.wn = wi * self.weight_fraction
        elif wn:
            self.wi = wn / self.weight_fraction
        self.fuel_burnt = self.wi - self.wn

        self.time = range_feet / self.velocity


    def set_range(self, aircraft, wi, wn):
        self.wi = wi
        self.wn = wn
        # self.wi = (wi + wn) / 2

        AVL_input(aircraft, self.wi)
        run_AVL(self.flight_conditions, aircraft)
        self.cl, self.cd = import_coefficients(aircraft, self)
        self.lift_to_drag = self.cl / self.cd

        self.weight_fraction = wn / wi
        k = (self.cd - aircraft.cd0) / self.cl ** 2

        g = 32.1
        q = self.flight_conditions.q
        sref = aircraft.sref
        D = self.cd * q * sref
        self.thrust = D
        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.flight_conditions.altitude, self.flight_conditions.mach,
                                                      self.thrust)


        sfc = self.sfc / 3600

        self.range = np.log(self.weight_fraction) * self.flight_conditions.velocity * self.lift_to_drag / (-sfc) / 6076.12
        self.fuel_burnt = wi-wn
        range_feet = self.range * 6076.12
        self.time = range_feet / self.flight_conditions.velocity
        self.max_thrust = max_thrust


class descent(MissionSegment):
    input_params = ['title', 'weight_fraction']
    def __init__(self, title='descent', weight_fraction=1, **kwargs):
        self.title = title
        super().__init__()
        self.weight_fraction = weight_fraction
        self.segment_type = 'descent'

    def breguet_range(self, aircraft, wi=None, wn=None):

        if wi:
            self.wi = wi
            self.wn = wi * self.weight_fraction
        else:
            self.wn = wn
            self.wi = wn / self.weight_fraction

        self.power_required = 0
        self.power_required_kw = 0
        self.altitude = .5 * aircraft.cruise_conditions.altitude
        self.velocity = .5 * aircraft.cruise_conditions.velocity
        self.fuel_burnt = self.wi - self.wn
        rate_of_descent = 5000 * 60     # ft/hr
        self.time = self.altitude * 2 / rate_of_descent # TODO make this better
        self.range = self.velocity * .592484 * self.time


class loiter(MissionSegment):
    input_params = ['title', 'altitude', 'time', 'mach']
    def __init__(self, title='loiter', altitude=0, time=0, mach=None, run_sim=False, best_velocity=False, **kwargs):
        """
        Initiate a loiter segment
        :param altitude: Loiter altitude (ft)
        :param time: Loiter time (hours)
        """
        self.title = title
        super().__init__()
        self.altitude = altitude
        self.time = time
        self.segment_type = 'loiter'
        self.run_sim = run_sim
        self.best_velocity = best_velocity
        if not mach:
            self.mach = .25
        else:
            self.mach = mach

    def breguet_range(self, aircraft, wi=None, wn=None):
        K = 0
        cd0, cdw = aircraft.get_cd0(self.altitude, self.mach)
        self.cd0 = cd0
        self.flight_conditions = FlightConditions(self.altitude, self.mach)
        if wi:
            weight = wi
        else:
            weight = wn

        if self.run_sim:
            AVL_input(aircraft, weight, mach=self.mach)
            run_AVL(self.flight_conditions, aircraft, cd0=cd0, cdw=cdw)

            self.cl, self.cd = import_coefficients(aircraft, self)
            K = (self.cd - cd0) / self.cl ** 2
            self.K = K
        else:
            for seg in aircraft.mission.mission_profile:
                if hasattr(seg, 'K'):
                    K = seg.K
                    self.mach = seg.mach
                    break

            self.cl = weight / (self.flight_conditions.q * aircraft.sref)
            self.cd = cd0 + K * self.cl ** 2




        #TODO fix this, add an actual K calculator
        if self.best_velocity:
            self.velocity = np.sqrt(2 * wn / (self.flight_conditions.rho * aircraft.sref) * np.sqrt(K / (3 * cd0)))
            self.mach = self.velocity / self.flight_conditions.a
            self.flight_conditions = FlightConditions(self.altitude, self.mach)
        E = self.time * 3600



        self.thrust = self.cd * self.flight_conditions.q * aircraft.sref
        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.flight_conditions.altitude,
                                                                      self.flight_conditions.mach,
                                                                      self.thrust)

        self.lift_to_drag = self.cl / self.cd
        self.weight_fraction = np.exp(-E * self.sfc/3600 / self.lift_to_drag)

        if wi:
            wn = wi * self.weight_fraction
        else:
            wi = wn / self.weight_fraction

        self.wn = wn
        self.wi = wi
        self.fuel_burnt = self.wi - self.wn
        self.range = self.time * self.flight_conditions.velocity


class landing(MissionSegment):
    reserve_fuel = 0
    wf_reserve = 0
    w_landing = 0
    input_params = ['title', 'weight_fraction', 'reserve_fuel']

    def __init__(self, title='landing', weight_fraction=1, reserve_fuel=0, **kwargs):
        self.title = title
        super().__init__()
        self.weight_fraction = weight_fraction
        self.wf_reserve = reserve_fuel
        self.segment_type = 'landing'

    def breguet_range(self, aircraft, wi=None, wn=None):
        self.reserve_fuel = aircraft.w_fuel * self.wf_reserve
        w_landing = aircraft.weight_takeoff - aircraft.w_fuel + self.reserve_fuel

        if wi:
            weight = wi
        else:
            weight = wn

        self.wn = w_landing
        self.wi = w_landing / self.weight_fraction
        self.power_required = 0
        self.power_required_kw = 0
        self.fuel_burnt = self.wi - self.wn


class weight_drop(MissionSegment):
    # Instantaneous weight drop
    weight_dropped = 0
    input_params = ['title', 'weight_dropped']

    def __init__(self, title='weight_drop', weight_dropped=0, **kwargs):
        self.title = title
        super().__init__()
        self.weight_dropped = weight_dropped
        self.segment_type = 'weight_drop'

    def breguet_range(self, aircraft, wi=None, wn=None):

        if wi:
            wn = wi - self.weight_dropped
        else:
            wi = wn + self.weight_dropped

        self.wn = wn
        self.wi = wi
        self.fuel_burnt = 0
        self.weight_fraction = 1

#TODO test out wieght drop
