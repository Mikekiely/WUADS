
---
Mission Profile and Weights Analysis
---
---
With your input file created and propulsion analysis done, running a basic analysis in WUADS from a python interface is
fairly straight forward. Simply import WUADS, create an aircraft using your desired inputs file, and run your analyses.

```python
from WUADS import *

input_file = './inputs/737-800.yml'
ac = Aircraft(input_file)

weights_report(ac, filename=None)
ac.mission.run_case()
mission_profile_report(ac, filename=None)
```

ac.mission.run_case in this case analyzes the aircraft's total mission profile, as declared in the input file. The mission
profile report and weights reports write the default reports featuring to a file. Note that the filename arguments are optional,
by default these files will be stored in your ouputs folder. Along with these reports will be the automatically generated 
AVL files.
