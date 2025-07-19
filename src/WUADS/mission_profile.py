import os
import subprocess

from WUADS.flight_conditions import FlightConditions
from WUADS.avl_run import run_AVL, AVL_input, import_coefficients
import numpy as np

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



    def __init__(self):
        pass

    def breguet_range(self, aircraft, wi):
        return 0, 0, 0, 0, 0


class takeoff(MissionSegment):
    thrust_setting = 100

    def __init__(self, thrust_setting=100, time=0, title='takeoff', **kwargs):
        self.title = title
        super().__init__()
        self.time = time
        self.thrust_setting = thrust_setting
        self.segment_type = 'takeoff'

    def breguet_range(self, aircraft, wi):
        # SFC = fuelflow/thrust
        if aircraft.propulsion.engine_type == 'propeller':
            self.sfc, self.max_thrust = aircraft.propulsion.analyze_performance(
                self.altitude, self.mach,
                horse_power=aircraft.propulsion.horse_power,
                fuel_consumption_rate=aircraft.propulsion.fuel_consumption_rate * 1.4
            )
        else:
            self.sfc, self.max_thrust = aircraft.propulsion.analyze_performance(
                self.altitude, self.mach, self.thrust
            )
        thrust = self.thrust_setting * aircraft.propulsion.max_thrust / 100
        #thought this was repeated not sure what the difference between self.sfs and sfc is or self.thrust and thrust why do we need both?
        #sfc, max_thrust = aircraft.propulsion.analyze_performance(self.altitude, self.mach, thrust)
        if aircraft.propulsion.engine_type == 'propeller':
            sfc, max_thrust = aircraft.propulsion.analyze_performance(
                self.altitude, self.mach,
                horse_power=aircraft.propulsion.horse_power,
                fuel_consumption_rate=aircraft.propulsion.fuel_consumption_rate * 1.4
            )
        else:
            sfc, max_thrust = aircraft.propulsion.analyze_performance(
                self.altitude, self.mach, self.thrust
            )
        fuel_flow = sfc * thrust  # Lbs / hr
        self.fuel_burnt = fuel_flow * self.time
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

    def __init__(self, title='climb', start_velocity=0, end_velocity=0, start_altitude=0, end_altitude=0, best_climb=False, **kwargs):
        super().__init__()
        self.title = title
        self.__dict__.update(kwargs)
        self.best_climb = best_climb
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




    def breguet_range(self, aircraft, wi):
        cd0, cdw = aircraft.get_cd0(self.altitude, self.mach)

        if self.run_sim:
            AVL_input(aircraft, aircraft.weight_takeoff, mach=self.mach)
            run_AVL(self.flight_conditions, aircraft, cd0=cd0, cdw=cdw)

            self.cl, self.cd = import_coefficients()
        else:
            self.cl = aircraft.weight_takeoff / (self.flight_conditions.q * aircraft.sref)
            self.cd = aircraft.cd0 * 1.87  # TODO Make this better (induced drag estimation)

        self.lift_to_drag = self.cl / self.cd

        cd0 = aircraft.cd0 * aircraft.cruise_conditions.q / self.flight_conditions.q
        K = (self.cd - cd0) / self.cl ** 2
        self.K = K

        a = aircraft.aero_components['Main Wing'].aspect_ratio
        sweep = aircraft.aero_components['Main Wing'].sweep_le
        if (sweep * 180 / np.pi) > 30:
            e = 4.61 * (1 - .045 * a**.68) * np.cos(sweep) ** .15 - 3.1
        else:
            e = 1.78 * (1 - .045 * a**.68) - .64

        g = 32.1
        q = self.flight_conditions.q
        sref = aircraft.sref
        D = self.cd * q * sref
        self.thrust = D
        delta_he = (self.end_altitude + 1 / (2 * g) * self.end_velocity ** 2) - (1 / (2 * g) * self.start_velocity ** 2)

        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.altitude, self.flight_conditions.mach, self.thrust)

        if self.power_available > 0:
            pav = self.power_available / .0009478171 * .453592
            max_thrust = pav / self.velocity

        self.max_thrust = max_thrust
        self.weight_fraction = np.exp(
        -(self.sfc / 3600) * delta_he / (self.velocity * (1 - D / max_thrust)))
        climb_angle = np.arcsin(max_thrust / wi - D / wi)
        rate_of_climb = self.velocity * np.sin(climb_angle)
        self.rate_of_climb = rate_of_climb
        self.time = (self.end_altitude - self.start_altitude) / rate_of_climb
        self.range = self.velocity * self.time / 6076.12
        self.fuel_burnt = self.sfc * D * self.time
        self.fuel_burnt = self.max_thrust * self.sfc * self.time
        self.wi = wi
        self.wn = wi * self.weight_fraction
        self.fuel_burnt = self.wi - self.wn
        # self.power_required = self.velocity * self.thrust
        self.power_required_kw = self.power_required * .001355818


