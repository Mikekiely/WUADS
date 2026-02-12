
---
Propulsion Analysis
---

Propulsion in WUADS is estimated using 1 of 2 methods. Note that the following section is dedicated specifically to
turbofan engines, I will update this with turboprop and prop engines when those are ready. 

---
The first method for calculating turbofan engine performance is to use the WUADS generalized turbofan model. This is a 
general model used to calculate the maximum thrust and specific fuel consumption of an engine at a given Mach number and 
Altitude. It is included in the Default_Turbofan_data.xlsx file. 

This default turbofan model can be scaled to more closely match the engine you are trying to model. Real world engine
performance data is difficult to find, so there is the option to scale the engine data on its performance at sea level, 
at cruise, or at both. For instance, the engine data for the 737-800's CFM56-7B engine is only published at sea level,
so the following can be used to scale the data.

```yaml
Propulsion:
  thrust_sea_level: 24200
  sfc_sea_level: 0.356
  thrust_cruise: None
  sfc_cruise: None
```
Simply omitting the unknown values works as well. If performance metrics for both cruise and sea level are known, both
can be input. In this case, a weighted bilinear interpolation is used to scale the default performance curves between
these values. 

---
Alternatively, for a higher fidelity analysis the default engine profiles can be overridden with the desired engine
performance metrics. The formatting for these input propulsion files must be the same as the included default turbofan data
file, 2 header rows with the mach numbers on the third row and the altitudes on the first column. These reference mach
Mach numbers and Altitudes can be changed at will, they do not need to be the same or even the same length as the included file.
The gui also has a tab to make and load propulsion datafiles

To load a propulsion data file, simply include the following line, replacing the file name with you data file.

```yaml
Propulsion:
  engine_data_file: engine_data.xlsx
```

Note that if you still include scaling factors with the engine data file, the code will still scale your input data.

