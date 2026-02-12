
---
Custom Components
---
---
WUADS allows you to make and implement your own custom components and override existing analysis methods.
To do this, you need to create a class in a new module. The following python script gives the basic syntax for 
creating a new component, including all the required methods for a complete analysis.

Note that this example gives all the possible customization options. For a simplified class, you can simply override an
existing component in WUADS and inherit all its methods and variables. For instance, if you inherit the "Wing" class,
the methods to create the geometry, set the weights, and set the parasite drag arre inheritted as well. For some examples 
of this, see the attached files.

```python
from WUADS.components.component import PhysicalComponent

class custom_component(PhysicalComponent):
    # Note: this class inherets the PhysicalComponent class, this will be discussed later

    def __init__(self, params):
        
        """
        The __init__ function defined how the component is defined and the geometry is created.
        Use this function to initiate and set your class parameters.
        
        The params input represents a set of keyword arguments that will be passed into this function. 
        This is simply the block of text in the yaml input file that defines your component
        """
        
        # Initiate any custom variables here. For instance, assume this component is defined by a length and diameter
        self.length = 0
        self.diameter = 0
        
        # Call the super().__init__ function. 
        # This will set your class variables to what they are declared as in your input params
        super().__init__(params)
        
        # At this point your parameters are set, use the rest of this function to set whatever else you
        # need to set (for example: aspect ratio, fineness ratio, etc.)
        self.fineness_ratio = self.length / self.diameter
        
    # The rest of the required functions are your analysis methods
    # The functions displayed here are the defaults that your class will use if you choose not to override them
    
    # Note: Make sure you use the same arguments as these examples. Also make sure you are returning the same variables
    
    
    def parasite_drag(self, flight_conditions, sref, aircraft):
        """
        Use this function to set your component's parasite drag. Make sure to use these same arguments.
        
        Arguments:
            - flight_conditions: A WUADS class that contains the given flight conditions. Variables such as velocity, rho (density), mach, etc.
            - aircraft: The aircraft instance that the component belongs to
            - sref: aircraft reference area
        """
        
        self.cd0 = 0
        return self.cd0
    
    def set_wave_drag(self, aircraft, flight_conditions=None):
        """
        Use this function to set your component's wave drag. If you are unsure, its probably a safe bet to leave this as zero.
        """
        self.cdw = 0
        return self.cdw
    
    def set_weight(self, aircraft, wdg):
        """
        This function contains the method to set your component's weight (in lbs).
        
        Arguments:
            - wdg: Design gross weight of the aircraft the component belongs to
        """
        self.weight = 0
        return self.weight
    
    def set_cg(self):
        """
        Set the component's center of gravity [x, y, z]
        """
        
        self.cg = [self.xle + self.length/2, 0, 0]
        super().set_cg()    # Note: this is important for setting the whole plane's cg
        
    def update(self, variable, value, **kwargs):
        """
        Use this function to control how the component is updated when the ac.update_component() function is called.
        
        By default what this function does is changes the input parameters and re initializes the component.
        Change this to accomplish things like maintaining an aspect ratio, etc.
        """
        
        self.params[variable] = value
        self.__init__(self.params)

```

To use this class as your custom parameter, declare the component as follows in the components list of your input yaml file.

```yaml
components:
  custom_component:     # Note: This line must match the name of your class for your custom component
    module_name: "custom_component.py"    # this is the name of the file your class is in
    title: "Custom Component 1"
    length: 10          # Change these input parameters to whatever you need to. This is what will be passed as "params" in your __init__ file
    diameter: 5
    
```