class cruise(MissionSegment):
    wn = 0
    range = None

    def __init__(self, aircraft=None, mach=0, altitude=0, title='cruise', find_range=True, range=None, **kwargs):
        self.title = title
        super().__init__()
        self.mach = mach
        self.altitude = altitude
        self.flight_conditions = aircraft.cruise_conditions
        self.find_range = find_range

        self.range = range
        self.run_sim = True
        fc = FlightConditions(self.altitude, self.mach)
        self.flight_conditions = fc
        self.velocity = fc.velocity
        self.segment_type = 'cruise'

    def breguet_range(self, aircraft, wn=None, wi=None):
        # determines the fuel burnt during a set range cruise segment
        if self.range is None:
            print('Please input a desired range or set find_range to true')
            return

        if wi:
            self.wi = wi
            weight = wi
        elif wn:
            self.wn = wn
            weight = wn

        AVL_input(aircraft, weight)
        run_AVL(self.flight_conditions, aircraft)
        self.cl, self.cd = import_coefficients()
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
        self.cl, self.cd = import_coefficients()
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
    def __init__(self, title='descent', weight_fraction=1, **kwargs):
        self.title = title
        super().__init__()
        self.weight_fraction = weight_fraction
        self.segment_type = 'descent'

    def breguet_range(self, aircraft, wn):
        self.wn = wn
        self.wi = wn / self.weight_fraction
        self.power_required = 0
        self.power_required_kw = 0
        self.altitude = .5 * aircraft.cruise_conditions.h
        self.velocity = .5 * aircraft.cruise_conditions.velocity
        self.fuel_burnt = self.wi - self.wn
        rate_of_descent = 5000 * 60     # ft/hr
        self.time = self.altitude * 2 / rate_of_descent # TODO make this better
        self.range = self.velocity * .592484 * self.time


class loiter(MissionSegment):


    def __init__(self, title='loiter', altitude=0, time=0, mach=None, **kwargs):
        """
        Initiate a loiter segment
        :param altitude: Loiter altitude (ft)
        :param time: Loiter time (hours)
        """
        self.title = title
        super().__init__()
        self.altitude = altitude
        self.time = time
        if not mach:
            self.mach = .25

    def breguet_range(self, aircraft, wn):
        K = 0
        for seg in aircraft.Mission.mission_profile:
            if hasattr(seg, 'K'):
                K = seg.K
                self.mach = seg.mach
                break

        cd0, _ = aircraft.get_cd0(self.altitude, self.mach)
        self.flight_conditions = FlightConditions(self.altitude, self.mach)
        self.velocity = np.sqrt(2 * wn / (self.flight_conditions.rho * aircraft.sref) * np.sqrt(K / (3 * cd0)))
        self.velocity = 200
        self.mach = self.velocity / self.flight_conditions.a
        self.flight_conditions = FlightConditions(self.altitude, self.mach)
        E = self.time * 3600

        self.cl = wn / (self.flight_conditions.q * aircraft.sref)

        self.cd = cd0 + K * self.cl**2

        self.thrust = self.cd * self.flight_conditions.q * aircraft.sref
        self.sfc, max_thrust = aircraft.propulsion.analyze_performance(self.flight_conditions.altitude,
                                                                      self.flight_conditions.mach,
                                                                      self.thrust)


        self.lift_to_drag = self.cl / self.cd
        self.weight_fraction = np.exp(-E * self.sfc/3600 / self.lift_to_drag)
        self.wn = wn
        self.wi = wn / self.weight_fraction
        self.fuel_burnt = self.wi - self.wn
        self.range = self.time * self.flight_conditions.velocity


class landing(MissionSegment):
    reserve_fuel = 0
    wf_reserve = 0
    w_landing = 0

    def __init__(self, title='landing', weight_fraction=1, reserve_fuel=0, **kwargs):
        self.title = title
        super().__init__()
        self.weight_fraction = weight_fraction
        self.wf_reserve = reserve_fuel
        self.segment_type = 'landing'

    def breguet_range(self, aircraft, wn):
        self.reserve_fuel = aircraft.UsefulLoad.w_fuel * self.wf_reserve
        w_landing = aircraft.weight_takeoff - aircraft.UsefulLoad.w_fuel + self.reserve_fuel
        self.wn = w_landing
        self.wi = w_landing / self.weight_fraction
        self.power_required = 0
        self.power_required_kw = 0
        self.fuel_burnt = self.wi - self.wn
