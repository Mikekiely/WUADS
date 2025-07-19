import os
import subprocess

# Writes .avl file readable by avl
# Writes avl geometry file
def AVL_input(ac, w, mach=None):
    if mach == None:
        mach = ac.cruise_conditions.mach

    output_dir = ac.output_dir
    plane_file = os.path.join(output_dir, f'{ac.file_prefix}_plane.avl')
    mass_file = os.path.join(output_dir, f'{ac.file_prefix}_mass.avl')

    # Writes a .avl file that's readable by the program
    fid = open(plane_file, 'w')

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
            for j in range(len(comp._avl_sections)):
                fid.write('Section\n')
                fid.write('#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace\n')
                fid.write('{0}  {1}  {2}  {3}  {4}\n'.format(comp._avl_sections[j][0], comp._avl_sections[j][1],
                                                             comp._avl_sections[j][2], comp._avl_sections[j][3],
                                                             comp._avl_sections[j][4]))

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

    output_dir = ac.output_dir
    derivs_file = os.path.join(output_dir, 'derivs.dat')

    # Conversion Factors
    slg2kgm = 515.379
    ft2m = 0.3048

    # %% Inputs
    geom_file = "plane.avl"
    mass_file = "plane.mass"
    h = fc.altitude
    M = fc.mach
    Cd0 = cd0 + cdw

    a = fc.a * ft2m
    V = M * a

    # %% XFOIL input file writer
    if os.path.exists(derivs_file):
        os.remove(derivs_file)

    commands = (f"LOAD {ge}")

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



