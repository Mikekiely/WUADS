import os
import subprocess

from WUADS.flight_conditions import FlightConditions
import numpy as np

class mission_segment:
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


class takeoff(mission_segment):
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

class climb(mission_segment):
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


class cruise(mission_segment):
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


class descent(mission_segment):
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


class loiter(mission_segment):


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


class landing(mission_segment):
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


# Writes .avl file readable by avl
# Writes avl geometry file
def AVL_input(ac, w, mach=None):
    if mach == None:
        mach = ac.cruise_conditions.mach

    # Writes a .avl file thats readable by the program
    fid = open('plane.avl', 'w')

    fid.write('AVL Geometry\n\n')
    fid.write('#Mach\n')
    fid.write(f'{mach}\n\n')
    fid.write('#IYsym   IZsym   Zsym\n')
    fid.write('0       0       0\n')
    fid.write('#Sref    Cref    Bref\n')
    fid.write("{0}   {1}   {2}\n\n".format(ac.sref, ac.aero_components['Main Wing'].cref, ac.aero_components['Main Wing'].span))
    fid.write("#Xref    Yref    Zref\n")
    fid.write('{0}     {1}     {2}\n'.format(ac.cg[0], ac.cg[1], ac.cg[2]))
    fid.write('#--------------------------------------------------\n')

    components = {}
    components['Main Wing'] = ac.aero_components['Main Wing']
    for comp in ac.aero_components.keys():
        if not comp == 'Main Wing':
            components[comp] = ac.aero_components[comp]

    for comp in components.values():
        if comp.aero_body:
            fid.write('SURFACE\n')
            fid.write('{0}\n\n'.format(comp.title))
            fid.write('!Nchordwise  Cspace  Nspanwise  Sspace\n')
            fid.write('12           2.0     26         -1.5\n')
            if 'wing' in comp.component_type.lower():
                fid.write('Component\n')
                fid.write('1\n\n')
                fid.write('Angle\n2 \n\n')

            if 'vertical' not in comp.component_type:
                fid.write('YDUPLICATE\n')
                fid.write('0\n\n')

            fid.write('SCALE\n')
            fid.write('1   1   1\n\n')

            # Sections
            for j in range(len(comp.sections)):
                fid.write('Section\n')
                fid.write('#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace\n')
                fid.write('{0}  {1}  {2}  {3}  {4}\n'.format(comp.sections[j][0], comp.sections[j][1],
                                                             comp.sections[j][2], comp.sections[j][3],
                                                             comp.sections[j][4]))

                if 'horizontal' in comp.component_type.casefold():
                    fid.write('Control\n')
                    fid.write('Elevator 3.0 .2 0. 1. 0. 1\n')
                if len(comp.airfoil) != 0:
                    fid.write('AFILE\n')
                    fid.write('{0}\n\n'.format(comp.airfoil))
                else:
                    fid.write('\n')

            fid.write('#--------------------------------------------------\n')

    fid.close()

    # Write Mass File
    fid = open('plane.mass', 'w')
    fid.write('Lunit = 3.048000e-01 m\n')
    fid.write('Munit = 4.535000e-01 kg\n')
    fid.write('Tunit = 1 s\n\n')
    fid.write('{0}  {1}  {2}  {3}  {4}  {5}  {6}\n'.format(w, ac.cg[0], ac.cg[1], ac.cg[2], ac.inertia[0], ac.inertia[1], ac.inertia[2]))
    fid.close()



