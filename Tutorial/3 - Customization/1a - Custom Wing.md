
---
Custom Wing
---
---

As mentioned in the previous tutorial, a pre existing WUADS component class can be used to simplify making your custom
class. As an example, lets make a subclass of wing. It will take the same inputs as the wing and be defined the same,
except 2 differences. 

1. A new model for calculating the wing weight will be used. In this model, we will just calculate the wing weight 
by assuming a set weight per square foot of wing. This will require an additional class variable to be defined.
2. the parasite drag will be set to half of what WUADS normally predicts.

Outside of these changed models, nothing else needs to be altered. The custom wing class looks like this.

```python
from WUADS.components.aerobodies.wing import Wing

class custom_wing(Wing):

    def __init__(self, params):
        self.weight_per_sq_ft = 0   # You need to initiate this variable before calling super
        super().__init__(params)    # This will create your entire geometry, no need to override anything
        
    def set_weight(self, aircraft, wdg):
        # Note: the arguments still need to be the same, even if you aren't using them
        self.weight = self.area * self.weight_per_sq_ft
        return self.weight
    
    def parasite_drag(self, flight_conditions, sref, aircraft):
        super().parasite_drag(flight_conditions, sref, aircraft) # Set the parasite drag using the default functions
        self.cd0 *= .5
        return self.cd0

```