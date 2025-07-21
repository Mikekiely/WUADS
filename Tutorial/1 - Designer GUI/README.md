---
Designer GUI Tutorial
---

The following tutorial will cover in detail how to use the aircraft designer
gui for WUADS. Please note that the GUI is functional however is very much still a 
work in progress. We have several exciting updates planned for the GUI in the future
but the current iteration should work for defining some baseline configurations.

---
Loading the GUI
---
To load the gui simply type the following into the terminal/command line from your current working
directory

```
WUADS-gui
```

![WUADS GUI](/docs/images/WUADS_gui.png)

If everything is installed correctly, your gui should now be open. Note that the first time you run this
it may take a few minutes. Note that if no other input file is specified, the WUADS designer gui opens
a Boeing 737-800. You can change this by instead using the following command when launching the gui

```bash
WUADS-gui path-to-your-input-file
```

Alternatively, you can launch WUADS and simply load your configuration file from the file menu
in the top right. The WUADS input file is a fairly complex .yml configuration file will be 
covered in detail in section 3. To create these files, it can be helpful to start from an existing
input file. There are several sample inputs included in [docs/sample_inputs](docs/sample_inputs).

When you are done editting your aircraft you can write you input file by using the save button in the file menu

---
The Aircraft Info Menu
---

![Aircraft Info Menu](/docs/images/aircraft_info.png)

On the lefthand side of the screen there are a set of toolbars with which you can edit your aircraft.
The first toolbar, 'Aircraft Information', is fairly straightforward. Note that if you hover your mouse
over the variable names, a tooltip will appear with units. The variables are as follows:

- Title: This will determine the name of the prefix on output files, so use valid characters
- Design Range: How far is your plane designed to travel in nmi. Note, this doesn't effect the mission profile,
only certain weight methods
- Cruise Altitude and Mach Number
- Ultimate Load: The maximum g force your aircraft is expected to experience. 4.5 is a good guess for alot of aircraft
- Fuel Density
- Aircraft Type: general aviation or Transport.
- Lock Component Weights: The weight of each component is dependent on the weight of the full aircraft, meaning 
that an iterative method is needed to calculate the total weight. Making the fuselage larger for instance will require a
heavier wing since more structural support is required. When you check off this box, the component weights will be held 
constant where they currently are. This is also important when running off design conditions, like a mission with less than 
maximum fuel or cargo weight.

---
Component List
---
This is where you edit you major structural components like the wing and the fuselage. You can double click to edit
and existing component or you can right click to add or remove a component. Note that as the code stands right now,
you are required to have components named 'Fuselage', 'Main Wing', and 'Engine'. There are plans to update this in the 
future, but as of now do not delete these components.

---
Useful Load
---
Here, you can edit all the non structural weights that your plane is holding, like the passengers, pilots, cargo, fuel,
and crew. When you double-click on one, additionally you can edit the x coordinate of the center of gravity.
The reset button on the bottom resets the center of gravity to reasonable positions (note: this is based on the 737. 
don't use this feature on configurations significantly different that this.)

---



