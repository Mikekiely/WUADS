from .aircraft import Aircraft
import os

def weights_report(aircraft: Aircraft, filename=None):
    """
    Generates a detailed weights report for a given aircraft and writes it to a file.

    :param object aircraft: aircraft which the weights report is for.
    :param str filename: Name of the file that contains the weights report.

    """
    directory = aircraft.output_dir

    if not filename:
        filename = f'{aircraft.file_prefix}_weights.dat'

    with open(os.path.join(directory, filename), 'w') as f:

        f.write(f'Weights Report For Aircraft: {aircraft.title}\n')
        f.write('================================================\n')
        f.write(f'\t\t\t\t\t\t\tWeight (lbs)\n')
        f.write(f'\t\t\t\t\t\t-------------------\n')
        f.write(f'Takeoff Gross Weight: \t\t{aircraft.weight_takeoff:.2f}\n')
        f.write(f'Maximum Takeoff Weight: \t\t{aircraft.weight_max:.2f}\n')
        f.write(f'Operating Empty Weight:\t\t{aircraft.weight_empty:.2f}\n')
        f.write(f'Fuel Weight:\t\t\t\t{aircraft.w_fuel:.2f}\n\n')
        f.write(f'Aircraft Center of Gravity - Empty (ft):\tX:{aircraft.cg_empty[0]:.2f}, Y: {aircraft.cg_empty[1]:.2f}, Z: {aircraft.cg_empty[2]:.2f}\n')
        f.write(
            f'Aircraft Center of Gravity - Full (ft):\t\tX:{aircraft.cg[0]:.2f}, Y: {aircraft.cg[1]:.2f}, Z: {aircraft.cg[2]:.2f}\n\n')
        f.write('================================================\n')
        f.write('          Structural Components\n\n')
        f.write(f'\t\t\t\t\t\tWeight (lbs)\tX cg (ft)\n')
        f.write(f'\t\t\t\t\t\t--------------------------------\n')
        max_variable_name_length = max(len(name) for name in aircraft.aero_components.keys()) + 3

        for comp in aircraft.aero_components.values():
            f.write("{:<{name_width}} {:>{weight_width}.2f} {:>{cg_width}.2f}\n".format(comp.title,
                                                                                  comp.weight,
                                                                                  comp.cg[0],
                                                                   name_width=max_variable_name_length,
                                                                   weight_width=10,
                                                                                  cg_width=12))
            # f.write(f'{comp.title}:\t\t\t\t\t\t{comp.weight}\n')

        f.write('\n================================================\n')
        f.write('             Useful Load \n\n')
        f.write(f'\t\t\t          Weight (lbs)\t\t\tNumber\t\tx cg (ft)\n')
        f.write(f'\t\t            ---------------\t\t-------------   -------\n')
        max_name_width = 15
        f.write("{:<17} {:>11}{:>22}{:>12.2f}\n".format('Passengers',
                                                     aircraft.useful_load.w_passengers,
                                               aircraft.useful_load.n_passengers,
                                                     aircraft.useful_load.cg_passengers[0]))
        f.write("{:<17} {:>11}{:>22}{:>12.2f}\n".format('Pilots', aircraft.useful_load.w_pilots,
                                               aircraft.useful_load.n_pilots,
                                                        aircraft.useful_load.cg_pilots[0]))
        f.write("{:<17} {:>11}{:>22}{:>12.2f}\n".format('Flight Attendants', aircraft.useful_load.w_flight_attendants,
                                               aircraft.useful_load.n_flight_attendants,
                                                        aircraft.useful_load.cg_pilots[0]))
        f.write("{:<17} {:>11}{:>22}{:>12.2f}\n\n".format('Cargo', aircraft.useful_load.w_cargo,
                                                    '', aircraft.useful_load.cg_cargo[0]))

        max_variable_name_length = max(len(name) for name in aircraft.subsystems.components.keys()) + 3

        f.write('================================================\n')
        f.write('          Subsystems\n\n')
        f.write("{:>35}{:>12}\n".format('Weight (lbs)', 'x cg (ft)'))
        f.write("{:>39}\n".format('------------------------------------------'))
        for comp in aircraft.subsystems.components.values():
            f.write("{:<{name_width}} {:>{weight_width}.2f}{:>14.2f}\n".format(comp.title,
                                                                               comp.weight,
                                                                               comp.cg[0],
                                                                   name_width=max_variable_name_length,
                                                                   weight_width=12))

        if aircraft.misc_components:
            f.write('================================================\n')
            f.write('          Misc Weights\n\n')
            f.write("{:>35}{:>12}\n".format('Weight (lbs)', 'x cg (ft)'))
            f.write("{:>39}\n".format('------------------------------------------'))
            for comp in aircraft.misc_components.values():
                f.write("{:<{name_width}} {:>{weight_width}.2f}{:>14.2f}\n".format(comp.title,
                                                                                   comp.weight,
                                                                                   comp.cg[0],
                                                                                   name_width=max_variable_name_length,
                                                                                   weight_width=12))

