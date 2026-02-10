import pyvista as pv
import numpy as np
from scipy.interpolate import splprep, splev
from PySide6.QtWidgets import QVBoxLayout, QFrame
from pyvistaqt import QtInteractor
from pathlib import Path
from importlib import resources


class graphics(QFrame):
    """
    Main graphics display

    Uses Pyvista for 3D graphics display
    """
    meshes = {}
    selected_component = ''

    # Initiate graphics window widget and plotter
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # Create frame and graphics plotter
        self.setFrameShape(QFrame.StyledPanel)
        vlayout = QVBoxLayout()
        self.plotter = QtInteractor(self)

        vlayout.addWidget(self.plotter.interactor)
        self.setLayout(vlayout)

    # Plots all components declared in aircraft.aero_components
    def plot_aircraft(self, aircraft):
        # Add meshes for all components
        for comp in aircraft.aero_components.values():
            mesh = plot_component(comp)
            # self.meshes[comp.title] = plot_component(comp)
            try:
                self.meshes[comp.title] = self.plotter.add_mesh(mesh, show_edges=False, color='grey', metallic=.25, pbr=True)
            except:
                print(f'Failed to Mesh {comp.title}')

        # Rotate default camera position
        pos, focal_point, up = self.plotter.camera_position
        new_pos =[-264.1594486764661, -197.83994171675525, 210.9712561359443]
        self.plotter.camera_position = [[-264.1594486764661, -197.83994171675525, 210.9712561359443], focal_point, up]
        self.plotter.reset_camera()
        self.plotter.render()
        # self.plotter.camera.zoom('tight')


    # Updates a given component and replots it
    def update_component(self, component):
        # Remove mesh if the component is deleted
        try:
            comp = self.parent.aircraft.aero_components[component]
        except KeyError:
            if component in self.meshes:
                self.plotter.remove_actor(self.meshes[component])
                self.plotter.update()
            return

        if component in self.meshes:
            self.plotter.remove_actor(self.meshes[component])
        mesh = plot_component(comp)
        self.meshes[component] = self.plotter.add_mesh(mesh, show_edges=False, color='grey', metallic=.25, pbr=True)
        self.plotter.update()


    # Highlights selected component
    def handleComponentSelected(self, component):
        if self.selected_component and self.selected_component in self.meshes:
            self.meshes[self.selected_component].prop.color = 'grey'
        self.selected_component = component
        if component in self.meshes:
            self.meshes[component].prop.color = 'red'
        self.plotter.update()

    def handleComponentRenamed(self, old_title, new_title):
        self.meshes[new_title] = self.meshes.pop(old_title)




def interpolate_curve(x, y, num_points=100):
    # Calculate the spline representation of the curve
    tck, u = splprep([x, y], s=0)

    # Generate a finer parameterization of the curve
    u_interp = np.linspace(0, 1, num_points)

    # Perform spline interpolation to get new x and y values
    x_interp, y_interp = splev(u_interp, tck)

    return x_interp, y_interp

#TODO graphics and gui support for advanced wings