# runs specified case and saves results in derivs.st file
def run_AVL(fc, ac, cd0=None, cdw=None):

    if cd0 is None:
        cd0 = ac.cd0
    if cdw is None:
        cdw = ac.cdw

    # Conversion Factors
    slg2kgm = 515.379
    ft2m = 0.3048

    # %% Inputs
    geom_file = "plane.avl"
    mass_file = "plane.mass"
    h = fc.h
    M = fc.mach
    Cd0 = cd0 + cdw

    a = fc.a * ft2m
    V = M * a

    # %% XFOIL input file writer
    if os.path.exists("derivs.st"):
        os.remove("derivs.st")

    input_file = open("input_file.in", 'w')
    input_file.write("LOAD {0}\n".format(geom_file))
    input_file.write("Mass {0}\n".format(mass_file))
    input_file.write("MSET\n")
    input_file.write("0\n")

    input_file.write("Oper\n")
    input_file.write("C1\n")
    input_file.write("G {0}\n".format(9.81))
    input_file.write("D {0}\n".format(fc.rho * slg2kgm))
    input_file.write("V {0}\n\n".format(V))

    input_file.write("D1 PM 0\n")
    # input_file.write("D1 a 3")
    input_file.write("M\n")
    input_file.write("MN {0}\n".format(M))
    input_file.write("CD {0}\n\n".format(Cd0))

    input_file.write("x\n")
    input_file.write("st\n")
    input_file.write("derivs.st\n\n")

    input_file.write("Quit\n\n")
    input_file.close()

    subprocess.call('avl.exe < input_file.in', shell=True, stdout=subprocess.DEVNULL)

# Imports lift and drag coefficients from output derivs.st file
def import_coefficients():
    try:
        with open('derivs.st', 'r') as fid:
            derivs = fid.readlines()[23:25]
    except FileNotFoundError:
        raise FileNotFoundError('AVL failed to achieve trim conditions')

    cl = []
    for t in derivs[0].split():
        try:
            cl.append(float(t))
        except ValueError:
            pass

    cd = []
    for t in derivs[1].split():
        try:
            cd.append(float(t))
        except ValueError:
            pass
    return cl[0], cd[0]

def mission_profile_report(aircraft, filename):
    with open(filename, 'w') as f:
        f.write(f'Mission profile analysis for Aircraft: {aircraft.title}\n')
        f.write('================================================\n')
        # f.write(f'Maximum Range: {aircraft.}')
        f.write("{:>32} {:>19}\n".format('Range (nmi)', 'Fuel Burnt (lbs)'))
        f.write("{:<15} {:>15.2f} {:>17}\n\n".format('Total', aircraft.range, aircraft.UsefulLoad.w_fuel))

        for seg in aircraft.mission_profile:
            f.write("{:<15} {:>15.2f} {:>17.2f}\n".format(seg.segment_type, float(seg.range), float(seg.fuel_burnt)))

        f.write(f"\nReserve and Trap Fuel ({aircraft.mission_profile[-1].wf_reserve*100}%): {aircraft.mission_profile[-1].reserve_fuel:.2f} lbs\n")

        i=0
        c1 = 18
        c2 = 15
        for seg in aircraft.mission_profile:
            f.write('\n=========================================================================================\n')
            f.write(f'Segment {i}: {seg.segment_type}\n\n')
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Range (nmi)', seg.range, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Wi (lbs)', seg.wi, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Wn (lbs)', seg.wn, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.6f}\n".format('Weight Fraction', seg.weight_fraction, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n\n".format('Fuel Burnt (lbs)', seg.fuel_burnt, c1=c1, c2=c2))

            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Lift/Drag', seg.lift_to_drag, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Cl', seg.cl, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n\n".format('Cd', seg.cd, c1=c1, c2=c2))

            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('altitude', seg.altitude, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Mach', seg.mach, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Velocity (m/s)', seg.velocity, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n\n".format('Time (min)', seg.time/60, c1=c1, c2=c2))

            if seg.thrust > 0:
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Thrust Required (lbf)', seg.thrust, c1=c1, c2=c2))
            if hasattr(seg, 'max_thrust'):
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Thrust Available (lbf)', seg.max_thrust, c1=c1, c2=c2))
            if seg.sfc > 0:
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('SFC (lb/lbf/hr)', seg.sfc, c1=c1, c2=c2))

            i += 1



