WUADS
=====

Washington University Aerospace Design Suite (WUADS) is a Python-based conceptual aircraft design package built with 
two core goals: simplicity and extensibility. WUADS combines empirical methods with mixed-fidelity numerical models, 
enabling users to rapidly analyze aircraft performance across a wide range of configurations — from conventional 
transports to complex systems with alternative propulsion and unconventional geometries.

![WUADS gui](docs/images/WUADS_gui.png)
---
##  Features
- **User Friendly Designer GUI**

  WUADS aircraft designer GUI is designed to simplify the process of creating and editting WUADS input files 


- **Empirical Weight Estimation**  
  Component-level empirical methods are used to accurately estimate the aircraft's weight based on configuration and inputs.


- **Vortex Lattice Method (VLM) Integration**  
  WUADS automates the setup and analysis of aerodynamic performance using the Athena Vortex Lattice (AVL) code.


- **Aerodynamic Performance Analysis**  
  Combines VLM results with empirical drag models to evaluate overall aircraft aerodynamic efficiency and static stability.


- **Mission-Based Range Estimation**  
  Supports custom mission profiles to estimate fuel burn, reserve fuel, and maximum range capabilities.


- **Optimization-Ready Framework**  
  Rapid performance predictions and a modular structure make WUADS ideal for conceptual optimization tasks.


- **Customizability and Extensibility**
  WUADS is designed to allow the user to easily override the built in methods allowing for custom components, analysis 
  methods, etc.
---
Download and Installation
---
WUADS can be downloaded like any other python package

```
pip install WUADS
```

The only complication is that in order to run a full aerodynamic analysis, Athena Vortex Lattice will need to be installed
in the current working directory. Note that this just needs to be the "avl.exe". Alternatively, you can set up an 
environment variable which links 'avl' to the path of your avl.exe file. You can find the avl download on the site below.
- https://web.mit.edu/drela/Public/web/avl/

---
Basic Usage
---
The basic syntax for using WUADS if fairly straightforward assuming you have already defined your input file.

```python
from WUADS import Aircraft, weights_report, mission_profile_report

input_file = './inputs/aircraft.yml'    # Define the path to your input file
ac = Aircraft(input_file)               # Create the aircraft

weights_report(ac)                      # Generate a weights report
ac.mission.run_case()
mission_profile_report(ac)

```
The above code will load the aircraft input file, generate the geometry, calculate the weight, calculate the parasite
drag, and populate the mission profile, and calculate the overall range of the aircraft. It will output 2 seperate reports
one detailing the aircraft's weight properties and one detailing the aircraft's mission profile and range.

You have two seperate ways to create the input file. One is to edit the aircraft's .yml input file directly. This file 
is designed to be as readable to the user as possible and is not overly complex to use, however to simplify the process 
of creating these files, the designer GUI can be used. To launch the GUI, enter the following into the terminal or command line

```
WUADS 
```

Alternatively you can launch the gui with your input file instead of the default input

```
WUADS ./inputs/input_file.yml
```
---
Tutorials
---

Whether you're new to aircraft design or experienced in computational modeling, **WUADS** offers a simple interface with the flexibility for custom applications.

A growing collection of tutorials is available in the [`tutorials/`](./tutorials) directory, including:

---
Citations
---
If you use WUADS in your research, please cite the following dissertation:

- Kiely, M. "The Conceptual Design, Analysis and Optimization of a Hydrogen Combustion and a Hydrogen Fuel-Cell Powered Aircraft",
PhD. Thsis, Washington University in St. Louis, available: available: http://openscholarship.wustl.edu/eng_etds/1031/

```bibtex
@phdthesis{kiely2025,
  author       = {Mike Kiely},
  title        = {The Conceptual Design, Analysis and Optimization of a Hydrogen Combustion and a Hydrogen Fuel-Cell Powered Aircraft},
  school       = {Washington University in St. Louis},
  year         = {2024},
  address      = {St. Louis, MO},
  note         = {available: http://openscholarship.wustl.edu/eng_etds/1031/}
}
```

Additionally, this thesis provides a full comprehensive explanation of all the models used in WUADS as well

---
Developers and Contributors
---
WUADS was developed and validated by

- Mike Kiely - k.mike@wustl.edu
- Natasha Igic
- Duyen Nguyen

## Want to contribute?

Please do! We are always looking to expand the code in whatever way we can and welcome contributions from the community
To get involved just raise issues, create pull requests, or email me at k.mike@wustl.edu

---
Liscence
---
## License

WUADS is licensed under the [Mozilla Public License 2.0 (MPL 2.0)](LICENSE).

This license allows you to freely use, modify, and distribute the software, provided that any modifications to the 
original source files are also shared under the same license. For more details, see the [full license text](LICENSE).

