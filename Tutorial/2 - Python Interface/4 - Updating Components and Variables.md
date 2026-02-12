
---
Updating components and variables
---
---
The following section covers how to use WUADS functions to update and change components. 

Upper level aircraft variables such as w_fuel, w_cargo, mach_cruise, and altitude_cruise can be updated simply by changing 
the variables directly. For instance, the following code changes all those variables directly.

```python
from WUADS import *

input_file = './inputs/737-800.yml'
ac = Aircraft(input_file)
ac.w_fuel = 40000       # Changes fuel weight to 40000 lbs
ac.w_cargo = 15000      # Changes cargo weight to 15000 lbs
ac.mach_cruise = .8     # Changes cruise mach number to 0.8
ac.altitude_cruise = 30000 # Changes cruise altitude to 30000 ft
```

updating component's input parameters takes a function in the aircraft class. This is important as you need to ensure the 
weight and parasite drag of the aircraft are calculated accurately. The aircraft.update_component function takes a list
of tuples as an argument, each tuple containing the name of the component to be changed, the name of the variable you want
to change, and the value you want to change the variable to. 

```python
ac.update_component([
    ('Main Wing', 'area', 1500),
    ('Main Wing', 'sweep', 25),
    ('Fuselage', 'length', 100)
])

# Note: the format for the argument is as follows. It must be a list 
# [(Component Title, variable name, value)]
```

---
It is important to consider what changing some of the geometric and weight parameters does to the overall weight calculation.
WUADS' weight calculation uses a series of iterative processes to balance individual component weights vs total aircraft 
weights. For example, the wing must be sized to support the overall weight of the aircraft, which in term depends on how 
much the wing weighs. What this means in practice is that changing some parameters can unexpectedly change the weights of 
other components. 

To avoid this sort of error, the lock_component_weights variable can used. This variable overrides the component weight 
calculation function, ensuring they stay the same no matter what variables are changed. For instance, the following code
can be used to run an analysis at lower fuel and cargo weights, without changing the weight of the wing.

```python
ac.lock_component_weights = True
ac.w_fuel = 20000
ac.w_cargo = 10000
```
Alternatively, the aircraft reference weight can be set. When a reference weight is set, the set_weight function will
bypass the iterative loop and size the components as if the aircraft weight is equal to the reference weight.

```python
ac.reference_weight = 150000    # Set reference weight to 150000 lbs
```