def plot_wing(wing):
    try:
        # Installed package case
        airfoil_path = resources.files("WUADS.assets").joinpath("naca_0012.dat")
        with airfoil_path.open("r", encoding="utf-8") as f:
            clean_lines = (" ".join(line.strip().split()) for line in f)
            data = np.genfromtxt(clean_lines, delimiter=" ")
    except (ModuleNotFoundError, AttributeError, FileNotFoundError):
        # Cloned repo fallback
        airfoil_path = Path(__file__).parent.parent / "assets" / "naca_0012.dat"
        with airfoil_path.open("r", encoding="utf-8") as f:
            clean_lines = (" ".join(line.strip().split()) for line in f)
            data = np.genfromtxt(clean_lines, delimiter=" ")

    vert = False
    if wing.component_type == 'Vertical':
        vert = True

    # Set profile airfoil
    x_u = data[:len(data) // 2, 0]
    x_l = data[len(data) // 2:, 0]
    y_u = data[:len(data) // 2, 1]
    y_l = data[len(data) // 2:, 1]
    x_profile = np.concatenate([x_u, list(reversed(x_l))])
    z_profile = np.concatenate([y_u, list(reversed(y_l))])

    # Set parameters

    if not vert:
        b = wing.span / 2  # semi span
    else:
        b = wing.span
    taper = wing.taper
    sweep = wing.sweep_le
    if wing.area == 0:
        S = .5 * wing.span * (wing.ct + wing.cr)
    else:
        S = wing.area
    dihedral = wing.dihedral

    x = []
    y = []
    z = []

    n = 50
    if vert:
        yle_ar = np.linspace(wing.zle, wing.zle + b, n)
    else:
        yle_ar = np.linspace(wing.yle, wing.yle + b, n)

    scaled = False
    if len(wing.airfoil_thickness) >= 2:
        scale_factor = np.linspace((wing.airfoil_thickness[0] / .12), (wing.airfoil_thickness[1] / .12), n)
        scaled = True

    for i in range(len(yle_ar)):
        yle = yle_ar[i]
        if not vert:
            xle = wing.xle + (yle - wing.yle) * np.tan(sweep)
            zle = wing.zle + (yle - wing.yle) * np.tan(dihedral)
            chord = S / ((1 + taper) * b) * (1 - (1 - taper) / (2 * b) * np.abs(2 * (yle - wing.yle)))
            x.append(np.array(x_profile * chord + xle))
            y.append(np.linspace(yle, yle, len(x_profile)))

            if scaled:
                z.append(np.array((z_profile * chord) * scale_factor[i] + zle))
            else:
                z.append(np.array(z_profile * chord + zle))
        else:
            zle = yle
            xle = wing.xle + (zle - wing.zle) * np.tan(sweep)
            chord = S / ((1 + taper) * b) * (1 - (1 - taper) / (2 * b) * np.abs(2 * (zle - wing.zle))) * 1.3
            x.append(np.array(x_profile * chord + xle))
            y.append(np.array(z_profile*chord))
            z.append(np.linspace(zle, zle, len(x_profile)))

    if vert:
        chord = .001
        x.append(np.array(x_profile * chord + xle))
        y.append(np.array(z_profile * chord))
        z.append(np.linspace(zle, zle, len(x_profile)))
    else:
        choord = .001
        x.append(np.array(x_profile * chord + xle))
        y.append(np.linspace(yle, yle, len(x_profile)))
        z.append(np.array(z_profile * chord + zle))

    return np.array(x), np.array(y), np.array(z)

def plot_fuselage(fuselage):
    if fuselage.diameter == 0 or fuselage.length == 0:
        return None, None, None

    x = [0, 2.84, 6.2, 8.76, 11.67, 17.6, 37.3, 55.5, 81.8, 94.9, 105, 114.7, 125]
    z = [-2.75, -2.17, -1.35, -.62, -.03, 0, 0, 0, 0, .54, 2.13, 3.5, 5.4]
    d = [.1, 5.149, 7.937, 10.3, 12.157, 13.2, 13.2, 13.2, 13.2, 12.120, 8.94, 6.20, 2.4]

    l = fuselage.length
    w = fuselage.diameter

    x_max = x[-1]
    x = [(i / x_max) * l for i in x]
    z = [(i / x_max) * l for i in z]
    d_max = np.max(d)
    d = [i / d_max * w for i in d]
    r = [i * .5 for i in d]

    x_surf = []
    y_surf = []
    z_surf = []

    # Interpolate fuselage curve
    n_length = 50
    n_cross_section = 50
    x_base = x
    x, r = interpolate_curve(x, r, n_length)
    x, z = interpolate_curve(x_base, z, n_length)

    for i in range(len(x)):
        x_fuse = []
        y_fuse = []
        z_fuse = []
        # theta = np.linspace(0, 2 * np.pi, n_cross_section)
        theta = np.linspace(-np.pi / 2, np.pi / 2, n_cross_section)
        for t in theta:
            x_fuse.append(x[i])
            y_fuse.append(r[i] * np.cos(t))
            z_fuse.append(z[i] + r[i] * np.sin(t))
        x_surf.append(np.array(x_fuse))
        y_surf.append(np.array(y_fuse))
        z_surf.append(np.array(z_fuse))

    return np.array(x_surf), np.array(y_surf), np.array(z_surf)

def plot_nacelle(nacelle):
    length = nacelle.length
    diameter = nacelle.diameter
    n=50
    x_arr = np.linspace(nacelle.xle, nacelle.xle+length, n)
    x = []
    y = []
    z = []
    y0 = nacelle.yle
    z0 = nacelle.zle

    for xi in x_arr:
        theta = np.linspace(0, np.pi*2, 30)
        x_cross = []
        y_cross = []
        z_cross = []
        for t in theta:
            x_cross.append(xi)
            y_cross.append(y0 + np.cos(t) * diameter/2)
            z_cross.append(z0 + np.sin(t) * diameter/2)
        x.append(x_cross)
        y.append(y_cross)
        z.append(z_cross)

    return np.array(x), np.array(y), np.array(z)

def plot_component(component):
    if (component.component_type == 'Wing' or
            component.component_type == 'Horizontal' or
            component.component_type == 'Vertical'):
        x, y, z = plot_wing(component)
    elif component.component_type == 'Fuselage':
        x, y, z = plot_fuselage(component)
        if any(v is None for v in (x, y, z)):
            return
    elif component.component_type == 'Engine':

        xle = component.xle
        yle = component.yle
        zle = component.zle
        if not isinstance(xle, list):
            xle = [component.xle]
            yle = [component.yle]
            zle = [component.zle]
        mesh = pv.PolyData()

        # stl_path = resources.files("WUADS.assets").joinpath("nacelle.stl")

        try:
            # Works when installed as a package
            stl_path = resources.files("WUADS.assets").joinpath("nacelle.stl")
        except (ModuleNotFoundError, AttributeError):
            # Fallback for running from cloned repo
            stl_path = Path(__file__).parent.parent / "assets" / "nacelle.stl"

        for x, y, z in zip(xle, yle, zle):
            # Read STL from package resource path
            temp = pv.read(str(stl_path)).rotate_y(-90, inplace=True)
            bounds = temp.bounds
            xscale = (bounds[1] - bounds[0]) / component.length
            yscale = (bounds[5] - bounds[4]) / component.diameter
            temp = temp.scale([1 / xscale, 1 / yscale, 1 / yscale])
            xyz = [x, y, z]
            temp = temp.translate(xyz)
            mesh = mesh + temp + temp.reflect([0, 1, 0])

        return mesh
    elif component.component_type.lower() == 'wing_advanced':
        # section 1
        x, y, z = plot_wing(component.sections[0])
        grid = pv.StructuredGrid(x, y, z)
        mesh = grid.extract_surface().triangulate()
        if len(component.sections) > 1:
            for sec in component.sections[1:]:
                x, y, z = plot_wing(sec)
                grid = pv.StructuredGrid(x, y, z)
                mesh1 = grid.extract_surface().triangulate()
                mesh = mesh + mesh1
        mesh = mesh + mesh.reflect((0, 1, 0))
        return mesh
    else:
        return

    grid = pv.StructuredGrid(x, y, z)
    mesh = grid.extract_surface().triangulate()
    mesh = mesh + mesh.reflect((0, 1, 0))

    # plotter.add_mesh(mesh, show_edges=False, color='grey', metallic=.25, pbr=True)
    return mesh
