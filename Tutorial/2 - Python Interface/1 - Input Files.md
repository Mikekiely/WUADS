
---
Input Files
---

The following section will cover the WUADS input file and how to read and create them. These files contain the same
information as the gui and are the main data format used to load airplane configurations into WUADS. A sample input file
is included in this folder and is called "737-800.yml". Note that this is the same as the default configuration loaded
into WUADS when launching the gui.

The WUADS input files are structured as a yaml file (.yml or .yaml). This data structure allows for a very readable
input for the WUADS code. Note that the gui simply acts as a slightly more legible, interactable interface for these 
yaml files. In fact the fields in the input yaml file are used to populate the tabs of the gui.

---
Structure
---
The yaml files are structured using a series of headers which contain sets of aircraft information (corresponding to the 
gui headers). For instance, the first header contains upper level aircraft information, and is shown below. Note that the
included file contains all possible inputs, its probably a good idea to just work off of this.

```yaml
aircraft:
  title: 'b737-800'         # Used for output file prefix
  altitude: 35000           # Altitude at cruise
  mach: 0.78                 # Mach number at cruise
  max_mach: .78           # Maximum mach number at cruise
  ultimate_load: 4.5        # Ultimate Load Factor (g's)
  w_fuel: 46000             # Fuel Weight
  cg_fuel: [68, 0, 0]       # Fuel center of gravity (Optional)
  rho_fuel: 6.8             # Fuel density (lbs/gal) (Optional)
  n_passengers: 180         # number of passengers (Optional)
  cg_passengers: [60, 0, 0]  # Center of gravity for passengers (Optional)
  n_pilots: 2               # Number of pilots (Optional)
  n_flight_attendants: 4    # Number of flight attendants (Optional)
  cg_crew: [9, 0, 0]        # Center of gravity for the crew (Optional)
  w_cargo: 15757            # Cargo Weight (Optional)
  cg_cargo: [60, 0, 0]      # Center of gravity for cargo (Optional)
  design_range: 2935        # Design range (nmi)
  n_engines: 2              # number of engines
```
Similary, the component list is structured as a list of lists. The "Components" header is declared, then
each component with its corresponding input parameters is declared. Each individual component has its required set of
input parameters and also has a set of optional input variables for higher fidelity analysis. In fact, any variable that
the component stores in its analysis can be overridden by declaring it here. For instance, the laminar percentage over the 
wing is automatically calculated, but that calculation can be overridden by simply declaring laminar_percent: 0.1. 

The set of input parameters you use for your components is important, as will be seen later. The variables included as 
input parameters can be easily updated using the update_component() function, allowing for the entire geometry to be 
quickly editted

```yaml
components:
  wing:
    # Required Inputs
    title: 'Main Wing'
    area: 1340                  # Surface Area
    span: 111                   # Wing Span
    taper: 0.1581               # Wing Taper Ratio
    sweep: 25.01                # Quarter Chord Sweep (deg)
    sweep_location: .25
    dihedral: 6                 # Dihedral Angle at root
    xle: 42.4                   # X value at leading edge
    yle: 0                      # Y value at leading edge
    zle: -2.42                  # Z value at leading edge

    # Optional Inputs
    laminar_percent: .1         # Percentage of chord experiencing laminar flow
    control_surface_ratio: .1   # Percentage of the chord which has a control surface (used for weights
    airfoil_thickness: [.12, .07]

  horizontal:
    title: 'Horizontal Stabilizer'
    span: 47.1
    cr: 12.8
    ct: 2.55
    sweep: 34.407
    sweep_location: 0
    dihedral: 7
    xle: 111
    yle: 0
    zle: 4.415
    control_surface_ratio: .2
```