def mission_profile_report(aircraft, filename=None):

    directory = aircraft.output_dir

    if not filename:
        filename = f'{aircraft.file_prefix}_mission_report.dat'

    with open(os.path.join(directory, filename), 'w') as f:
        f.write(f'Mission profile analysis for Aircraft: {aircraft.title}\n')
        f.write('================================================\n')
        # f.write(f'Maximum Range: {aircraft.}')
        f.write("{:>32} {:>19}\n".format('Range (nmi)', 'Fuel Burnt (lbs)'))
        w_fuel = 0
        for seg in aircraft.mission.mission_profile:
            w_fuel += seg.fuel_burnt
        w_fuel += aircraft.mission.mission_profile[-1].reserve_fuel

        f.write("{:<15} {:>15.2f} {:>17}\n\n".format('Total', aircraft.mission.range, w_fuel))

        for seg in aircraft.mission.mission_profile:
            f.write("{:<15} {:>15.2f} {:>17.2f}\n".format(seg.segment_type, float(seg.range), float(seg.fuel_burnt)))

        try:
            f.write(f"\nReserve and Trap Fuel ({aircraft.mission.mission_profile[-1].wf_reserve*100}%): {aircraft.mission.mission_profile[-1].reserve_fuel:.2f} lbs\n")
        except:
            pass

        i=0
        c1 = 18
        c2 = 15
        for seg in aircraft.mission.mission_profile:
            f.write('\n=========================================================================================\n')
            f.write(f'Segment {i}: {seg.segment_type}\n\n')
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Range (nmi)', seg.range, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Wi (lbs)', seg.wi, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Wn (lbs)', seg.wn, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.6f}\n".format('Weight Fraction', seg.weight_fraction, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n\n".format('Fuel Burnt (lbs)', seg.fuel_burnt, c1=c1, c2=c2))

            if hasattr(seg, 'aoa'):
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Angle of Attack (deg)', seg.aoa, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('Lift/Drag', seg.lift_to_drag, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Cl', seg.cl, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Cd', seg.cd, c1=c1, c2=c2))
            if seg.cdw > 0:
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Cdw', seg.cdw, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n\n".format('Cd0', seg.cd0, c1=c1, c2=c2))

            f.write("\t{:<{c1}}{:>{c2}.2f}\n".format('altitude', seg.altitude, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Mach', seg.mach, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Velocity (ft/s)', seg.velocity, c1=c1, c2=c2))
            f.write("\t{:<{c1}}{:>{c2}.4f}\n\n".format('Time (min)', seg.time/60, c1=c1, c2=c2))

            if seg.thrust > 0:
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Thrust Required (lbf)', seg.thrust, c1=c1, c2=c2))
            if hasattr(seg, 'max_thrust'):
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('Thrust Available (lbf)', seg.max_thrust, c1=c1, c2=c2))
            if seg.sfc > 0:
                f.write("\t{:<{c1}}{:>{c2}.4f}\n".format('SFC (lb/lbf/hr)', seg.sfc, c1=c1, c2=c2))

            i += 1
